#!/usr/bin/env python3
"""Check a delivered GLB against a platform profile from references/platform-targets.md.

Plain Python 3, no dependencies. Reads the GLB directly (not through Blender), so it sees what the
engine will receive. Exit 1 on any FAIL.

    python3 scripts/check_platform.py exports/roblox-prop/PR_Chest.glb --profile roblox-prop
    python3 scripts/check_platform.py exports/crazygames/CH_Hero.glb --profile crazygames --json out.json

Profiles: roblox-prop roblox-rig roblox-accessory roblox-layered roblox-body spawn crazygames
astrocade generic. FBX deliveries: export a GLB copy with the same settings and check that.
"""
import argparse
import json
import struct
import sys

R15 = ["Root", "HumanoidRootNode", "LowerTorso", "UpperTorso", "Head",
       "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand",
       "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"]
BODY_GROUPS = {
    "head": (["Head"], 4000),
    "torso": (["UpperTorso", "LowerTorso"], 1750),
    "left_arm": (["LeftUpperArm", "LeftLowerArm", "LeftHand"], 1248),
    "right_arm": (["RightUpperArm", "RightLowerArm", "RightHand"], 1248),
    "left_leg": (["LeftUpperLeg", "LeftLowerLeg", "LeftFoot"], 1248),
    "right_leg": (["RightUpperLeg", "RightLowerLeg", "RightFoot"], 1248),
}

# per_mesh / total: triangle limits (hard = FAIL, soft = WARN); tex: max texture edge;
# bytes: file size (soft, hard); compressed: warn when meshopt/draco missing
PROFILES = {
    "roblox-prop": dict(per_mesh=(20000, None), tex=(1024, 1024), skin="forbid"),
    "roblox-rig": dict(per_mesh=(20000, None), tex=(1024, 1024), skin="require", max_joints_sets=1),
    "roblox-accessory": dict(total=(4000, None), tex=(2048, 2048), skin="forbid"),
    "roblox-layered": dict(total=(4000, None), tex=(2048, 2048), skin="require", cages=True,
                           max_joints_sets=1, r15=True),
    "roblox-body": dict(total=(10742, None), tex=(2048, 2048), skin="require", body=True,
                        max_joints_sets=1, r15=True),
    "spawn": dict(total=(None, 30000), tex=(None, 1024), bytes=(5_000_000, None)),
    "crazygames": dict(total=(None, 50000), tex=(2048, 2048), bytes=(4_000_000, 15_000_000),
                       compressed=True),
    "astrocade": dict(total=(None, 15000), tex=(None, 1024), bytes=(1_500_000, 2_000_000),
                      compressed=True, no_ktx2=True),
    "generic": dict(),
}


def read_glb(path):
    data = open(path, "rb").read()
    magic, version, length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        raise SystemExit(f"FAIL not a GLB: {path}")
    off, js, binchunk = 12, None, b""
    while off < len(data):
        clen, ctype = struct.unpack("<II", data[off:off + 8])
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            binchunk = chunk
        off += 8 + clen
    return data, version, length, js, binchunk


