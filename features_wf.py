import math
import os
import sys
# allow for import of features
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from features import *
from sexp import sexp,make_symbol,make_string,make_list


def interp_workflow(env: dict, wf, interp_override=None):
    # print(env,wf, sep = "\n")
    if(interp_override is None):
        interp_override = interp_workflow
    def interp(wf):
        return interp_override(env, wf, interp_override)
    match(wf):
        case x if x == "f" and type(x) is make_symbol:
            return False
        case "False":
            return False
        case ("eval", something):
            if(type(something) is make_symbol):
                return interp(sexp(something.name).content())
            elif(type(something) is sexp):
                return interp(something.content())
            else:
                return interp(something)
        case ("funV", *_):
            return wf
        # (with (x, y) (...))
        case ("lambda" | "λ", fargs, body):
            newEnv = {}
            newEnv.update(env)
            return ("funV", fargs, newEnv, body)
        case ("with", (x, y), rest):
            newEnv = {}
            newEnv.update(env)
            newEnv[interp(x)] = interp_override(env, interp(y), interp_override)
            return interp_override(newEnv, rest, interp_override)
        case ("with", (name, fargs, body), rest):
            newEnv = {}
            newEnv.update(env)
            name_u = interp(name)
            fun = ("funV", fargs, newEnv, body)
            newEnv[name_u] = fun
            # ("funV", fargs, env, body)
            return interp(("with", (name_u, fun), rest))
        case (("lambda", fargs, body), *args):
            return interp((interp(("lambda", fargs, body)), *args))
        case (("funV", fargs, fenv, body), *args):
            if(len(fargs) != len(args)):
                return ("Error", f"function needs {len(fargs)} argument(s) but gotten {len(args)} argument(s)!")
            else:
                newEnv = {}
                newEnv.update(fenv)
                for i, farg in enumerate(fargs):
                    newEnv[farg] = interp(args[i])
                return interp_override(newEnv, body, interp_override)
        # (add x y) | (+ x y)
        # case ("add" | "+", x, y):
        #     # print(interp(x), interp(y))
        #     return interp(x) + interp(y)
        case ("add" | "+", *vars):
            sum = interp(vars[0])
            for i in range(1,len(vars)):
                sum += interp(vars[i])
            return sum
        # (sub x y) | (- x y)
        case ("sub" | "-", x, y):
            return interp(x) - interp(y)
        # (multiply x y) | (* x y)
        case ("multiply" | "*", x, y):
            return interp(x) * interp(y)
        case ("divide" | "/", x, y):
            return interp(x) / interp(y)
        case ("deg->rad", degree):
            return interp(degree)/180*math.pi
        case ("equal?"|"=", a, b):
            return interp(a) == interp(b)
        case ("less?"|"<", a, b):
            return interp(a) < interp(b)
        case ("greater?"|">", a, b):
            return interp(a) > interp(b)
        case ("leq?"|"<=", a, b):
            return interp(a) <= interp(b)
        case ("geq?"|">=", a, b):
            return interp(a) >= interp(b)
        case ("or", a, b):
            return interp(a) or interp(b)
        case ("and", a, b):
            return interp(a) and interp(b)
        case ("if", cond, a, b):
            if(interp(cond)):
                return interp(a)
            else: 
                return interp(b)
        case ("not", x): 
            return not interp(x)
        case ("first", arr):
            return interp(("aref", 0, interp(arr)))
        case ("rest", arr):
            return interp(arr)[1:]
        case ("aref", index, arr):
            return interp(interp(arr)[interp(index)])
        case ("empty?", arr):
            return len(interp(arr)) == 0
        case ("make-string", sym):
            result = interp(sym)
            return make_string(result.name if result is make_symbol else str(result))
        case ("make-symbol", *rest):
            return make_symbol(" ".join(map(lambda item: item.name if type(item) is make_symbol else str(item), rest)))
        case (("cons",)| ("list",)):
            return sexp(tuple())
        case ("cons", item, arr):
            return sexp((interp(item), *interp(arr)))
        case ("list", *items):
            return make_list(map(lambda item: interp(item),items))
        case ("string-split", string, delimiter):
            return make_list(interp(string).split(interp(delimiter)))
        case ("filepath-basename", string):
            return os.path.basename(interp(string))
        case ("filepath-filenameNoExt", string):
            return make_string(os.path.splitext(os.path.basename(interp(string)))[0])
        # case ("new-scene"):
        #     return ("Scene", new_scene())
        # case ("new-scene", name):
        #     return ("Scene", new_scene(interp(name)))
        # case ("copy-scene", ("Scene", src_scene)):
        #     return ("Scene", copy_scene(interp(src_scene)))
        # case ("copy-scene", ("Scene", src_scene), scene_name):
        #     return ("Scene", copy_scene(interp(src_scene), interp(env, scene_name)))
        case ("import", "FBX", path):
            print(path)
            return tuple(importFBX(interp(path)))
        case ("export", "FBX", path):
            return (exportFBX(interp(path)))
        case ("export", "FBX", path, target):
            return tuple(exportFBX(interp(path), interp(target)))
        case ("uv-unwrap", "ALL"):
            return tuple(uv_unwrap())
        case ("uv-unwrap", objects):
            return tuple(uv_unwrap(interp(objects)))
        case ("unsubdiv", iterations):
            return tuple(unsubdiv(interp(iterations), inplace=False))
        case ("unsubdiv", iterations, target):
            return tuple(unsubdiv(interp(iterations), interp(target), inplace=False))
        case ("planar", angle_limit_rad):
            return tuple(planar_decimate(interp(angle_limit_rad), inplace=False))
        case ("planar", angle_limit_rad, target):
            return tuple(planar_decimate(interp(angle_limit_rad), interp(target), inplace=False))
        case ("collapse", ratio):
            return tuple(collapse(interp(ratio), interp(target), inplace=False)) 
        case ("collapse", ratio, target):
            return tuple(collapse(interp(ratio), interp(target), inplace=False))
        case (x, *rest):
            # TOOO: need to fix the logic below
            return interp((env.get(x), *rest)) if x in env.keys() else ((interp(x), *rest))
        case (x,):
            return interp(env.get(x)) if x in env.keys() else (x,)
        case x:
            return env.get(x) if x in env.keys() else x


