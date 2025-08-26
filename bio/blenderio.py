import subprocess

def open_blender_console(blendercmd):
    # blendercmd = get_config().get("expLODe.blenderCmd")
    return subprocess.Popen([blendercmd, 
                           "-b", 
                           "--python-console"],
                          stdin=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          stdout=None)

def open_blender_python(blendercmd, python_file_path:str):
    # blendercmd = get_config().get("expLODe.blenderCmd")
    return subprocess.Popen([blendercmd, 
                           "-b", 
                           "--python",
                           python_file_path],
                          stdin=subprocess.PIPE,
                        #   stderr=subprocess.STDOUT,
                          stdout=None)