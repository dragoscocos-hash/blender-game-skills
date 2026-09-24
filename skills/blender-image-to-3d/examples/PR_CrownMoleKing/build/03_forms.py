"""PR_CrownMoleKing forms (stylised prop: forms are built straight into LOW, no HIGH/bake step;
colour comes from flat materials baked to one 512 atlas in 05). Replaces the 02 blockout objects.
Masses and positions are the gated blockout values (build/02_blockout.py); new constants here are
secondary forms read from ref/front.png unless marked # inferred.
Run: python3 <skill>/scripts/run_bpy.py build/03_forms.py --master PR_CrownMoleKing_master.blend
"""
import bpy, bmesh, sys, math, os, random
from mathutils import Vector, Matrix, noise

PHASE = "03_forms"
TAG = "phase:" + PHASE
U = 0.34
SS = 0.88 / 0.95                   # band depth / width (blockout gate)
random.seed(7)

COLORS = {                          # sheet colours, stylised flat
    "M_Gold": ((1.0, 0.76, 0.18), 0.55, 0.35),   # stylised gold: part metallic so it stays yellow under dark envs
    "M_Velvet": ((0.40, 0.10, 0.52), 0.0, 0.90),
    "M_Bone": ((0.92, 0.84, 0.66), 0.0, 0.55),
    "M_Dirt": ((0.42, 0.27, 0.14), 0.0, 1.00),
    "M_Ruby": ((0.78, 0.02, 0.14), 0.0, 0.15),
    "M_GemAmber": ((0.85, 0.45, 0.05), 0.0, 0.15),
    "M_GemGrey": ((0.55, 0.55, 0.55), 0.0, 0.15),
    "M_GemPink": ((0.88, 0.55, 0.62), 0.0, 0.15),
    "M_GemPurple": ((0.55, 0.18, 0.85), 0.0, 0.15),
    "M_GemBlack": ((0.04, 0.04, 0.06), 0.0, 0.10),
    "M_GemOrange": ((0.97, 0.35, 0.04), 0.0, 0.15),
}


def master_path():
    a = sys.argv[sys.argv.index("--") + 1:]
    return a[a.index("--master") + 1]


def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    c, metal, rough = COLORS[name]
    c = tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)   # sRGB -> linear
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*c, 1)
    return m


def clear():
    for ob in [o for o in bpy.data.objects if o.get("owner") in (TAG, "phase:02_blockout")]:
        bpy.data.objects.remove(ob, do_unlink=True)


def link(name, bm, material, loc=(0, 0, 0), rot=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat(material))
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot is not None:
        ob.rotation_euler = rot
    ob["owner"] = TAG
    bpy.data.collections["LOW"].objects.link(ob)
    return ob


def ring_xy(ang_deg, r):
    a = math.radians(ang_deg)
    return Vector((r * math.sin(a), -r * math.cos(a) * SS, 0))