def interp_workflow0(wf0):
    return interp_workflow({}, sexp(wf0).content())

# def testLOD1():
#     folder = os.path.abspath(os.path.dirname(__file__))
#     test_fbx_file = os.sep.join([folder, "test.fbx"])
#     out_fbx_file = os.sep.join([folder, "testLOD1.fbx"])
#     workflow = f"""
#     (with (inFile (make-string {test_fbx_file}))
#         (with (outFile (make-string {out_fbx_file}))
#             (export FBX outFile
#                 (planar (deg->rad 10)
#                     (import FBX inFile)))))""".replace("\n","")
#     interp_workflow0(workflow)
#     os.remove(out_fbx_file)
#     return True

# def testLOD2():
#     folder = os.path.abspath(os.path.dirname(__file__))
#     test_fbx_file = os.sep.join([folder, "test.fbx"])
#     out_fbx_file = os.sep.join([folder, "testLOD2.fbx"])
#     workflow = f"""
#     (with (inFile (make-string {test_fbx_file}))
#         (with (outFile (make-string {out_fbx_file}))
#             (export FBX outFile
#                 (unsubdiv 10
#                     (import FBX inFile)))))""".replace("\n","")
#     interp_workflow0(workflow)
#     os.remove(out_fbx_file)
#     return True

# assert(testLOD1())
# assert(testLOD2())


assert (interp_workflow0("(with (a 12) (divide a 4))") == 3)
assert (interp_workflow0("(with (a 12) (/ a 4))") == 3)
assert (interp_workflow0("(with (b 4) (with (a 12) (/ a b)))") == 3)
assert (interp_workflow0("(with (b 4) (with (a 12) (if (= a 12) (/ a b) -1)))") == 3)
assert (interp_workflow0("(with (b 4) (with (a 12) (if (not (= a 12)) (/ a b) -1)))") == -1)
assert (interp_workflow0("(with (b 4) (with (a 12) (if (= a 121) (/ a b) -1)))") == -1)
assert (interp_workflow0("(first '(b 4))") == 'b')
assert (interp_workflow0("(first (list b 4))") == 'b')
assert (interp_workflow0("(first (cons b (cons 4 '())))") == 'b')
# print (interp_workflow0("(rest (b 4))"))
assert (interp_workflow0("(rest '(b 4))") == (4,))
assert (interp_workflow0("(rest (cons b '(4)))") == (4,))
assert (interp_workflow0("(rest (cons b (cons 4 '())))") == (4,))
assert (interp_workflow0("(empty? (rest (rest '(b 4))))"))
# print(interp_workflow({},(("funV", ('a', 'b'),{},('/','a','b')),12,3)))
assert (interp_workflow({},(("funV", ('a', 'b'),{},('/','a','b')),12,3)) == 4)
# print(interp_workflow0("(with (div (a b) (/ a b)) (div 12 3))"))
assert (interp_workflow0("(with (div (a b) (/ a b)) (div 12 3))") == 4)
# print (interp_workflow0("(with (mod (a b) (if (>= a b) (mod (- a b) b) a)) (mod 12 4)"))
assert (interp_workflow0("(with (mod (a b) (if (>= a b) (mod (- a b) b) a)) (mod 12 4))") == 0)

def repl():
    print()
    print("Welcome to Workflow REPL...")
    print("type \"exit\" to leave...\n")
    env = {}
    try:
        print(">",end=" ")
        inp = input()
        def interp_with_define(env, wf, override=None):
            # print(env,wf, sep = "\n")
            match(wf):
                case ("define"|"def", (x, *fargs), body):
                    result = ("funV", fargs, env, body)
                    env[x] = result
                    return result
                case ("define"|"def", x ,y):
                    result = y
                    if(y != x):
                        result = interp_workflow(env, y, interp_with_define)
                    env[x] = result
                    return result
                case ("undefine"|"undef", x):
                    return env.pop(x)
                case ("exit" | ("exit",)):
                    raise EOFError()
                case x:
                    return interp_workflow(env, x, interp_with_define)
        
        while (1):
            if(inp != ""):
                inp_sexp = sexp(inp)
                # print("unclosed brackets: ", inp_sexp.num_unclosed)
                while(inp_sexp.num_unclosed > 0):
                    print("..." + "    "*inp_sexp.num_unclosed, end = " ")
                    addition = input()
                    inp = " ".join([inp, addition])
                    inp_sexp = sexp(inp)
                print(repr(interp_with_define(env, inp_sexp.content())))
            print(">",end=" ")
            inp = input()
    except EOFError:
        print("Exiting...")
    except Exception as e:
        print(f"Unhandled Python Exception:")
        raise e

if __name__ == "__main__" or __name__ == "__console__":
    repl()