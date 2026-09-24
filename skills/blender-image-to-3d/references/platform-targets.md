# Platform targets

Read in Phase 0 (to pick the profile and fill TARGET), again before Phase 4 (budgets), Phase 6
(rig family and bone names) and Phase 9 (export, compression, upload). Each profile overrides
the generic budget table in `delivery-and-acceptance.md` where the two disagree; the platform
limit is a hard wall, the generic tier is only a starting point.

Facts below were verified on the web on 2026-09-24. Platform rules drift: when a check fails
in a way that contradicts this file, or before any money is spent (Roblox fees, advances),
re-verify against the linked source and update this file.

## Contents

1. Profile table (pick one)
2. Roblox in-game (`roblox-prop`, `roblox-rig`)
3. Roblox UGC avatar items (`roblox-accessory`, `roblox-layered`, `roblox-body`)
4. Roblox Creator Store (selling kits to developers)
5. Spawn (`spawn`)
6. CrazyGames (`crazygames`)
7. Astrocade (`astrocade`)
8. Generic engines (Unity, Unreal, Godot, three.js) and asset stores
9. Bone maps (R15, Mixamo)
10. One source, many exports

## 1. Profile table

| Profile | Format | Tri budget (LOD0) | Max texture | Rig | Compression | Check |
|---|---|---|---|---|---|---|
| `roblox-prop` | FBX or GLB | 20,000 per mesh (hard); aim 500 to 5,000 | 1024 | none | none (Roblox recompresses) | `check_platform.py --profile roblox-prop` |
| `roblox-rig` | FBX or GLB | 20,000 per mesh | 1024 | custom or R15, 4 influences | none | `roblox-rig` |
| `roblox-accessory` | FBX or GLB | 4,000 total (hard) | 2048 | none | none | `roblox-accessory` |
| `roblox-layered` | FBX or GLB | 4,000 render mesh (hard) + cages | 2048 | skinned to R15 | none | `roblox-layered` |
| `roblox-body` | FBX or GLB | 10,742 total; per part below | 2048 | R15 exact names | none | `roblox-body` |
| `spawn` | GLB, embedded textures | aim ≤ 15k hero, ≤ 3k prop | 1024 | Mixamo-style names for IK | optional (CDN compresses) | `spawn` |
| `crazygames` | GLB | aim ≤ 20k hero, ≤ 3k prop; scene < 100k verts on screen | 2048 hero, 1024 props | any | meshopt + KTX2 or WebP | `crazygames` |
| `astrocade` | GLB | aim ≤ 8k hero, ≤ 2k prop | 1024 | any | meshopt + WebP | `astrocade` |
| `unity` / `unreal` / `godot` / `threejs` | per engine | generic tier table | generic | generic DEF- rig | per engine | `generic` |

A request that names several platforms gets one master and one export per profile (section 10).
Budgets are the smallest number that keeps the silhouette at the game camera; do not spend a
budget just because it exists.

## 2. Roblox in-game assets

Sources: https://create.roblox.com/docs/art/modeling/specifications,
https://create.roblox.com/docs/art/blender, https://create.roblox.com/docs/art/modeling/surface-appearance

**Units.** 1 stud = 0.28 m. Keep the master in metres (Phase 1 rule) and convert at the boundary:
import in Studio with Scale Unit = Metre, or set the export scale so a 1.85 m character arrives
as about 6.6 studs. A default Roblox avatar is about 5 to 5.5 studs (1.4 to 1.55 m); design
props against that, not against a 1.85 m human, or doors and chests will look oversized next to
players. Record the chosen factor in the manifest.

**Axes.** Roblox's Blender guide: FBX export Forward Z, Up Y, Apply Scalings "FBX Unit Scale";
glTF export scale 1, Forward Z, Up Y; Studio import World Forward Front, World Up Top. The
skill's FBX exporter uses -Z forward, so either pass World Forward = Back at import or flip the
axis in the export; decide once per project, write it in the manifest, and verify with the
round trip that the asset faces the way the game expects.

