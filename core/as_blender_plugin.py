import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import CollectionProperty,StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator 
import math, mathutils
import sys

from .features import *


class EXPLODE_PROP_LODconfig(bpy.types.PropertyGroup):

    def update_name(self, context):
        names = list(map(lambda key: context.scene.explode_LODs[key].name, context.scene.explode_LODs.keys()))
        print(f"{names=}")
        while len(set(names)) != len(names):
            if self.name[-1] in "0123456789":
                self.name = f"{self.name[:-1]}{int(self.name[-1]) + 1}"
            else:
                self.name += "1"
            names = list(map(lambda key: context.scene.explode_LODs[key].name, context.scene.explode_LODs.keys()))


    name: StringProperty(default="LOD1",
                         description="name of the LOD and the suffix of the LOD mesh on export",
                         update=update_name)
    
    type: EnumProperty(name="type",
        items=(("Planar", "Planar Decimate",""),
            ("Unsubdiv", "Unsubdivide Decimate",""),
            ("Collapse", "Collapse Decimate","")),
            default="Planar")
    
    _PROPERTIES = {
        "Planar": "angle_limit",
        "Unsubdiv": "iterations",
        "Collapse": "ratio",
    }
    # Planar only
    angle_limit: FloatProperty(name = "Angle Limit",
                            description = "Planar Modifier Angle Limit",
                            min=0,
                            max=math.pi,
                            default=math.radians(10.),
                            subtype="ANGLE")
    # Iterations
    iterations: IntProperty(name = "Iterations", default=10,
                        min=0, max=32767)
    # collapse only
    ratio: FloatProperty(name = "ratio",
                         description= "collapse ratio",
                         default=0.95,
                         min = 0.,
                         max = 1.0)
    
    show_self: BoolProperty(default=True, options={"HIDDEN"})
    

    def apply_to_objs(self, objs: typing.Iterable[bpyObject], inplace=False):
        match self.type:
            case "Planar":
                return planar_decimate(self.angle_limit, objs, inplace, self.name)
            case "Unsubdiv":
                return unsubdiv(self.iterations, objs, inplace, self.name)
            case "Collapse":
                return collapse(self.ratio,objs, inplace, self.name)

    def draw_self(self, layout:bpy.types.UILayout, context:bpy.types.Context):
        row = layout.row()
        row.label(text="LOD Editor:")
        icon = 'TRIA_DOWN' if self.show_self else 'TRIA_RIGHT'
        row.prop(self, "show_self", icon=icon, icon_only=True)
        layout.separator()
        if(self.show_self):
            layout.prop(self, "name")
            layout.prop(self, "type")
            layout.prop(self, EXPLODE_PROP_LODconfig._PROPERTIES[self.type])

class EXPLODE_UL_loLODConfig(bpy.types.UIList):
    bl_idname = "EXPLODE_UL_loLODConfig"
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, *, index = 0, flt_flag = 0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                layout.prop(item, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="None", translate=False, icon_value=icon)
            # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

