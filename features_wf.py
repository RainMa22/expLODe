import math
import os
import sys

# allow for import of features
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from features import *
from sexp import sexp


def interp_workflow(env: dict, wf):
    # print(env,wf, sep = "\n")
    def interp(wf):
        return interp_workflow(env, wf)
    match(wf):
        # (with (x, y) (...))
        case ("with", (x, y), rest):
            newEnv = {}
            newEnv.update(env)
            newEnv[x] = interp_workflow(env, interp(y))
            return interp_workflow(newEnv, rest)
        # (add x y) | (+ x y)
        case ("add" | "+", x, y):
            print(interp(x), interp(y))
            return interp(x) + interp(y)
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
        case ("if", cond, a, b):
            if(interp(cond)):
                return interp(a)
            else: 
                return(interp(b))
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
        case ("new-scene"):
            return ("Scene", new_scene())
        case ("new-scene", name):
            return ("Scene", new_scene(interp(name)))
        case ("copy-scene", ("Scene", src_scene)):
            return ("Scene", copy_scene(interp(src_scene)))
        case ("copy-scene", ("Scene", src_scene), scene_name):
            return ("Scene", copy_scene(interp(src_scene), interp(env, scene_name)))
        case ("import", "FBX", path):
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
        case x:
            return env.get(x) if x in env.keys() else x


def interp_workflow0(wf0):
    return interp_workflow({}, sexp(wf0))

# def testLOD1():
#     folder = os.path.abspath(os.path.dirname(__file__))
#     test_fbx_file = os.sep.join([folder, "test.fbx"])
#     out_fbx_file = os.sep.join([folder, "testLOD1.fbx"])
#     workflow = f"""
#     (with (inFile {test_fbx_file})
#         (with (outFile {out_fbx_file})
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
#     (with (inFile {test_fbx_file})
#         (with (outFile {out_fbx_file})
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
assert (interp_workflow0("(first (b 4))") == 'b')
assert (interp_workflow0("(rest (b 4))") == (4,))
assert (interp_workflow0("(empty? (rest (rest (b 4))))"))

def repl():
    print()
    print("Welcome to Workflow REPL...")
    print("type \"exit\" to leave...\n")
    env = {}
    inp = input()
    def interp_with_define(wf):
        match(wf):
            case ("define"|"def", x ,y):
                result = y
                if(y != x):
                    result = interp_workflow(env, y)
                env[x] = result
                return result
            case ("undefine"|"undef", x):
                return env.pop(x)
            case x:
                return interp_workflow(env, x)
    
    while (inp != "exit"):
        if(inp != ""):
            print(interp_with_define(sexp(inp)))
        inp = input()

if __name__ == "__main__":
    repl()