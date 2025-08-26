class badSexpError(ValueError):
    pass

class make_symbol():
    def __init__(self, name:str):
        self.name = name
    def __hash__(self):
        return hash(f"(make-symbol {self.name})")
    def __eq__(self, value):
        return value == self.name
    def __str__(self):
        return f"{self.name}"
    def __repr__(self):
        return f"(make-symbol {self.name})"

class make_string(str):
    def __new__(self, name:str):
        return super().__new__(self, name)
    def __add__(self, value):
        return make_string(super().__add__(value))
    def __str__(self):
        return super().__str__()
    def __repr__(self):
        return super().__repr__()[1:-1].join(["\"","\""])

def make_list(iterable):
    return sexp(iterable)

def parse_word(word: str):
    try:
        word = float(word)
        if (word == int(word)):
            word = int(word)
    except ValueError:
        pass
    return word if ((type(word) is not str) or (type(word) is make_string)) else make_symbol(word)

def find_string(s: list[str], end = "\""):
    escape: bool = False
    success: bool = False
    chars = []
    offset = 0
    while(offset < len(s)):
        c = s[offset]
        if escape:
            escape = False
            match(c):
                case "b":
                    chars.append("\b")
                case "f":
                    chars.append("\f")
                case "n":
                    chars.append("\n")
                case "r":
                    chars.append("\r")
                case "t":
                    chars.append("\t")
                case "v":
                    chars.append("\v")
                case "\'" | "\"" | "\\":
                    chars.append(c)
                case "x":
                    candidate = "".join(s[offset + 1: offset + 3])
                    chars.append(chr(int(candidate, 16)))
                    offset += 2
                case x if x in "01234567":
                    candidate = "".join(s[offset: offset + 3])
                    chars.append(chr(int(candidate, 8)))
                    offset += 2
                case _:
                    raise ValueError(f"Invalid escape character: \"{c}\"")
        else:
            if c == "\\":
                escape = True
            elif c == end:
                success = True
                break
            else:
                chars.append(c)
        offset += 1
    if(not success):
        return -1, ""
    return offset, make_string("".join(chars))

assert(find_string("") == (-1, ""))
assert(find_string("a") == (-1, ""))
assert(find_string(r'\""') == (2, "\""))
assert(find_string(r'\'"') == (2, "\'"))
assert(find_string(r'\b"') == (2, "\b"))
assert(find_string(r'\\"') == (2, "\\"))
assert(find_string(r"""\x4e" """) == (4, "\x4e"))
assert(find_string(r"""\000" """) == (4, "\000"))
try:
    find_string(r"\ ")
    assert(False)
except ValueError:
    pass

