"""PR_CrownMoleKing blockout. Units metres, Z up, front faces -Y, origin at ground centre.
u = subject height 0.34 m (brief SCALE). All ratios from asset-brief.md PROPORTIONS (front view
unless noted). Run: python3 <skill>/scripts/run_bpy.py build/02_blockout.py --master PR_CrownMoleKing_master.blend
"""
import bpy, bmesh, sys, math, os
from mathutils import Vector, Matrix

PHASE = "02_blockout"
TAG = "phase:" + PHASE
U = 0.34
SIDE_SCALE = 0.88 / 0.95          # band depth / width: side view 0.83-0.90u vs front 0.93-0.96u


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return a[a.index("--master") + 1]


def col(name):
    return bpy.data.collections[name]


def clear():
    for ob in [o for o in bpy.data.objects if o.get("owner") == TAG]:
        bpy.data.objects.remove(ob, do_unlink=True)


def link(name, bm, loc=(0, 0, 0), rot=None, coll="LOW"):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot is not None:
        ob.rotation_euler = rot
    ob["owner"] = TAG
    col(coll).objects.link(ob)
    return ob


def lathe(profile, segs=48):
    """profile: list of (r, z) in metres, closed loop, revolved around Z."""
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        ring = [bm.verts.new((r * math.sin(a), -r * math.cos(a) * SIDE_SCALE, z)) for r, z in profile]
        rings.append(ring)
    n = len(profile)
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % segs]
        for j in range(n):
            bm.faces.new((r0[j], r1[j], r1[(j + 1) % n], r0[(j + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def ellipsoid(rx, ry, rz, segs=24, rings=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    bmesh.ops.scale(bm, vec=(rx, ry, rz), verts=bm.verts)
    return bm


def cone(r1, r2, depth, segs=12):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=depth)
    bmesh.ops.translate(bm, vec=(0, 0, depth / 2), verts=bm.verts)   # base at z=0
    return bm


def box(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, sz / 2), verts=bm.verts)
    return bm


def ring_point(angle_deg, r):
    a = math.radians(angle_deg)
    return Vector((r * math.sin(a), -r * math.cos(a) * SIDE_SCALE, 0))


def build():
    R = 0.45 * U                              # band outer radius (dia 0.90u)
    # band: rolled lower rim 0.02-0.12u, body, raised upper rim 0.39-0.46u; inner wall r 0.41u
    prof = [(0.41 * U, 0.0), (0.455 * U, 0.0), (0.47 * U, 0.05 * U), (0.46 * U, 0.11 * U),
            (0.46 * U, 0.13 * U), (0.475 * U, 0.37 * U), (0.475 * U, 0.40 * U),
            (0.47 * U, 0.45 * U), (0.41 * U, 0.46 * U)]
    link("PR_CrownMoleKing_Band", lathe(prof))

    # velvet dome: top 0.87u, widest 0.80u, centred 0.46u
    link("PR_CrownMoleKing_Velvet", ellipsoid(0.40 * U, 0.40 * U * SIDE_SCALE, 0.41 * U), loc=(0, 0, 0.46 * U))

    # nugget 0.89-1.00u, width 0.15u
    link("PR_CrownMoleKing_Nugget", ellipsoid(0.075 * U, 0.07 * U, 0.06 * U, 10, 6), loc=(0, 0, 0.94 * U))

    # 7 claws; front one tallest (tip 0.89u), others 0.85u; flare to r 0.53u at 0.64u (front width 1.06u)
    for ang in (0, 45, -45, 90, -90, 135, -135):
        tall = 1.0 if ang == 0 else 0.955
        base = ring_point(ang, 0.455 * U)
        base.z = 0.40 * U
        out = ring_point(ang, 1.0).normalized()
        yaw = math.atan2(out.x, -out.y)                 # rotate local -Y to the outward direction
        # outward lean per claw: the side claws set the front width, the front/back claws the side depth
        lean = math.radians({0: 5, 45: 13, 90: 6, 135: 20}[abs(ang)])
        seg_h = 0.30 * U
        gb = link(f"PR_CrownMoleKing_Claw{ang:+04d}_Base", box(0.13 * U, 0.06 * U, seg_h),
                  loc=base, rot=(lean, 0, yaw))
        # tip: from the top of the gold base, curls back inward
        tip_root = base + Matrix.Rotation(yaw, 3, 'Z') @ (Matrix.Rotation(lean, 3, 'X') @ Vector((0, 0, seg_h)))
        tip_len = max(0.18 * U, (0.89 * tall * U) - tip_root.z)
        link(f"PR_CrownMoleKing_Claw{ang:+04d}_Tip", cone(0.065 * U, 0.004 * U, tip_len),
             loc=tip_root, rot=(math.radians(-20), 0, yaw))   # bone tip curls back inward (front view crescents)

    # emblem medallion: dia 0.37u centred 0.29u; side view shows it 0.10u proud of the band front
    em = bmesh.new()
    bmesh.ops.create_cone(em, cap_ends=True, segments=32, radius1=0.185 * U, radius2=0.185 * U, depth=0.08 * U)
    link("PR_CrownMoleKing_Emblem", em, loc=(0, -(R * SIDE_SCALE + 0.05 * U), 0.27 * U),
         rot=(math.radians(90 - 14), 0, 0))   # tilted: bottom stands out, top leans on the rim (side view)

    # 6 gems on the band at 0.22u (inferred spacing around the emblem)
    for ang in (45, -45, 100, -100, 155, -155):
        p = ring_point(ang, 0.455 * U)
        p.z = 0.22 * U
        link(f"PR_CrownMoleKing_Gem{ang:+04d}", ellipsoid(0.045 * U, 0.045 * U, 0.045 * U, 12, 6), loc=p)


def main():
    master = args()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(master))
    clear()
    build()
    tris = 0
    for ob in [o for o in bpy.data.objects if o.get("owner") == TAG]:
        tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"[{PHASE}] objects {len([o for o in bpy.data.objects if o.get('owner') == TAG])}, tris {tris}")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(master))


main()
