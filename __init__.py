# blender plugin entry point

bl_info = {
    "name": "expLODe",
    "author": "RainMa22",
    "blender": (4,2,0), # Minimum Blender version
    "version": (0,1,0),
    "category": "Import-Export",
    "location": "File > Export > FBX (with LOD)",
	"description": "LOD generation and export as FBX",
}

def register():
    # expLODe.blenderCmd
    from .core.as_blender_plugin import register as reg
    reg()

def unregister():
    from .core.as_blender_plugin import unregister as unreg
    unreg()
