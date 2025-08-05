import bpy
import math
import random

def new_scene_as_name(scene_name = None):
    id = scene_name if scene_name is not None else str(random.randbytes(8))
    bpy.ops.scene.new(type='EMPTY')
    bpy.data.scenes[-1].name = str(id)
    return scene_name

def copy_scene_to_name(scene_name = None):
    id = scene_name if scene_name is not None else str(random.randbytes(8))
    bpy.ops.scene.new(type='FULL_COPY')
    bpy.context.scene.name = str(id)
    return scene_name

def remove_scene(scene_name):
    return bpy.data.scenes.remove(bpy.data.scenes[scene_name])

def switch_to_scene(scene_name):
    bpy.context.window.scene=bpy.data.scenes[str(scene_name)]

def importFBX(filepath):
    bpy.ops.import_scene.fbx(filepath=filepath,axis_forward='Z', axis_up='Y')

def exportFBX(filepath):
    bpy.ops.export_scene.fbx(filepath=filepath,axis_forward='Z', axis_up='Y',apply_scale_options='FBX_SCALE_UNITS')

def lvl_one_lod_to_all():
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        modifier:bpy.types.DecimateModifier = obj.modifiers.new(name="lod1.decimate",type="DECIMATE")
        modifier.angle_limit = (10.0/180*math.pi)
        modifier.decimate_type = "DISSOLVE" # planar
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier="lod1.decimate")
    
def lvl_two_lod_to_all():
    # modifier = bpy.types.DecimateModifier()
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        modifier:bpy.types.DecimateModifier = obj.modifiers.new(name="lod2.decimate",type="DECIMATE")
        modifier.decimate_type="UNSUBDIV"
        modifier.iterations=10
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier="lod2.decimate")