class sexp():
    # insteance variable __sexp is a int|float|tuple

    def __init__(self,s):
        if(type(s) is sexp):
            self.__sexp:tuple|int|float|make_symbol|make_string = tuple(s.__sexp)
        try:
            if(iter(s) and type(s) is not str):
                self.__sexp = tuple(s)
                self.num_unclosed = 0
            else:
                raise Exception("needs sexp parsing") 
        except:
            self.__sexp,self.num_unclosed = sexp.__make_sexp(str(s))
            if(len(self.__sexp) != 0): self.__sexp = self.__sexp[0]

    
    def content(self):
        return self.__sexp

    def __eq__(self, value):
        return self.content() == value
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        if(type(self.content()) is not tuple):
            return "'" + repr(self.content())
        content_repr = "(" + " ".join([repr(item) for item in self.content()]) + ")"
        if(type(self.content())) is tuple:
            return "'" + content_repr
        else: 
            return content_repr
    def __hash__(self):
        return self.content().__hash__()
    
    def __getitem__(self, item):
        return self.content().__getitem__(item)
    
    def __len__(self):
        return self.content().__len__()
    
    def __make_sexp(s: str):
        s = s.replace("\t", " ").replace("\r"," ").replace("\n"," ").strip()
        # print(s)

        # tokenize
        if (not s.startswith("(")):
        # or not s.endswith(")"):
            if(s.startswith("\"")): 
                result = find_string(s[1:])
                if(result != -1): 
                    return ((find_string(s[1:])[1],), 0)
            elif(s.startswith("'")):
                result, num_unclosed = sexp.__make_sexp(s[1:])
                # print(s[1:])
                return (tuple() if len(result) == 0 else sexp(result[0])), num_unclosed
            # parse word into number if appropriate
            else:
                return ((parse_word(s),),0)            

        def tokenize(loc: list[str]):
            token_stack = []  # added and removed from the back
            curr_tokens = []
            curr_word = []
            off = 0
            while off < len(loc):
                c = loc[off]
                match(c):
                    case "(":
                        token_stack.append(curr_tokens)
                        curr_tokens = []
                    case ")":
                        if (len(curr_word) != 0):
                            curr_tokens.append(parse_word("".join(curr_word)))
                            curr_word = []
                        # if (len(token_stack) == 0):
                        #     break
                        next_scope = token_stack.pop()
                        next_scope.append(tuple(curr_tokens))
                        curr_tokens = next_scope
                        if(len(token_stack) == 0):
                            off +=1
                            break
                    case " ":
                        if (len(curr_word) != 0):
                            curr_tokens.append(parse_word("".join(curr_word)))
                            curr_word = []
                    case "\"":
                        offset,string = find_string(loc[off+1:])
                        if(offset != -1):
                            if (len(curr_word) != 0):
                                curr_tokens.append(parse_word("".join(curr_word)))
                                curr_word = []
                            off += offset + 1 # skip closing quotation as well
                            curr_tokens.append(string)
                        else: 
                            curr_word.append(c)
                    case "'":
                        if (len(curr_word) != 0):
                            curr_tokens.append(parse_word("".join(curr_word)))
                            curr_word = []
                        if (loc[off+1] != "("):
                            off += 1
                            continue
                        # print(loc[off + 1:])
                        offset, sub_sexp_tokens, num_unclosed = tokenize(loc[off + 1:])
                        # offset += 1
                        # print(sub_sexp_tokens)
                        sub_sexp = sexp(sub_sexp_tokens[0])
                        # print(sub_sexp)
                        curr_tokens.append(sub_sexp)
                        off += offset
                    case _:
                        curr_word.append(c)
                # print(f"{off}[{s[off]}]:", f"stack:{token_stack}, tokens:{curr_tokens}, word: {curr_word}" ,sep = "\n")
                off += 1
            # print(off, tuple(curr_tokens))
            if(len(curr_word) != 0):
                curr_tokens.append(parse_word("".join(curr_word)))
            # print(curr_tokens)
            return off, tuple(curr_tokens), len(token_stack)
        _, result, num_unclosed = tokenize([char for char in s])
        return result, num_unclosed

# print(sexp("1"))
assert (sexp("1") == 1)
# print(sexp("(with (a 12) '(divide a 4))"))
# print(sexp("(with (a 12) '(divide a 4))") == (make_symbol("with"), (make_symbol("a"), 12), sexp("(divide a 4)")))
# print((make_symbol("with"), (make_symbol("a"), 12), sexp("(divide a 4)")))
assert (sexp("(with (a 12) '(divide a 4))") ==
        ("with", ("a", 12), sexp("(divide a 4)")))
assert (sexp("(with (a 12) (divide a 4))") ==
        ("with", ("a", 12), ("divide", "a", 4)))
assert (sexp("(with (b 4) (with (a 12) (divide a b)))") ==
        ("with", ("b", 4),
        ("with", ("a", 12),
        ("divide", "a", "b"))))
assert (sexp("'()") == sexp(sexp(tuple())))
assert (sexp("(= '() (list))") == ("=", sexp(sexp(tuple())), ("list",)))
assert (sexp("(with (b 4)\r\n\t(with (a 12) (divide a b)))") ==
        ("with", ("b", 4),
        ("with", ("a", 12),
        ("divide", "a", "b"))))

# print(sexp("(with (b 4)\r\n\t(with (a \"12\") (divide a b)))"))
assert (sexp("(with (b 4)\r\n\t(with (a 12) (divide a b)))") ==
        ("with", ("b", 4),
        ("with", ("a", 12),
        ("divide", "a", "b"))))
assert (sexp("(import FBX ./test.fbx)")) == ("import","FBX", "./test.fbx")