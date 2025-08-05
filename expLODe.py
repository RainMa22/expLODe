import bpy
import shutil
import os
import json


# loads attempts to find blender and use it for later scripts
config : dict = {}

if(not os.path.exists("config.json")):
    shutil.copyfile("config.default.json","config.json")

with open("config.json", "r") as file:
    config = json.loads(file.read())

blender_command = config.get("expLODe.blenderCmd")
if(blender_command is None or blender_command == ""):
    print("Blender path not defined! Attempting to find automatically...")
    blenderPath = shutil.which("blender")
    if(blenderPath is None):
        print("Blender is not on PATH!")
    else: 
        blender_command = blenderPath

config["expLODe.blenderCmd"] = blender_command if blender_command is not None else ""

with open("config.json", "w") as file:
    config = file.write(json.dumps(config))

if blender_command is None or blender_command == "":
    print("Unable to Find Blender!")
    print("Please configure `expLODe.blenderCmd` in config.json!")
    print("Exiting...")
    exit()