def lathe(profile, segs=40, sx=1.0, sy=SS, lobes=0, lobe_amp=0.0):
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        k = 1 + lobe_amp * math.cos(lobes * a) if lobes else 1
        rings.append([bm.verts.new((r * k * math.sin(a) * sx, -r * k * math.cos(a) * sy, z)) for r, z in profile])
    n = len(profile)
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % segs]
        for j in range(n - 1):
            bm.faces.new((r0[j], r1[j], r1[j + 1], r0[j + 1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sweep(path, radii, segs=8, flat=1.0, cap=True, ref=Vector((0, -1, 0))):
    """Tube along path points; radii per point; flat < 1 squashes the axis along `ref` (outward),
    which also fixes the ring frame so the tube never twists."""
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(ref)
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        nrm = side.cross(t).normalized()
        ring = []
        for s in range(segs):
            a = 2 * math.pi * s / segs
            off = side * math.cos(a) * radii[i] + nrm * math.sin(a) * radii[i] * flat
            ring.append(bm.verts.new(p + off))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segs):
            bm.faces.new((rings[i][s], rings[i][(s + 1) % segs], rings[i + 1][(s + 1) % segs], rings[i + 1][s]))
    if cap:
        bm.faces.new(list(reversed(rings[0])))
        if radii[-1] > 1e-5:
            bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def lump(radius, subdiv=2, amp=0.25, seed=0, squash=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))
    for v in bm.verts:
        d = noise.noise(v.co * (3.0 / radius) + off)
        v.co *= 1 + amp * d
        v.co.x *= squash[0]; v.co.y *= squash[1]; v.co.z *= squash[2]
    return bm


def ellipsoid(rx, ry, rz, segs=16, rings=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    bmesh.ops.scale(bm, vec=(rx, ry, rz), verts=bm.verts)
    return bm


def build():
    # BAND: rolled lower rim 0.02-0.12u, recessed body, raised upper rim 0.39-0.46u, inner wall
    prof = [(0.41, 0.46), (0.47, 0.465), (0.478, 0.45), (0.478, 0.405), (0.47, 0.39),
            (0.462, 0.375), (0.462, 0.145), (0.468, 0.13), (0.478, 0.115), (0.482, 0.07),
            (0.476, 0.025), (0.46, 0.0), (0.41, 0.0), (0.41, 0.46)]
    link("PR_CrownMoleKing_Band", lathe([(r * U, z * U) for r, z in prof], segs=40), "M_Gold")

    # VELVET: dome top 0.87u, widest 0.80u, soft lobes bulging between the 7 claws
    dome = []
    for i in range(9):
        t = i / 8
        ang = t * math.pi / 2
        dome.append((0.40 * U * math.cos(ang) + 1e-5, 0.46 * U + 0.41 * U * math.sin(ang)))
    dome.insert(0, (0.40 * U, 0.40 * U))
    link("PR_CrownMoleKing_Velvet", lathe(dome, segs=28, lobes=7, lobe_amp=0.04), "M_Velvet")

    # NUGGET: lumpy gold, 0.89-1.00u, width 0.15u, sits on the dome
    link("PR_CrownMoleKing_Nugget", lump(0.08 * U, 1, 0.35, 3, (1.1, 1.0, 1.1)), "M_Gold",
         loc=(0, 0, 0.905 * U))   # sunk into the dome top (0.87u) so no gap shows

    # CLAWS: gold knuckled finger (0.40-0.64u) + bone talon curling inward to 0.85-0.89u
    lean = {0: 5, 45: 13, 90: 6, 135: 20}            # gated in 02
    for ang in (0, 45, -45, 90, -90, 135, -135):
        out = ring_xy(ang, 1.0).normalized()
        base = ring_xy(ang, 0.455 * U) + Vector((0, 0, 0.40 * U))
        L = math.radians(lean[abs(ang)])
        tall = 1.0 if ang == 0 else 0.955
        pts, rad = [], []
        # finger: 5 points, knuckle bulges at 1/3 and 2/3
        for k in range(6):
            s = k / 5
            h = 0.24 * U * s                          # gold finger 0.40-0.64u, the talon carries the top
            p = base + out * (math.sin(L) * h) + Vector((0, 0, math.cos(L) * h))
            pts.append(p)
            bulge = 1.0 + (0.12 if k in (2, 4) else 0.0)
            rad.append(0.082 * U * (1 - 0.12 * s) * bulge)   # chunky fingers (front view width 0.13u)
        link(f"PR_CrownMoleKing_Claw{ang:+04d}_Finger", sweep(pts, rad, 10, flat=0.6, ref=out), "M_Gold")
        # talon: continues up and curls inward (the -20 deg tilt of 02 as a smooth arc)
        tpts, trad = [], []
        top = pts[-1] - Vector((0, 0, 0.02 * U))      # talon sheath overlaps the finger top
        tip_h = (0.89 * tall * U) - top.z
        for k in range(9):
            s = k / 8
            # horn curve: bows outward first, then hooks inward at the tip (front view crescents)
            bow = 0.035 * U * math.sin(math.pi * s) - 0.06 * U * s ** 2.2
            p = top + out * bow + Vector((0, 0, tip_h * s))
            tpts.append(p)
            trad.append(0.068 * U * (1 - s) ** 0.8 + 0.001)
        link(f"PR_CrownMoleKing_Claw{ang:+04d}_Talon", sweep(tpts, trad, 10, flat=0.7, ref=out), "M_Bone")

    # EMBLEM: raised medallion rim + inset face, tilted (02 gate), centred 0.27u
    em_loc = Vector((0, -(0.455 * U * SS + 0.05 * U), 0.27 * U))
    em_rot = Matrix.Rotation(math.radians(90 - 14), 4, 'X')
    med = [(0.0, 0.03), (0.15, 0.03), (0.165, 0.045), (0.185, 0.035), (0.188, -0.03), (0.0, -0.03)]
    bm = lathe([(r * U + 1e-5, z * U) for r, z in med], segs=32, sx=1, sy=1)
    link("PR_CrownMoleKing_Medallion", bm, "M_Gold", loc=em_loc, rot=em_rot.to_euler())

    def on_face(x, z, lift):                     # point on the medallion face (local x right, z up)
        # medallion local frame: x right, y up (after the 90 deg tilt), z out of the face
        return em_loc + em_rot.to_3x3() @ Vector((x, z, 0.03 * U + lift))
    # mole head: round head + pointed snout, upper half of the face (front view)
    head = on_face(0, 0.05 * U, 0.03 * U)
    link("PR_CrownMoleKing_MoleHead", ellipsoid(0.09 * U, 0.07 * U, 0.075 * U, 16, 8), "M_Gold", loc=head)
    snout = on_face(0.0, 0.02 * U, 0.08 * U)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.03 * U, radius2=0.004 * U, depth=0.07 * U)
    link("PR_CrownMoleKing_MoleSnout", bm, "M_Gold", loc=snout, rot=(math.radians(90 - 14 + 70), 0, 0))
    # paws gripping the ruby, lower half
    for sx in (-1, 1):
        paw = on_face(sx * 0.075 * U, -0.07 * U, 0.035 * U)
        link(f"PR_CrownMoleKing_MolePaw{'L' if sx < 0 else 'R'}", ellipsoid(0.055 * U, 0.03 * U, 0.04 * U, 12, 6),
             "M_Gold", loc=paw, rot=(0, 0, sx * math.radians(25)))
    # ruby: octagonal faceted gem between the paws
    ruby = on_face(0, -0.08 * U, 0.05 * U)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.055 * U, radius2=0.03 * U, depth=0.035 * U)
    link("PR_CrownMoleKing_Ruby", bm, "M_Ruby", loc=ruby, rot=(math.radians(90 - 14), 0, 0), smooth=False)

    # GEMS: cabochons in gold bezels at 0.22u (inferred order, one of each colour)
    for ang, m in ((45, "M_GemGrey"), (-45, "M_GemAmber"), (100, "M_GemPink"), (-100, "M_GemBlack"),
                   (155, "M_GemPurple"), (-155, "M_GemOrange")):
        n = ring_xy(ang, 1.0).normalized()
        p = ring_xy(ang, 0.465 * U) + Vector((0, 0, 0.22 * U))
        rot = Vector((0, 0, 1)).rotation_difference(n).to_euler()
        bez = [(0.0, 0.0), (0.06, 0.0), (0.062, 0.02), (0.05, 0.022), (0.0, 0.01)]
        link(f"PR_CrownMoleKing_Bezel{ang:+04d}", lathe([(r * U + 1e-5, z * U) for r, z in bez], 16, 1, 1),
             "M_Gold", loc=p, rot=rot)
        cab = [(0.047, 0.0), (0.045, 0.02), (0.03, 0.04), (0.0, 0.047)]
        link(f"PR_CrownMoleKing_Gem{ang:+04d}", lathe([(r * U + 1e-5, z * U) for r, z in cab], 16, 1, 1),
             m, loc=p + n * 0.012 * U, rot=rot, smooth=True)

    # DIRT: clumps on the upper rim between claws (front view: at about +-30 deg), plus one at back-left
    for i, ang in enumerate((32, -32, 150)):
        p = ring_xy(ang, 0.46 * U) + Vector((0, 0, 0.48 * U))
        link(f"PR_CrownMoleKing_Dirt{i}", lump(0.05 * U, 2, 0.45, 10 + i, (1.2, 1.0, 0.8)), "M_Dirt", loc=p)


def main():
    m = master_path()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(m))
    clear()
    build()
    obs = [o for o in bpy.data.objects if o.get("owner") == TAG]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs)
    print(f"[{PHASE}] objects {len(obs)}, tris {tris}")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(m))


main()
