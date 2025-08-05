import bpy
import math
import random

def newScene():
    id = random.randbytes(8)
    bpy.ops.scene.new(type='EMPTY')
    bpy.data.scenes[-1].name = str(id)
    bpy.context.window.scene=bpy.data.scenes[str(id)]

def importFBX(filepath):
    bpy.ops.import_scene.fbx(filepath=filepath,axis_forward='Z', axis_up='Y')

def exportFBX(filepath):
    bpy.ops.export_scene.fbx(filepath=filepath,axis_forward='Z', axis_up='Y',apply_scale_options='FBX_SCALE_UNITS')

def lvl_one_lod_to_all():
    modifier = bpy.types.DecimateModifier() 
    modifier.angle_limit = (10.0/180*math.pi)
    modifier.decimate_type = "DISSOLVE" # planar
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        bpy.context.active_object = obj
        bpy.ops.object.modifier_apply(modifier)
    
def lvl_two_lod_to_all():
    modifier = bpy.types.DecimateModifier()
    modifier.decimate_type="UNSUBDIV"
    modifier.iterations=10
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        bpy.context.active_object = obj
        bpy.ops.object.modifier_apply(modifier)