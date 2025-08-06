import bpy
import math
import random
import re


def new_scene(scene_name = None):
    id = scene_name if scene_name is not None else str(random.randbytes(8))
    bpy.ops.scene.new(type='EMPTY')
    bpy.data.scenes[-1].name = str(id)
    return scene_name

def copy_scene(src_scene, scene_name = None):
    id = scene_name if scene_name is not None else str(random.randbytes(8))
    bpy.context.window.screen = bpy.data.scenes[src_scene]
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
    modified = []
    for obj in bpy.context.selected_objects:
        obj.name += suffix
        modified.append(obj)
    return modified

def dup_and_rename_suffix(prev_suffix="", new_suffix=None):
    new_suffix = new_suffix if new_suffix is not None else f"copy{random.randint(0,255)}"
    bpy.ops.object.duplicate()
    changed = []
    for select_obj in bpy.context.selected_objects:
        select_obj.name = select_obj.name.replace(f"{prev_suffix}.001", f".{new_suffix}")
        changed.append(select_obj)
    return changed

def remove_scene(scene_name):
    return bpy.data.scenes.remove(bpy.data.scenes[scene_name])

def switch_scene(scene_name):
    bpy.context.window.scene=bpy.data.scenes[str(scene_name)]

def importFBX(filepath):
    bpy.ops.import_scene.fbx(filepath=filepath,axis_forward='Z', axis_up='Y')
    imported = [obj for obj in bpy.context.selectable_objects]
    return imported

def exportFBX(filepath, target=None):
    target = target if target is not None else bpy.context.scene.objects
    deselect_all()
    for obj in target:
        obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=filepath,
                             axis_forward='Z', 
                             axis_up='Y',
                             use_selection=True,
                             apply_scale_options='FBX_SCALE_UNITS')

def uv_unwrap(target:bpy.types.SceneObjects=bpy.context.selected_objects):
    deselect_all()
    changed = []
    for obj in target:
        bpy.context.view_layer.objects.active=obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)
        changed.append(obj)
    return changed

def lvl_one_lod(target:bpy.types.SceneObjects = None):
    return planar_decimate(angle_limit=10.0/180*math.pi, target=target)

def lvl_two_lod(target: bpy.types.SceneObjects = None):
    return unsubdiv(10, target)

def unsubdiv(iterations: int, target:bpy.types.SceneObjects = None):
    target = target if target is not None else get_selected()
    fx_name = f"unsubdiv_{iterations}"
    changed = []
    for obj in target:
        if obj.type != 'MESH':
            continue
        modifier:bpy.types.DecimateModifier = obj.modifiers.new(name=fx_name,type="DECIMATE")
        modifier.decimate_type="UNSUBDIV"
        modifier.iterations=iterations
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=fx_name)
        changed.append(obj)

def planar_decimate(angle_limit = 10.0/180*math.pi, target = None):
    target = target if target is not None else get_selected()
    fx_name = f"planar_{int(angle_limit/math.pi*180)}"
    changed = []
    for obj in target:
        if obj.type != 'MESH':
            continue
        modifier:bpy.types.DecimateModifier = obj.modifiers.new(name=fx_name,type="DECIMATE")
        modifier.angle_limit = angle_limit
        modifier.decimate_type = "DISSOLVE" # planar
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=fx_name)
        changed.append(obj)
    return changed


def collapse(ratio: float = 0.95, target = None):
    target = target if target is not None else get_selected()
    fx_name = f"collapse_{ratio:.02f}"
    changed = []
    for obj in target:
        if obj.type != 'MESH':
            continue
        modifier:bpy.types.DecimateModifier = obj.modifiers.new(name=fx_name,type="DECIMATE")
        modifier.ratio = ratio
        modifier.decimate_type = "COLLAPSE" # planar
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=fx_name)
        changed.append(obj)
    return changed

def lvl_one_lod_to_all():
    return lvl_one_lod(bpy.context.scene.objects)
        
    
def lvl_two_lod_to_all():
    return lvl_two_lod(bpy.context.scene.objects)
