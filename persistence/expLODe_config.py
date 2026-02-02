# loads attempts to find blender and use it for later scripts
import json
import os
import shutil
import subprocess
import sys
from globals import expLODe_root as proj_root
from os.path import join as path_join


__config: dict = {}


def load_config():
    global __config
    config_json_path = path_join(proj_root, "config.json")
    default_json_path = path_join(proj_root, "config.default.json")
    if (not os.path.exists(config_json_path)):
        shutil.copyfile(default_json_path, config_json_path)

    with open(config_json_path, "r") as file:
        __config = json.loads(file.read())

    blender_command = __config.get("expLODe.blenderCmd")

    if ("blender" in sys.argv[0].lower()):
        print(f"Using provided argument ${sys.argv[0]} as blender command")
        blender_command = sys.argv[0]
    if (blender_command is None or blender_command == ""):
        print("Blender path not defined! Attempting to find automatically...")
        blenderPath = shutil.which("blender")
        if (blenderPath is None):
            print("Blender is not on PATH!")
        else:
            blender_command = blenderPath

    __config["expLODe.blenderCmd"] = blender_command if blender_command is not None else ""
    write_config(__config)


def get_config():
    if(__config == {}):
        load_config()
    return __config.copy()

def write_config(config: dict):
    global __config
    __config = config
    with open(path_join(proj_root, "config.json"), "w") as file:
        file.write(json.dumps(config))

def check_version():
    blender_command = get_config().get("expLODe.blenderCmd")
    if blender_command is None or blender_command == "":
        print("Unable to Find Blender!")
        print("Please configure `expLODe.blenderCmd` in config.json!")
        print("Exiting...")
        exit()

    print("Blender found, checking version")

    v_string = ""
    v_ver = ""
    v_major = -1
    v_minor = -1
    v_patch = -1
    try:
        with subprocess.Popen((blender_command + " --version").split(" "), stdout=subprocess.PIPE).stdout as proc_out:
            v_string = proc_out.readline().decode()
            v_ver = v_string.split(" ")[1]
            v_major, v_minor, v_patch = (int(x) for x in v_ver.split("."))
    except:
        pass
    print(v_major, v_minor, v_patch, sep=".")
    if not (5.0 >= float(f"{v_major}.{v_minor}") >= 4.2 ):
        print(f"invalid version {v_ver}! Blender >= 4.2, <= 5.0 expected!")
        return False

    print("blender version satisfied")
    return True