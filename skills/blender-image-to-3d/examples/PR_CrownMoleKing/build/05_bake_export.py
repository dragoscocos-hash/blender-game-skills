"""Delivery copy for roblox-prop: join LOW into two MeshParts (Body, Jewels), UV unwrap, bake the flat
material colours into one 512 colour atlas per part (metallic forced to 0 for the bake, see
blender-5-notes), rebuild simple delivery materials, export GLB to exports/roblox-prop/.
The master LOW objects are untouched (non-destructive)."""
import bpy, sys, os

U = 0.34
a = sys.argv[sys.argv.index("--") + 1:]
MASTER = a[a.index("--master") + 1]
OUT = a[a.index("--out") + 1]
RES = 512

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(MASTER))
scn = bpy.context.scene
scn.render.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = 4

low = [o for o in bpy.data.collections["LOW"].objects if o.type == "MESH"]
jewel_mats = {"M_Ruby"} | {m for m in bpy.data.materials.keys() if m.startswith("M_Gem")}


def dup_join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    copies = []
    for o in objs:
        c = o.copy()
        c.data = o.data.copy()
        bpy.data.collections["EXPORT"].objects.link(c)
        copies.append(c)
    for c in copies:
        c.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


jewels = [o for o in low if o.data.materials and o.data.materials[0].name in jewel_mats]
body = [o for o in low if o not in jewels]
parts = [dup_join(body, "PR_CrownMoleKing_Body"), dup_join(jewels, "PR_CrownMoleKing_Jewels")]

for ob in parts:
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()                          # lock triangulation before bake
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.01)  # no sharp-seam option (5.0 island shatter)
    bpy.ops.object.mode_set(mode="OBJECT")

    img = bpy.data.images.new(ob.name + "_Color", RES, RES)
    saved = []
    for m in ob.data.materials:                                   # bake target node + metallic 0
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        saved.append((bsdf, bsdf.inputs["Metallic"].default_value))
        bsdf.inputs["Metallic"].default_value = 0.0
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        nt.nodes.active = t
    scn.render.bake.use_pass_direct = False
    scn.render.bake.use_pass_indirect = False
    scn.render.bake.margin = 8
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
    for bsdf, mv in saved:
        bsdf.inputs["Metallic"].default_value = mv
    tex_path = os.path.join(OUT, img.name + ".png")
    os.makedirs(OUT, exist_ok=True)
    img.filepath_raw = tex_path
    img.file_format = "PNG"
    img.save()

    # one delivery material per part, textured with the atlas
    dm = bpy.data.materials.new(ob.name + "_Mat")
    dm.use_nodes = True
    nt = dm.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.0 if "Jewels" in ob.name else 0.5
    bsdf.inputs["Roughness"].default_value = 0.2 if "Jewels" in ob.name else 0.4
    ob.data.materials.clear()
    ob.data.materials.append(dm)

bpy.ops.object.select_all(action="DESELECT")
for ob in parts:
    ob.select_set(True)
glb = os.path.join(OUT, "PR_CrownMoleKing.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_materials="EXPORT", export_cameras=False, export_lights=False)
for ob in parts:
    print("PART", ob.name, "tris", len(ob.data.polygons))
print("EXPORTED", glb)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(MASTER.replace("_master", "_baked")))
