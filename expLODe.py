import bpy
import sys
import argparse
import shutil
import os
import json
import subprocess

# loads attempts to find blender and use it for later scripts
__config : dict = {}

def load_config():
    global __config
    parent=os.path.dirname(__file__)
    parent=os.path.abspath(parent)
    if(not os.path.exists(parent+os.sep+"config.json")):
        shutil.copyfile(parent+os.sep+"config.default.json",
                        parent+os.sep+"config.json")

    with open(parent+os.sep+"config.json", "r") as file:
        __config = json.loads(file.read())

    blender_command = __config.get("expLODe.blenderCmd")

    if("blender" in sys.argv[0].lower()):
        print(f"Using provided argument ${sys.argv[0]} as blender command")
        blender_command = sys.argv[0]
    if(blender_command is None or blender_command == ""):
        print("Blender path not defined! Attempting to find automatically...")
        blenderPath = shutil.which("blender")
        if(blenderPath is None):
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

    v_string=""
    v_ver=""
    v_major=-1
    v_minor=-1
    v_patch=-1
    with subprocess.Popen((blender_command + " --version").split(" "), stdout=subprocess.PIPE).stdout as proc_out:
        v_string = proc_out.readline().decode()
        v_ver = v_string.split(" ")[1]
        v_major,v_minor,v_patch = (int(x) for x in v_ver.split("."))

    print(v_major,v_minor,v_patch, sep=".")
    if(v_major != 4 or v_minor < 2):
        print(f"invalid version {v_ver}! Blender >= 4.2, < 5.0.0 expected!")
        
    print("blender version satisfied")

def parse_args():
    parser = argparse.ArgumentParser(prog="expLODe", 
                                     usage="-i (file).fbx [-o (out folder)]",
                                     description="a Python3 LOD script using blender")
    parser.add_argument('-i', '--inFile')
    parser.add_argument('-o', '--outFolder')
    args = parser.parse_args()
    inFile:str = args.inFile
    outFolder:str = args.outFolder
    if(inFile is None):
        parser.print_usage()
        exit(1)
    else:
        inFile = inFile if args.inFile.lower().endswith(".fbx") else (args.inFile + ".fbx") 
    if(not os.path.exists(inFile)):
        print(f"in file {args.inFile} does not exist!")
        exit(1)
    elif(not os.path.isfile(inFile)):
        print(f"in file {args.inFile} is not a file!")
        exit(2)
    elif(outFolder is None):
        outFolder=os.path.dirname(args.inFile)
        outFolder = os.path.abspath(outFolder)
    print(f"using out folder {outFolder}")
    return inFile, outFolder
        
def main():
    load_config()
    check_version()
    inFile, outFolder = parse_args()
    print(inFile, outFolder)

if __name__ == "__main__":
    main()