# Adapted Code from https://github.com/EdyJ/blender-to-unity-fbx-exporter
# MIT License
# Copyright (c) 2020 Angel García "Edy"

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
class expLODeFBXExporter(Operator, ExportHelper):
    """
    offers Unity-compatible FBX exports with LOD options 
    """
    bl_idname = "export_scene.explode_fbx"
    bl_label = "Export FBX"
    bl_options = {'UNDO_GROUPED'}

    filename_ext = ".fbx"

    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    active_collection: BoolProperty(
        name="Active Collection Only",
        description="Export objects in the active collection only (and its children). ",
        default=False,
    )

    selected_objects: BoolProperty(
        name="Selected Objects Only",
        description="Export selected objects only. ",
        default=False,
    )

    deform_bones: BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones (and non-deforming ones when they have deforming children)",
        default=False,
    )

    leaf_bones: BoolProperty(
        name="Add Leaf Bones",
        description="Append a final bone to the end of each chain to specify last bone length "
        "(use this when you intend to edit the armature from exported data)",
        default=False,
    )

    triangulate_faces: BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles. " \
        "This is necessary for exporting tangents in meshes with N-gons. " \
        "Otherwise Unity will show a warning when importing tangents in these meshes",
        default=False,
    )

    primary_bone_axis: EnumProperty(
        name="Primary",
        items=(('X', "X Axis", ""),
                ('Y', "Y Axis", ""),
                ('Z', "Z Axis", ""),
                ('-X', "-X Axis", ""),
                ('-Y', "-Y Axis", ""),
                ('-Z', "-Z Axis", ""),
        ),
        default='Y',
    )

    secondary_bone_axis: EnumProperty(
        name="Secondary",
        items=(('X', "X Axis", ""),
                ('Y', "Y Axis", ""),
                ('Z', "Z Axis", ""),
                ('-X', "-X Axis", ""),
                ('-Y', "-Y Axis", ""),
                ('-Z', "-Z Axis", ""),
        ),
        default='X',
    )

    tangent_space: BoolProperty(
        name="Export tangents",
        description="Add binormal and tangent vectors, " \
        "together with normal they form the tangent space (tris/quads only). " \
        "Meshes with N-gons won't export tangents unless the option Triangulate Faces is enabled",
        default=False,
    )



    def draw(self, context):
        layout = self.layout
        layout.row().label(text = "Selection")
        layout.row().prop(self, "active_collection")
        layout.row().prop(self, "selected_objects")

        layout.separator()
        layout.row().label(text = "Meshes")
        layout.row().prop(self, "triangulate_faces")
        layout.row().prop(self, "tangent_space")

        layout.separator()
        layout.row().label(text = "Armatures")
        layout.row().prop(self, "deform_bones")
        layout.row().prop(self, "leaf_bones")

        layout.row().label(text = "Bone Axes")
        split = layout.split(factor=0.4)
        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text = "Primary")
        split.column().prop(self, "primary_bone_axis", text="")
        split = layout.split(factor=0.4)
        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text = "Secondary")
        split.column().prop(self, "secondary_bone_axis", text="")
        layout.separator()
        row = layout.row()
        icon = 'TRIA_DOWN' if context.scene.expLODe_export_lod_panel_open else 'TRIA_RIGHT'
        row.label(text="LODs:")
        row.prop(context.scene, "expLODe_export_lod_panel_open", icon=icon, icon_only=True)
        if context.scene.expLODe_export_lod_panel_open:
            row = layout.row()
            split = row.split()
            split.template_list(EXPLODE_UL_loLODConfig.bl_idname,"LOLOD_full",context.scene, "explode_LODs",context.scene,"explode_LODIndex")
            column = row.column()
            column.operator(EXPLODE_OT_add_item.bl_idname,icon="ADD",text="")
            column.operator(EXPLODE_OT_remove_item.bl_idname,icon="REMOVE",text="")
            LODs:bpy.types.CollectionProperty = context.scene.explode_LODs
            active_idx=context.scene.explode_LODIndex
            if(len(LODs.items()) == 0):
                return
            active_lodconf: EXPLODE_PROP_LODconfig = LODs.get(LODs.keys()[active_idx])
            if(active_lodconf):
                active_lodconf.draw_self(layout,context)
 
    def execute(self, context):
        bpy.ops.ed.undo_push(message="STARTED FBX EXPORT")
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")

        targets = [obj for obj in bpy.data.objects if obj and obj in list(context.scene.objects)]
        unhid = []
        visibled = []
        for target in targets:
            unhid = unhide(target, unhide_parent=True, exclude=unhid)
            visibled = make_visible(target,make_visible_parent=True, exclude=visibled)
        print(f"unhid: {unhid}")
        print(f"visibled: {visibled}")
        if(self.active_collection):
            active_collection = context.view_layer.active_layer_collection.collection
            targets = [obj for obj in targets if obj in list(active_collection.objects)]
        if(self.selected_objects):
            targets = [obj for obj in targets if obj in context.selected_objects]
        print(targets)

        for target in targets:
            context.view_layer.objects.active = target
            for constraint in target.constraints:
                bpy.ops.constraint.apply(constraint=constraint.name)
            for modifier in target.modifiers:
                bpy.ops.object.modifier_apply(modifier=modifier.name)

        make_unity_compatible(targets=targets, inplace=True,name_override="")
        
        LODs:bpy.types.CollectionProperty = context.scene.explode_LODs
        def apply_lod_config(configname: str):
            config:EXPLODE_PROP_LODconfig = LODs[configname]
            return config.apply_to_objs(targets)
        
        LODs= list(map(apply_lod_config, context.scene.explode_LODs.keys()))
        print(LODs)
        for LOD in LODs:
            targets += LOD
        
        # for(config: LODConfig in context.scene.explod_LODs):

        print(self.filepath)
        exportFBX(self.filepath,targets, 
                  use_armature_deform_only=self.deform_bones,
                  add_leaf_bones=self.leaf_bones,
                  use_triangles=self.triangulate_faces,
                  primary_bone_axis=self.primary_bone_axis,
                  secondary_bone_axis=self.secondary_bone_axis,
                  use_tspace=self.tangent_space
                  )
        bpy.ops.ed.undo_push(message="")
        bpy.ops.ed.undo()
        return {"FINISHED"}

def menu_func_export(self, context):
    self.layout.operator(expLODeFBXExporter.bl_idname, text="FBX (Unity-compatible, with LOD)")


class EXPLODE_OT_add_item(bpy.types.Operator):
    bl_idname = "export_scene.explode_add_item"
    bl_label = "Add Item"

    def execute(self, context):
        item:EXPLODE_PROP_LODconfig = context.scene.explode_LODs.add()
        item.name = item.name
        # print(context.scene.explode_LODs.items())
        return {'FINISHED'}

class EXPLODE_OT_remove_item(bpy.types.Operator):
    bl_idname = "export_scene.explode_remove_item"
    bl_label = "Remove Item"

    def execute(self, context):
        index = context.scene.explode_LODIndex
        if index >= 0 and index < len(context.scene.explode_LODs):
            context.scene.explode_LODs[index]
            context.scene.explode_LODs.remove(index)
            context.scene.explode_LODIndex = min(index, len(context.scene.explode_LODs) - 1)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(expLODeFBXExporter)
    bpy.utils.register_class(EXPLODE_UL_loLODConfig)
    bpy.utils.register_class(EXPLODE_OT_add_item)
    bpy.utils.register_class(EXPLODE_OT_remove_item)
    bpy.utils.register_class(EXPLODE_PROP_LODconfig)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.Scene.expLODe_export_lod_panel_open = BoolProperty(
        default=False
    )
    bpy.types.Scene.explode_LODs = CollectionProperty(type=EXPLODE_PROP_LODconfig, 
                              name="LODs",
                              description="Additional LOD meshes to generate and export",
                              )
    
    bpy.types.Scene.explode_LODIndex = IntProperty()


def unregister():
    bpy.utils.unregister_class(expLODeFBXExporter)
    bpy.utils.unregister_class(EXPLODE_UL_loLODConfig)
    bpy.utils.unregister_class(EXPLODE_OT_add_item)
    bpy.utils.unregister_class(EXPLODE_OT_remove_item)
    bpy.utils.unregister_class(EXPLODE_PROP_LODconfig)
    
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    del bpy.types.Scene.expLODe_export_lod_panel_open