**Geometry.** 20,000 triangles per MeshPart (hard). Watertight where possible, no n-gons, UVs in
0..1, no zero-thickness surfaces (Roblox collision and shading misbehave on them). Split big
assets into several MeshParts along material or gameplay lines (a chest body and a lid that
opens) rather than hitting the cap.

**Pivots.** The Roblox importer does not reliably keep Blender object origins as the MeshPart
pivot. For anything that rotates (lids, doors, blades), also export the pivot as an empty named
`PIVOT_<part>` and have the Luau code compute or set the pivot (PivotOffset or a hinge Attachment)
from it or from the part bounds; say so in the handover.

**Collision.** Roblox builds collision from the render mesh (CollisionFidelity Box, Hull,
Default, PreciseConvexDecomposition). Keep COL_ proxies in the master for web targets, but for
Roblox note in the handover which CollisionFidelity each part needs; Box or Hull for pickups and
props, Precise only where players walk inside.

**Textures.** Plan on 1024 for in-game MeshParts (the specs page says 1024; the texture page
claims up to 4096; 2048 was raised only for avatar items in Feb 2026). SurfaceAppearance maps:
ColorMap (alpha allowed), NormalMap (OpenGL, +Y, matches this skill's default), RoughnessMap,
MetalnessMap, each a separate single-channel greyscale image. Do not ship packed ORM for Roblox;
export the unpacked masters. Emissive: EmissiveMaskContent plus EmissiveStrength/Tint in Studio.
Size guide: 5x5 studs 256 px, 10x10 studs 512 px, 20x20 studs 1024 px.

**Stylised Roblox look.** Most successful Roblox games are bright, chunky, low texel detail.
Prefer flat colour plus a small palette atlas, bold bevels and readable silhouettes over
photoreal PBR, unless the game's style lock says otherwise. Emissive + PointLight in Studio sells
gems and loot better than texture detail.

**Rigs (roblox-rig).** Custom rigs for creatures, traps and doors are allowed: max 4 influences,
bones at scale 1 and rotation 0 in rest, root bone at origin with no vertex weights. Animations:
the Animation Clip Editor importer (GA 31 Mar 2026) takes FBX/glTF with several clips; each clip
is still uploaded as its own Animation asset. Rigid mechanisms (a swinging blade, a trapdoor) are
often better as separate MeshParts driven by HingeConstraint or TweenService in Luau than as a
skinned rig; say which in the handover.

**Upload.** Official Roblox Blender plugin (Open Cloud, OAuth): each selected object or
collection uploads as a Package; in Studio: Toolbox > Inventory > My Packages. Or Studio 3D
Importer (Avatar tab > Import 3D), which shows warnings for tri count, UV and skinning problems.
When a Roblox Studio MCP is connected, the asset can be placed and checked from code after
upload (`insert_model` by asset id), but uploading itself is manual or plugin-driven.

## 3. Roblox UGC avatar items

Sources: https://create.roblox.com/docs/marketplace/marketplace-policy,
https://create.roblox.com/docs/marketplace/marketplace-fees-and-commissions,
https://create.roblox.com/docs/avatar/rigid-accessories/specifications,
https://create.roblox.com/docs/avatar/layered-accessories/specifications,
https://create.roblox.com/docs/avatar/character-bodies/specifications

### Money and eligibility (tell the user before building anything for sale)
- Seller needs government ID verification, 2-step verification and an active Roblox Plus (or
  legacy Premium) subscription; items go off sale if it lapses.
- Upload fee 80 R$ per 3D item (500 R$ with an emissive mask), not refunded on rejection.
- Publishing advance on first publish (non-Limited): Hat/Face/Head/Emote 1,500 R$, Hair and
  Neck/Shoulder/Front/Back/Waist 1,000 R$, layered clothing 600 R$, Body 2,500 R$. It is repaid
  only out of Roblox's share of later sales; unsold items never repay it.
- Creator share 30% at the price floor, 50% at 2x floor, 70% cap at 6x. Sold inside a game:
  creator 30% + game owner 40%, so an item sold inside the user's own game earns 70%.
- DevEx $0.0038 per earned Robux, minimum 30,000 R$. Non-US sellers need a W-8BEN in Creator Hub
  (Taxes) from Nov 2026 or 24% backup withholding applies.
- Aug 2026: automated duplicate detection removes items too similar to existing ones, with no fee
  refund. Generic shapes (plain crowns, basic swords, stock wings) are exposed; give every item a
  distinctive silhouette feature.

### Policy gates (check in Phase 0, before modelling)
- Original work only. No franchise characters, logos, brand names, real people, or "inspired"
  copies of other items. Build new IP: borrow a genre, never names, marks or signature designs.
- Bodies may not include clothing, armour, accessories, tattoos or makeup: those ship as separate
  items. Human-like bodies with a chest need a fully opaque upper covering over the whole chest
  area and a lower covering over hips, groin and buttocks, in a colour different from the skin,
  not lingerie-like. Exaggerated proportions that make the breasts, pelvis or buttocks the focal
  point are rejected, as is heavy shading that highlights them.
- No gore, realistic weapons aimed at violence, drugs, political or religious symbols, items that
  obscure the avatar or UI. Fantasy weapons as back accessories exist, but keep them non-gory.
- AI-generated content is not banned on the Marketplace, but the seller is responsible for it, and
  purely AI output may not be protectable. Human-directed modelling (this skill's scripts) is the
  safer position; still record in the manifest which parts came from any generator.
- When a reference image would fail these gates (for example an exaggerated armoured female body
  sold as one bundle), say so in the brief and propose the legal split: a heroic, non-sexualised
  body plus armour pieces as separate accessories or layered clothing.

### roblox-accessory (rigid)
- 4,000 triangles, textures up to 2048, one mesh, no skinning.
- Must fit the category bounding box for its attachment (Hat, Hair, Face, Neck, Shoulder, Front,
  Back, Waist) at Classic/Normal/Slender scales; check the spec table for the current box.
- Build against the Roblox mannequin at real Roblox scale; place the accessory's attachment point
  (Hat_Att, BackAttachment etc.) as a SOCKET_ in the master and export it as the matching
  `<Name>Attachment`. Fit is judged in Studio's Accessory Fitting Tool before upload.

### roblox-layered (clothing, shoes, jackets)
- 4,000 triangles for the render mesh, textures up to 2048.
- Needs `<Name>_InnerCage` and `<Name>_OuterCage` meshes built from Roblox's official cage
  templates (download from the layered clothing docs). Deform the template; never delete, add or
  reorder cage vertices or change cage UVs, or validation fails.
- Skinned to the R15 bone names (section 9), 4 influences.
- This is the hardest Roblox category. Do one garment end to end through Studio's validation
  before building a set.

### roblox-body
- 15 meshes named `<Part>_Geo` (Head, UpperTorso, LowerTorso, Left/RightUpperArm, LowerArm, Hand,
  Left/RightUpperLeg, LowerLeg, Foot), grouped into 6 assets.
- Triangles: Head 4,000; UpperTorso + LowerTorso 1,750; each arm (3 parts) 1,248; each leg
  (3 parts) 1,248; total 10,742.
- R15 skeleton with exact names (section 9); Advanced R15 allows up to 37 extra bones. Rest pose
  I, A or T. Root and LowerTorso at origin.
- Dynamic head: caged, 1 mouth and 1 to 2 eye regions, at least the 17 required FACS poses.
- Outer cages required; `_Att` attachment meshes (Root_Att, Hat_Att, ...).
- Shortcut: Studio's Avatar Setup (auto-setup) rigs, skins, cages, partitions and generates FACS
  from a single watertight humanoid mesh in A or T pose, facing -Z, symmetrical, with a distinct
  neck, separate eyes, teeth and tongue, no accessories, at most 10,742 tris, at least one texture.
  For bodies, deliver that input mesh from this skill (Phases 0 to 5), then let Avatar Setup do
  Phase 6, then export its result back to Blender only for fixes.

## 4. Roblox Creator Store (models sold to developers)

- Models $2.99 to $49.99, paid in USD through Stripe, seller keeps net proceeds (tax and payment
  fees deducted), 30-day escrow. Needs 18+, ID verification, 2-step verification.
- Sell kits, not singles: a themed set (dungeon traps, loot chests, modular walls) with scripts or
  constraints already wired, a clear thumbnail and a readme. Buyers are developers, so clean
  naming, pivots, CollisionFidelity notes and a working demo place matter more than detail.
- Same build profile as `roblox-prop` / `roblox-rig`.
- Source: https://create.roblox.com/docs/production/creator-store

## 5. Spawn

Source: https://www.spawn.co/.well-known/agent-skills/uploaded-models/skill.md (read it live
before the first upload in a session; it changes with engine versions).

- GLB with embedded textures. No public numeric caps; the platform flags models as too heavy for
  phones and auto-LODs large worlds. Use the budgets in the table.
- The engine normalises size: in-game metres come from `layout.maxExtents`, `scale` multiplies.
  Still keep true metres in the master so sets stay consistent.
- Engine faces -Z, +Y up. Files uploaded by hand arrive as built; a Blender export usually fronts
  +Z in glTF space, so set `model.forward: "+z"` in the world YAML or rotate the export.
- Name materials semantically (`body_paint`, `trim_gold`, `glass`): Spawn can repaint by glTF
  material name, which gives colour variants for free.
- Any snake_case node name works as a socket; name SOCKET_ nodes accordingly on the Spawn copy
  (`socket_hand_r`) or record the mapping.
- Embedded clips play by name (case-insensitive, `Armature|` prefixes tolerated). Humanoid rigs
  with Mixamo-style names get IK and foot grounding; custom rigs play clips without IK. Use the
  Mixamo map in section 9 for any humanoid headed to Spawn.
- Skinned garments attach with `attachment: { skin: true }` using the body's bone names, so
  garments must share the body's exact skeleton.
- Upload: `PUT /api/sdk/v1/<worldId>/assets/value.<sha256>.<ext>` with `Content-Type:
  model/gltf-binary`, then reference the returned `/cdn/value.<sha>.glb`. Binary files inside a
  git push are refused. The `spawn-build` skill owns the world repo; this skill hands it the GLB
  and the socket/clip/material names.

## 6. CrazyGames

Source: https://docs.crazygames.com/requirements/technical/

- Initial download (until `gameplayStart`) 50 MB hard, 20 MB or less to be eligible for the mobile
  homepage. Total 250 MB, 1,500 files. Treat 20 MB as the real limit and give each asset a byte
  budget in the brief (hero character ~2 to 4 MB, prop 50 to 300 KB after compression).
- Three.js mobile budgets: under about 100 draw calls and 100k vertices on screen, textures at
  most 2048, 3 or fewer dynamic lights, pixel ratio capped at 2.
- One material per asset where possible (draw calls), shared atlases across a set, instancing for
  repeats. Merging meshes helps static props; never merge rigged or socketed assets.
- Compression is part of Phase 9 (`scripts/optimize_web.sh`): meshopt geometry, KTX2 (ETC1S for
  colour, UASTC for normal/ORM) or WebP textures. The game's loader needs `MeshoptDecoder` and, for
  KTX2, `KTX2Loader` with the basis transcoder shipped inside the bundle (no external CDN: the
  CrazyGames packager rejects external URLs).
- The `game-foundation` skill's asset convention is `worlds/<slug>/output/<object-id>/<id>.glb`
  or its own `assets/` folder; check the game's working file first. Lazy-load anything not needed
  for the first level after `gameplayStart`.

## 7. Astrocade

- Games are single pasted HTML files running three.js r128. Custom GLB hosting is not documented;
  before a real asset, test one small GLB in a paste build (inline base64 data URI or an allowed
  external URL) and record what worked in this file.
- Keep each GLB under about 1.5 MB, 2 MB hard. Use meshopt + WebP (r128 supports
  EXT_meshopt_compression via `setMeshoptDecoder` and EXT_texture_webp); avoid KTX2 on r128
  unless the transcoder version is proven to match.
- Mobile 9:16 at small on-screen sizes: silhouettes and flat colour beat texture detail. Aim for
  1 material and 512 to 1024 px per asset.
- The `astrocade-3d-build` skill owns the loader code; hand it the file and the node names.

## 8. Generic engines and asset stores

- Unity: FBX or GLB, the defaults in `delivery-and-acceptance.md`. Unity expects DirectX normal
  maps only when told; the skill ships OpenGL, so tick "flip green" or document it.
- Unreal: FBX, DirectX normals (flip green), Nanite optional for static meshes.
- Godot, three.js: GLB, OpenGL normals as shipped.
- Selling outside Roblox: Fab takes 12% and requires the "Created with AI" label for AI-assisted
  content; itch.io requires the Generative AI tag; Unity Asset Store requires disclosure; TurboSquid
  bans AI-generated content. Buyers largely ignore raw AI meshes, so only clean, documented, themed
  kits are worth listing.

## 9. Bone maps

The skill's own humanoid skeleton (DEF- names) stays the master. Target skeletons are produced by
a mapping, never by renaming the master (working rule). For Roblox bodies the R15 hierarchy has
fewer bones than the DEF- family, so the cleaner route is either to build the Roblox body with the
R15 family from the start in Phase 6 or to let Avatar Setup rig it.

R15 (exact names, hierarchy):
```text
Root
  HumanoidRootNode
    LowerTorso
      UpperTorso
        Head
        LeftUpperArm > LeftLowerArm > LeftHand
        RightUpperArm > RightLowerArm > RightHand
      LeftUpperLeg > LeftLowerLeg > LeftFoot
      RightUpperLeg > RightLowerLeg > RightFoot
```

DEF- to R15 (weights of unmapped bones merge into the parent listed):
```text
DEF-pelvis        LowerTorso
DEF-spine_01      LowerTorso (merge)
DEF-spine_02      UpperTorso
DEF-chest         UpperTorso (merge)
DEF-neck          Head (merge)
DEF-head          Head
DEF-clavicle.L    UpperTorso (merge)
DEF-upper_arm.L   LeftUpperArm
DEF-forearm.L     LeftLowerArm
DEF-hand.L        LeftHand (fingers merge here)
DEF-thigh.L       LeftUpperLeg
DEF-shin.L        LeftLowerLeg
DEF-foot.L        LeftFoot (toe merges here)
.R mirrors to Right*
```

DEF- to Mixamo (Spawn IK, most web retargeting):
```text
DEF-pelvis mixamorig:Hips      DEF-spine_01 mixamorig:Spine   DEF-spine_02 mixamorig:Spine1
DEF-chest mixamorig:Spine2     DEF-neck mixamorig:Neck        DEF-head mixamorig:Head
DEF-clavicle.L mixamorig:LeftShoulder   DEF-upper_arm.L mixamorig:LeftArm
DEF-forearm.L mixamorig:LeftForeArm     DEF-hand.L mixamorig:LeftHand
DEF-thigh.L mixamorig:LeftUpLeg         DEF-shin.L mixamorig:LeftLeg
DEF-foot.L mixamorig:LeftFoot           DEF-toe.L mixamorig:LeftToeBase
.R mirrors to Right*; fingers: mixamorig:LeftHandThumb1..3, Index1..3, Middle1..3, Ring1..3, Pinky1..3
```

Apply a map on a delivery copy: duplicate RIG_DEF and LOW into an export scene, rename bones and
matching vertex groups together, merge vertex groups for "(merge)" rows, then export. Record the
map used in the manifest.

## 10. One source, many exports

- One master per asset at 1 m units; profiles differ only in the export copy.
- Budgets: build LOD0 for the most generous profile the asset is headed to, then produce each
  platform's LOD0 by `lod_copy` down to that profile's budget. Roblox and Astrocade usually take
  what the generic tier calls LOD1 or LOD2.
- Textures: bake once at the largest needed size (2048), downscale per profile at export.
- Folder layout: `exports/<profile>/<Name>.<ext>` plus that profile's `asset-manifest.json`.
- Run `check_platform.py` per profile; a profile passes only on exit 0.