def image_size(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24]), "png"
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return (w, h), "jpeg"
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        if b[12:16] == b"VP8X":
            w = int.from_bytes(b[24:27], "little") + 1
            h = int.from_bytes(b[27:30], "little") + 1
            return (w, h), "webp"
        if b[12:16] == b"VP8 ":
            w, h = struct.unpack("<HH", b[26:30])
            return (w & 0x3FFF, h & 0x3FFF), "webp"
        if b[12:16] == b"VP8L":
            bits = int.from_bytes(b[21:25], "little")
            return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1), "webp"
    if b[:12] == b"\xabKTX 20\xbb\r\n\x1a\n":
        w, h = struct.unpack("<II", b[20:28])
        return (w, h), "ktx2"
    return (0, 0), "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("glb")
    ap.add_argument("--profile", required=True, choices=sorted(PROFILES))
    ap.add_argument("--json", help="write the report here")
    a = ap.parse_args()
    prof = PROFILES[a.profile]
    data, version, length, js, binc = read_glb(a.glb)
    fails, warns, info = [], [], {}

    def limit(value, pair, label):
        hard, soft = pair
        if hard is not None and value > hard:
            fails.append(f"{label} {value} > {hard}")
        elif soft is not None and value > soft:
            warns.append(f"{label} {value} > {soft} (soft)")

    if version != 2 or length != len(data):
        fails.append(f"header version {version} length {length} vs file {len(data)}")
    acc = js.get("accessors", [])
    exts = set(js.get("extensionsUsed", []))
    nodes = js.get("nodes", [])
    mesh_tris = {}
    joints_sets = 0
    for mi, mesh in enumerate(js.get("meshes", [])):
        name = mesh.get("name") or f"mesh{mi}"
        t = 0
        for prim in mesh.get("primitives", []):
            if prim.get("mode", 4) != 4:
                continue
            if "indices" in prim:
                t += acc[prim["indices"]]["count"] // 3
            else:
                t += acc[prim["attributes"]["POSITION"]]["count"] // 3
            js_n = sum(1 for k in prim["attributes"] if k.startswith("JOINTS_"))
            joints_sets = max(joints_sets, js_n)
        mesh_tris[name] = t
    # node names carry the object names Blender exported; map mesh -> node name when present
    node_mesh = {}
    for n in nodes:
        if "mesh" in n:
            mname = js["meshes"][n["mesh"]].get("name") or f"mesh{n['mesh']}"
            node_mesh[n.get("name", mname)] = mesh_tris.get(mname, 0)
    cages = {k: v for k, v in node_mesh.items() if k.endswith("_InnerCage") or k.endswith("_OuterCage")}
    render = {k: v for k, v in node_mesh.items() if k not in cages and not k.startswith("COL_")}
    total = sum(render.values())
    info["meshes"] = node_mesh
    info["render_tris_total"] = total

    if "per_mesh" in prof:
        for k, v in render.items():
            limit(v, prof["per_mesh"], f"tris {k}")
    if "total" in prof:
        limit(total, prof["total"], "tris total")

    skins = js.get("skins", [])
    joint_names = sorted({nodes[j].get("name", "") for s in skins for j in s["joints"]})
    info["joints"] = joint_names
    if prof.get("skin") == "require" and not skins:
        fails.append("no skin: profile needs a skinned mesh")
    if prof.get("skin") == "forbid" and skins:
        fails.append("skinned mesh in a static profile")
    mjs = prof.get("max_joints_sets")
    if mjs and joints_sets > mjs:
        fails.append(f"{joints_sets} JOINTS sets: more than 4 influences per vertex")
    if prof.get("r15") and skins:
        missing = [b for b in R15 if b not in joint_names]
        if missing:
            fails.append("R15 bones missing: " + ", ".join(missing))
    if prof.get("cages"):
        if not any(k.endswith("_InnerCage") for k in cages) or not any(k.endswith("_OuterCage") for k in cages):
            fails.append("layered clothing needs <Name>_InnerCage and <Name>_OuterCage meshes")
    if prof.get("body"):
        for g, (parts, cap) in BODY_GROUPS.items():
            t = sum(v for k, v in render.items() for p in parts if k in (p, p + "_Geo"))
            found = [p for p in parts if p in render or p + "_Geo" in render]
            if len(found) != len(parts):
                fails.append(f"body {g}: missing parts {sorted(set(parts) - set(found))} (name them <Part>_Geo)")
            limit(t, (cap, None), f"tris body {g}")

    imgs = []
    views = js.get("bufferViews", [])
    for ii, img in enumerate(js.get("images", [])):
        if "bufferView" not in img:
            fails.append(f"image {ii} not embedded ({img.get('uri', '?')})")
            continue
        bv = views[img["bufferView"]]
        b = binc[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
        (w, h), kind = image_size(b)
        imgs.append({"name": img.get("name", str(ii)), "w": w, "h": h, "kind": kind, "bytes": bv["byteLength"]})
        if "tex" in prof:
            limit(max(w, h), prof["tex"], f"texture {img.get('name', ii)}")
        if kind == "ktx2" and prof.get("no_ktx2"):
            warns.append(f"KTX2 texture {img.get('name', ii)}: unproven on this runtime, prefer WebP")
    info["images"] = imgs

    if "bytes" in prof:
        hard_soft = prof["bytes"]
        limit(len(data), (hard_soft[1], hard_soft[0]), "file bytes")
    if prof.get("compressed") and not (exts & {"EXT_meshopt_compression", "KHR_draco_mesh_compression"}):
        warns.append("geometry not compressed: run scripts/optimize_web.sh")
    if a.profile.startswith("roblox") and exts & {"EXT_meshopt_compression", "KHR_draco_mesh_compression", "KHR_texture_basisu"}:
        fails.append("compressed extensions in a Roblox export: Roblox's importer needs plain GLB/FBX")
    info["extensions"] = sorted(exts)
    info["bytes"] = len(data)

    for w in warns:
        print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print(f"{a.profile}: tris {total}, meshes {len(render)}, cages {len(cages)}, joints {len(joint_names)}, "
          f"images {len(imgs)}, bytes {len(data)}, WARN {len(warns)}, FAIL {len(fails)}")
    if a.json:
        json.dump({"profile": a.profile, "fails": fails, "warns": warns, **info}, open(a.json, "w"), indent=2)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
