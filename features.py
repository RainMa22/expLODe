import bpy
import math
import random
from copy import copy
import re

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

def deselect_all():
    bpy.ops.object.select_all(action="DESELECT")

def select_all():
    bpy.ops.object.select_all(action="SELECT")
    return bpy.context.selected_objects

def select_regex(regExp:re.Pattern):
    deselect_all()
    for obj in bpy.context.scene.objects:
        if(regExp.match(obj.name) is not None):
            # print(f"{obj.name}: {regExp.match(obj.name)}")
            obj.select_set(True)
    return bpy.context.selected_objects

def get_selected():
    return bpy.context.selected_objects

def select(prefix="", suffix=""):
    return select_regex(re.compile(f"^({prefix}).*({suffix})$",re.MULTILINE))

def add_suffix(suffix=None):
    suffix = suffix if suffix is not None else f"copy{random.randint(0,255)}"
    for obj in bpy.context.selected_objects:
        obj.name += suffix
    return suffix

def dup_and_rename_suffix(prev_suffix="", new_suffix=None):
    new_suffix = new_suffix if new_suffix is not None else f"copy{random.randint(0,255)}"
    bpy.ops.object.duplicate()
    for select_obj in bpy.context.selected_objects:
        select_obj.name = select_obj.name.replace(f"{prev_suffix}.001", f".{new_suffix}")
    return bpy.context.selectable_objects

def remove_scene(scene_name):
    return bpy.data.scenes.remove(bpy.data.scenes[scene_name])

def switch_to_scene(scene_name):
    bpy.context.window.scene=bpy.data.scenes[str(scene_name)]

def importFBX(filepath):
    bpy.ops.import_scene.fbx(filepath=filepath,axis_forward='Z', axis_up='Y')

def exportFBX(filepath):
    bpy.ops.export_scene.fbx(filepath=filepath,axis_forward='Z', axis_up='Y',apply_scale_options='FBX_SCALE_UNITS')

def lvl_one_lod(target:bpy.types.SceneObjects = [].copy()):
    for obj in target:
        if obj.type != 'MESH':
            continue
        modifier:bpy.types.DecimateModifier = obj.modifiers.new(name="lod1.decimate",type="DECIMATE")
        modifier.angle_limit = (10.0/180*math.pi)
        modifier.decimate_type = "DISSOLVE" # planar
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier="lod1.decimate")

def lvl_two_lod(target: bpy.types.SceneObjects = [].copy()):
     for obj in target:
        if obj.type != 'MESH':
            continue
        modifier:bpy.types.DecimateModifier = obj.modifiers.new(name="lod2.decimate",type="DECIMATE")
        modifier.decimate_type="UNSUBDIV"
        modifier.iterations=10
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier="lod2.decimate")

def lvl_one_lod_to_all():
    lvl_one_lod(bpy.context.scene.objects)
        
    
def lvl_two_lod_to_all():
    lvl_two_lod(bpy.context.scene.objects)