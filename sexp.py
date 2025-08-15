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
        return str(self)

class make_string(str):
    def __new__(self, name:str):
        return super().__new__(self, name)
    def __add__(self, value):
        return make_string(super().__add__(value))
    def __str__(self):
        return super().__str__()
    def __repr__(self):
        return super().__repr__()[1:-1].join(["\"","\""])
    


def parse_word(word: str):
    try:
        word = float(word)
        if (word == int(word)):
            word = int(word)
    except ValueError:
        pass
    return word if type(word) is not str else make_symbol(word)

def find_string(s: list[str], end = "\""):
    escape: bool = False
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
                break
            else:
                chars.append(c)
        offset += 1
    return offset, make_string("".join(chars))

# print(find_string(""))
assert(find_string("") == (0, ""))
assert(find_string("a") == (1, "a"))
assert(find_string(r"\"") == (2, "\""))
assert(find_string(r"\'") == (2, "\'"))
assert(find_string(r"\b") == (2, "\b"))
assert(find_string(r"\\") == (2, "\\"))
assert(find_string(r"\x4e") == (4, "\x4e"))
assert(find_string(r"\000") == (4, "\000"))
try:
    find_string(r"\ ")
    assert(False)
except ValueError:
    pass

class sexp(tuple):
    def __new__(self,s):
        return super().__new__(self,sexp.__gen_sexp(str(s)))
    
    def content(self):
        return self[0]

    def __eq__(self, value):
        return self[0].__eq__(value)
    
    def __str__(self):
        return f"'{self[0].__repr__()}" if type(self[0] is not (int | float)) else self[0].__repr__()
    
    def __repr__(self):
        return f"'{self[0].__repr__()}" if type(self[0] is not (int | float)) else self[0].__repr__()

    def __gen_sexp(s: str):
        s = s.replace("\t", " ").replace("\r"," ").replace("\n"," ").strip()
        # print(s)

        # tokenize
        if (not s.startswith("(")) or not s.endswith(")"):
            # parse word into number if appropriate
            return (parse_word(s),)            

        def tokenize(s: list[str]):
            token_stack = []  # added and removed from the back
            curr_tokens = []
            curr_word = []
            i = 0
            while i < len(s):
                c = s[i]
                match(c):
                    case "(":
                        token_stack.append(curr_tokens)
                        curr_tokens = []
                    case ")":
                        if (len(curr_word) != 0):
                            curr_tokens.append(parse_word("".join(curr_word)))
                            curr_word = []
                        next_scope = token_stack.pop()
                        next_scope.append(tuple(curr_tokens))
                        curr_tokens = next_scope
                    case " ":
                        if (len(curr_word) != 0):
                            curr_tokens.append(parse_word("".join(curr_word)))
                            curr_word = []
                    case "\"":
                        if (len(curr_word) != 0):
                            curr_tokens.append(parse_word("".join(curr_word)))
                            curr_word = []
                        offset,string = find_string(s[i+1:])
                        i += offset + 1 # skip closing quotation as well
                        curr_tokens.append(string)
                    case _:
                        curr_word.append(c)
                # print(f"{i}[{c}]:",token_stack, curr_tokens, curr_word,sep = "\n")
                i += 1
            return tuple(curr_tokens)  
        result = tokenize([char for char in s])
        # print(result)
        return result
        # return result if len(result) > 1 else result[0]

# print(sexp("1"))
assert (sexp("1") == 1)

assert (sexp("(with (a 12) (divide a 4))") ==
        ("with", ("a", 12), ("divide", "a", 4)))
assert (sexp("(with (b 4) (with (a 12) (divide a b)))") ==
        ("with", ("b", 4),
        ("with", ("a", 12),
        ("divide", "a", "b"))))
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