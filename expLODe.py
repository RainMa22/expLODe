# import bpy
import sys
import argparse
import os
from sexp import make_list, make_string, make_symbol
from expLODe_config import get_config, load_config, check_version
import subprocess

def parse_args():
    parent = os.path.abspath(os.path.dirname(__file__))
    parser = argparse.ArgumentParser(prog="expLODe",
                                     usage="-i (file1.fbx)[,(file2.fbx)] [-o (out folder)] [-s (scriptname).(py|wf)]",
                                     description="a Python3 LOD script using blender")
    parser.add_argument('-i', '--inFiles', default="")
    parser.add_argument('-o', '--outFolder')
    parser.add_argument('--gui',action="store_true", default=False)
    parser.add_argument('-s', '--script', default=os.path.join(parent, "default.wf"))
    
    args = parser.parse_args()
    inFiles: list[str] = args.inFiles.split(",")
    outFolder: str = args.outFolder
    if outFolder is None:
        outFolder = "."
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
            print(f"in file {inFile} does not exist!")
            print(f"Skipping in file {inFile}...")
            inFiles.remove(inFile)
        elif (not os.path.isfile(inFile)):
            print(f"in file {inFile} is not a file!")
            print(f"Skipping in file {inFile}...")
            inFiles.remove(inFile)
        elif (outFolder is None):
            outFolder = os.path.dirname(inFile)
            print(f"inferring outFolder to be: {os.path.abspath(outFolder)}")
    if(len(inFiles) == 0):
        print("Warning: No Valid In File!")
        # exit(1)

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
            "wf_file": wf_file,
            "gui": args.gui}

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
    args = parse_args()
    if args["gui"]:
        from gui.expLODe_gui import expLODe_gui_app,MainWidget
        app = expLODe_gui_app()
        sys.exit(app.exec())
    else:
        check_version()

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
