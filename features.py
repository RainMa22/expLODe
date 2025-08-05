import bpy

def importFBX(filepath):
    bpy.ops.import_scene.fbx(filepath,axis_forward='Z', axis_up='Y')
    