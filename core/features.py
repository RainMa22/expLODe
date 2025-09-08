import bpy
import math
import random
import re
import typing
from bpy.types import Object as bpyObject

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

def select_target(target):
    deselect_all()
    selected = []
    for obj in target:
        obj.select_set(True)
        selected.append(obj)
    return selected

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
    imported = [obj for obj in bpy.context.selected_objects]
    return imported

def exportFBX(filepath, targets=None):
    targets = targets if targets is not None else bpy.context.scene.objects
    deselect_all()
    for obj in targets:
        obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=filepath,
                             axis_forward='-Z', 
                             axis_up='Y',
                             use_selection=True,
                             object_types= set(("EMPTY", "CAMERA", "LIGHT", "ARMATURE", "MESH", "OTHER")),
                             apply_scale_options='FBX_SCALE_ALL')
    return filepath

def smart_uv_unwrap(target:bpy.types.SceneObjects=None, 
              context: int|str|None=None, undo = None,     
              angle_limit: float | None = 1.15192,
              margin_method: typing.Literal["SCALED", "ADD", "FRACTION"] | None = "SCALED",
              rotate_method: typing.Literal["AXIS_ALIGNED", "AXIS_ALIGNED_X", "AXIS_ALIGNED_Y"]
              | None = "AXIS_ALIGNED_Y",
              island_margin: float | None = 0.01,
              area_weight: float | None = 0.0,
              correct_aspect: bool | None = True,
              scale_to_bounds: bool | None = False):
    target = target if target is not None else get_selected()
    deselect_all()
    changed = []
    for obj in target:
        bpy.context.view_layer.objects.active=obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(context, 
                                 undo, 
                                 angle_limit, 
                                 margin_method,
                                 rotate_method,
                                 island_margin,
                                 area_weight,
                                 correct_aspect,
                                 scale_to_bounds
                                 )
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)
        changed.append(obj)
    return changed

def lvl_one_lod(target:bpy.types.SceneObjects = None):
    return planar_decimate(angle_limit=10.0/180*math.pi, target=target)

def lvl_two_lod(target: bpy.types.SceneObjects = None):
    return unsubdiv(10, target)

def unsubdiv(iterations: int, target:bpy.types.SceneObjects = None, inplace = True, name_override:str = None):
    target = target if target is not None else get_selected()
    fx_name = f"unsubdiv_{iterations}" if name_override is None else name_override
    if(not inplace):
        select_target(target)
        target = dup_and_rename_suffix(new_suffix=fx_name)
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
    return changed

def planar_decimate(angle_limit = math.radians(10.), target = None, inplace=True, name_override:str = None):
    target = target if target is not None else get_selected()
    fx_name = f"planar_{int(angle_limit/math.pi*180)}" if name_override is None else name_override
    if(not inplace):
        select_target(target)
        target = dup_and_rename_suffix(new_suffix=fx_name)
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


def collapse(ratio: float = 0.95, target = None, inplace=True, name_override:str = None):
    target = target if target is not None else get_selected()
    fx_name = f"collapse_{ratio:.02f}" if name_override is None else name_override
    if(not inplace):
        select_target(target)
        target = dup_and_rename_suffix(new_suffix=fx_name)
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

def layer_collection_of(collection: bpy.types.Collection):
    top_layer = bpy.context.view_layer.layer_collection
    exploration_stack = [top_layer]
    while(not len(exploration_stack) == 0):
        layer = exploration_stack.pop()
        if(layer.collection != collection):
            exploration_stack += layer.children
        else:
            return layer

def hide(object: bpyObject):
    hidden = []
    if(not object.hide_get()):
        hidden.append(object)
        object.hide_set(True)
    return hidden    

def unhide(object: bpyObject, unhide_parent = False, exclude = [].copy()):
    if(object in exclude):
        return exclude
    print(f"object {object} is {'not hidden' if not object.hide_get() else 'hidden'}")
    if(object.hide_get()):
        exclude.append(object)
        object.hide_set(False)
    if(unhide_parent):
        while(object.parent):
            if(object in exclude):
                continue
            object = object.parent
            print(f"object {object} is {'not hidden' if not object.hide_get() else 'hidden'}")
            if(object.hide_get()):
                exclude.append(object)
                object.hide_set(False)
    return exclude

def make_invis(object: bpyObject):
    invised = []
    if(not object.hide_viewport):
        invised.append(object)
        object.hide_viewport = True
    return invised    

def make_visible(object: bpyObject, make_visible_parent = False, exclude = [].copy()):
    if object in exclude:
        return exclude
    print(f"object {object} is {'visible' if not object.hide_viewport else 'invisible'}")
    if(object.hide_viewport):
        exclude.append(object)
        object.hide_viewport = False
    if(make_visible_parent):
        for collection in object.users_collection:
            if collection in exclude:
                continue
            print(f"collection {collection} is {'visible' if not collection.hide_viewport else 'invisible'}")
            if(collection.hide_viewport):
                exclude.append(collection)
                collection.hide_viewport = False
            layer_collection = layer_collection_of(collection)
            if layer_collection in exclude:
                continue
            print(f"layer collection of {collection} is {'visible' if not layer_collection.hide_viewport else 'invisible'}")
            if(layer_collection.hide_viewport):
                exclude.append(layer_collection)
                layer_collection.hide_viewport = False
        while(object.parent):
            object = object.parent
            print(f"object {object} is {'visible' if not object.hide_viewport else 'invisible'}")
            if(object.hide_viewport):
                exclude.append(object)
                object.hide_viewport = False
            for collection in object.users_collection:
                if collection in exclude:
                    continue
                print(f"collection {collection} is {'visible' if not collection.hide_viewport else 'invisible'}")
                if(collection.hide_viewport):
                    exclude.append(collection)
                    collection.hide_viewport = False
                layer_collection = layer_collection_of(collection)
                if layer_collection in exclude:
                    continue
                if(layer_collection.hide_viewport):
                    exclude.append(layer_collection)
                    layer_collection.hide_viewport = False
    return exclude