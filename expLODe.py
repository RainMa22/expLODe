# import bpy
import sys
import argparse
import shutil
import os
import json
from sexp import make_list, make_string, make_symbol
import subprocess
# loads attempts to find blender and use it for later scripts
__config: dict = {}


def load_config():
    global __config
    parent = os.path.dirname(__file__)
    parent = os.path.abspath(parent)
    if (not os.path.exists(parent+os.sep+"config.json")):
        shutil.copyfile(parent+os.sep+"config.default.json",
                        parent+os.sep+"config.json")

    with open(parent+os.sep+"config.json", "r") as file:
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

    with open(parent+os.sep+"config.json", "w") as file:
        file.write(json.dumps(__config))


def get_config():
    return __config.copy()


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
    with subprocess.Popen((blender_command + " --version").split(" "), stdout=subprocess.PIPE).stdout as proc_out:
        v_string = proc_out.readline().decode()
        v_ver = v_string.split(" ")[1]
        v_major, v_minor, v_patch = (int(x) for x in v_ver.split("."))

    print(v_major, v_minor, v_patch, sep=".")
    if (v_major != 4 or v_minor < 2):
        print(f"invalid version {v_ver}! Blender >= 4.2, < 5.0.0 expected!")

    print("blender version satisfied")


def parse_args():
    parent = os.path.abspath(os.path.dirname(__file__))
    parser = argparse.ArgumentParser(prog="expLODe",
                                     usage="-i (file1.fbx)[,(file2.fbx)] [-o (out folder)] [-s (scriptname).(py|wf)]",
                                     description="a Python3 LOD script using blender")
    parser.add_argument('-i', '--inFiles', required=True)
    parser.add_argument('-o', '--outFolder')
    parser.add_argument('-s', '--script', default=os.path.join(parent, "default.wf"))
    
    args = parser.parse_args()
    inFiles: list[str] = args.inFiles.split(",")
    outFolder: str = args.outFolder
    wf_file:str = ""
    script: str = ""
    
    if(args.script.lower().endswith(".py")):
        script = args.script
        wf_file = None
    elif(args.script.lower().endswith(".wf")):
        script = os.path.join(parent, "features_wf.py")
        wf_file = args.script
    
    if (inFiles is None):
        parser.print_usage()
        exit(1)
    for inFile in inFiles:
        if (not os.path.exists(inFile)):
            print(f"in file {args.inFile} does not exist!")
            print(f"Skipping in file {args.inFile}...")
            inFiles.remove(inFile)
        elif (not os.path.isfile(inFile)):
            print(f"in file {args.inFile} is not a file!")
            print(f"Skipping in file {args.inFile}...")
            inFiles.remove(inFile)
        elif (outFolder is None):
            outFolder = os.path.dirname(inFile)
            print(f"inferring outFolder to be: {os.path.abspath(outFolder)}")
    if(len(inFiles) == 0):
        print("No Valid In File! Exiting...")
        exit(1)

    if(not os.path.exists(script)):
        print(f"workflow script \"{script}\" does not exists!")
        exit(1)
    elif(not os.path.isfile(script)):
        print(f"workflow script \"{script}\" is not a file!")
        exit(2)

    inFiles = make_list(map(lambda inFile: make_string(os.path.abspath(inFile)), inFiles))
    outFolder = make_string(os.path.abspath(outFolder))

    return {"inFiles": inFiles, 
            "outFolder": outFolder, 
            "script": script,
            "wf_file": wf_file,}

def open_blender_console():
    blender = get_config().get("expLODe.blenderCmd")
    return subprocess.Popen([blender, 
                           "-b", 
                           "--python-console"],
                          stdin=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          stdout=None)

def open_blender_python(python_file_path:str):
    blender = get_config().get("expLODe.blenderCmd")
    return subprocess.Popen([blender, 
                           "-b", 
                           "--python",
                           python_file_path],
                          stdin=subprocess.PIPE,
                        #   stderr=subprocess.STDOUT,
                          stdout=None)

def main():
    load_config()
    check_version()
    args = parse_args()
    script = args.pop("script")
    wf_file = args.pop("wf_file")
    if(wf_file is not None):
        with open_blender_python(script) as proc:
            proc_in = proc.stdin
            for key,val in args.items():
                proc_in.write(f"(def {key} {repr(val)})\n".encode())
                print(f"(def {key} {repr(val)})\n")
            proc_in.flush()

            with open(wf_file) as file:
                text = file.read()
                proc_in.write(text.encode())
                print(text)
            proc_in.flush()

            proc_in.write(f"\nexit\n".encode())
            proc_in.flush()
            input()
            proc_in.close()
    else:
        with open_blender_console() as proc:
            proc_in = proc.stdin
            for key,val in args.items():
                proc_in.write(f"{key}={repr(val)}\n".encode())
                print(f"{key}={repr(val)}")
            proc_in.flush()

            with open(script) as file:
                text = file.read()
                proc_in.write(text.encode())
                print(text)
            proc_in.flush()
            input()
            proc_in.close()


if __name__ == "__main__":
    main()
