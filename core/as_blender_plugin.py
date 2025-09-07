import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator 
import math,mathutils

from .features import *

class expLODePlugin(Operator, ExportHelper):
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
    ) # pyright: ignore[reportInvalidTypeForm]

    active_collection: BoolProperty(
        name="Active Collection Only",
        description="Export objects in the active collection only (and its children). ",
        default=False,
    ) # pyright: ignore[reportInvalidTypeForm]

    selected_objects: BoolProperty(
        name="Selected Objects Only",
        description="Export selected objects only. ",
        default=False,
    ) # pyright: ignore[reportInvalidTypeForm]

    deform_bones: BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones (and non-deforming ones when they have deforming children)",
        default=False,
    ) # pyright: ignore[reportInvalidTypeForm]

    leaf_bones: BoolProperty(
        name="Add Leaf Bones",
        description="Append a final bone to the end of each chain to specify last bone length "
        "(use this when you intend to edit the armature from exported data)",
        default=False,
    ) # pyright: ignore[reportInvalidTypeForm]

    triangulate_faces: BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles. " \
        "This is necessary for exporting tangents in meshes with N-gons. " \
        "Otherwise Unity will show a warning when importing tangents in these meshes",
        default=False,
    ) # pyright: ignore[reportInvalidTypeForm]

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
    ) # pyright: ignore[reportInvalidTypeForm]

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
    ) # pyright: ignore[reportInvalidTypeForm]

    tangent_space: BoolProperty(
        name="Export tangents",
        description="Add binormal and tangent vectors, " \
        "together with normal they form the tangent space (tris/quads only). " \
        "Meshes with N-gons won't export tangents unless the option Triangulate Faces is enabled",
        default=False,
    ) # pyright: ignore[reportInvalidTypeForm]

    

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
        # return super().draw(context)
 
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

        for target in targets:
            # reset parent inverse
            if target.parent:
                world_mat = target.matrix_world.copy()
                target.matrix_parent_inverse.identity()
                target.matrix_basis = target.parent.matrix_world.inverted() @ world_mat
            mat_original = target.matrix_local.copy()
            target.matrix_local = mathutils.Matrix.Rotation(math.radians(-90.), 4, 'X')
            # apply rotation and scale
            deselect_all()
            target.select_set(True)
            context.view_layer.objects.active = target
            bpy.ops.object.transform_apply(location= False, rotation=True, scale=True)
            # this fixes unity's rotation offset
            target.matrix_local = mat_original @ mathutils.Matrix.Rotation(math.radians(90.), 4, "X")
            bpy.context.view_layer.update()

        print(self.filepath)
        exportFBX(self.filepath,targets)
        bpy.ops.ed.undo_push(message="")
        bpy.ops.ed.undo()
        return {"FINISHED"}

def menu_func_export(self, context):
    self.layout.operator(expLODePlugin.bl_idname, text="FBX (Unity-compatible, with LOD)")

def register():
    bpy.utils.register_class(expLODePlugin)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(expLODePlugin)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)