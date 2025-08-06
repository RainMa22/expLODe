import bpy
import math

from features import *

def interp_workflow(env, wf):
    def interp(wf):
        return interp_workflow(env,wf)
    match(wf):
        # ["with" (x, y) (...)]
        case ("with", (x, y), rest):
            newEnv = {}
            newEnv.update(env)
            newEnv[x] = interp_workflow(env, interp(y))
            interp_workflow(newEnv, rest)
        case ("add", x, y):
            return interp(x) + interp(y)
        case ("+", x, y):
            return interp(x) + interp(y)
        case ("sub", x,y):
            return interp(x) - interp(y)
        case ("-", x,y):
            return interp(x) - interp(y)        
        case ("multiply", x,y):
            return interp(x) * interp(y)
        case ("*", x,y):
            return interp(x) * interp(y)        
        case ("divide", x,y):
            return interp(x) / interp(y)
        case ("/", x,y):
            return interp(x) / interp(y)
        case ("deg", degree):
            return degree/180*math.pi
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
            return (exportFBX(path))
        case ("export", "FBX", interp(path), interp(target)):
            return tuple(exportFBX(interp(path), interp(target)))
        case ("uv-unwrap", "ALL"):
            return tuple(uv_unwrap())
        case ("uv-unwrap", objects):
            return tuple(uv_unwrap(interp(objects)))
        case ("unsubdiv", iterations):
            return tuple(unsubdiv(interp(iterations)))
        case ("unsubdiv", iterations, target):
            return tuple(unsubdiv(interp(iterations), interp(target)))
        case ("planar", angle_limit_rad):
            return tuple(planar_decimate(interp(angle_limit_rad)))
        case ("planar", angle_limit_rad, target):
            return tuple(planar_decimate(interp(angle_limit_rad), interp(target)))
        case ("collapse", ratio):
            return tuple(collapse(interp(ratio), interp(target)))
        case ("collapse", ratio, target):
            return tuple(collapse(interp(ratio), interp(target)))
        case (x):
            return env[x]
        
def interp_workflow0(wf0):
    return interp_workflow({}, tuple(wf0.split(" ")))