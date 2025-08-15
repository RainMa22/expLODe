class badSexpError(ValueError):
    pass


def sexp(s: str):
    s = s.replace("\t", " ").replace("\r"," ").replace("\n"," ").strip()
    # print(s)
    def parse_word(word: str):
        try:
            word = float(word)
            if (word == int(word)):
                word = int(word)
        except ValueError:
            pass
        return word
    # tokenize
    if (not s.startswith("(")) or not s.endswith(")"):
        return parse_word(s)
    # parse word into number if appropriate



    def tokenize(s: list[str]):
        token_stack = []  # added and removed from the back
        curr_tokens = []
        curr_word = []
        for i, c in enumerate(s):
            if (c == "("):
                token_stack.append(curr_tokens)
                curr_tokens = []
            elif (c == ")"):
                if (len(curr_word) != 0):
                    curr_tokens.append(parse_word("".join(curr_word)))
                    curr_word = []
                next_scope = token_stack.pop()
                next_scope.append(tuple(curr_tokens))
                curr_tokens = next_scope
            elif (c == " "):
                if (len(curr_word) != 0):
                    curr_tokens.append(parse_word("".join(curr_word)))
                    curr_word = []
            else:
                curr_word.append(c)
            # print(f"{i}[{c}]:",token_stack, curr_tokens, curr_word,sep = "\n")
        return tuple(curr_tokens)  
    result = tokenize([char for char in s])
    # print(result)
    return result if len(result) > 1 else result[0]

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
assert (sexp("(import FBX ./test.fbx)")) == ("import","FBX", "./test.fbx")