import os,sys
# allow for import of features
sys.path.append(os.path.abspath("."))

# import all function from features
from features import *

inFile = r"{inFile}"
outFolder = r"{outFolder}"

new_scene_as_name("fbxOG")
switch_to_scene("fbxOG")
importFBX(f"{inFile}")

remove_scene("Scene")
select_all()
uv_unwrap(get_selected())

# LOD1: planar 10deg
select_all()
add_suffix("OG")
dup_and_rename_suffix(prev_suffix="OG", new_suffix="LOD1")
select(suffix="LOD1")
lvl_one_lod(get_selected())

# LOD2: unsubdiv 10 iterations
select(suffix="OG")
dup_and_rename_suffix(prev_suffix="OG", new_suffix="LOD2")
select(suffix="LOD2")
lvl_two_lod(get_selected())
exportFBX(f"{outFolder}{os.sep}combined.fbx")

