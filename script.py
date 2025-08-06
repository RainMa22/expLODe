import os,sys
sys.path.append(os.path.abspath("."))

from features import *

inFile = r"{inFile}"
outFolder = r"{outFolder}"

new_scene_as_name("fbxOG")
switch_to_scene("fbxOG")
importFBX(f"{inFile}")

remove_scene("Scene")
select_all()
uv_unwrap(get_selected())

select_all()
add_suffix("OG")
dup_and_rename_suffix(prev_suffix="OG", new_suffix="LOD1")
select(suffix="LOD1")
lvl_one_lod(get_selected())

select(suffix="OG")
dup_and_rename_suffix(prev_suffix="OG", new_suffix="LOD2")
select(suffix="LOD2")
lvl_two_lod(get_selected())
exportFBX(f"{outFolder}{os.sep}combined.fbx")

