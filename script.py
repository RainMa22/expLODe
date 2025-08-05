import os,sys
sys.path.append(os.path.abspath("."))

from features import *

new_scene_as_name("fbxOG")
switch_to_scene("fbxOG")
importFBX(r"{inFile}")

remove_scene("Scene")
copy_scene_to_name("fbxLOD1")
copy_scene_to_name("fbxLOD2")

switch_to_scene("fbxLOD1")
lvl_one_lod_to_all()
exportFBX(r"{outFolder}{os.sep}LOD1.fbx")

switch_to_scene("fbxLOD2")
lvl_two_lod_to_all()
exportFBX(r"{outFolder}{os.sep}LOD2.fbx")

