---
name: blender-image-to-3d
description: Build a game-ready 3D asset in Blender from reference images or from a description, for characters, creatures, architecture, vehicles, props, weapons and environment pieces, through gated phases measured against the reference. Use whenever the user wants a 3D model, prop, weapon, character or game asset made (modelled, textured, rigged, animated or exported), even when Blender is not named and even with no image yet: the skill writes the reference sheet prompt for the user to generate first. Covers every platform target: Roblox (in-game MeshParts, UGC accessories, layered clothing, avatar bodies, Creator Store kits), Spawn, CrazyGames, Astrocade, Unity, Unreal, Godot, three.js, and one asset exported to several. Triggers include "make a prop for my game", "3D model of", "reference sheet", "turnaround", "UGC item", "sell on the Roblox marketplace", "GLB for my game". Ships bpy scripts for calibration, review renders, silhouette gates, validation, baking, export, reimport, platform checks and web compression.
license: MIT
---

# Blender image to 3D

Turn one or more reference images into a delivered game asset by moving through gated phases.
Every gate is passed with rendered evidence compared to the reference from the same camera and
at gameplay pixel size, never by looking at the viewport and deciding it seems fine. Most wasted
work in this pipeline is detail added on top of wrong proportions, so nothing gets detail until
its silhouette passes.

"Perfect" here has a definition: the acceptance checklist in
`references/delivery-and-acceptance.md` passes, the compare sheets show no measured deviation
above the phase tolerance, and every dimension or side that the reference did not show is listed
as inferred. Say so when a single image forces inference; do not present a guessed back as fact.

## Runtime

- Bundle check first. This file needs its `scripts/`, `references/` and `assets/` folders. If they
  are not next to this SKILL.md (the skill was installed as instructions only), fetch the bundle
  and use that folder as the skill directory for every path below:
  `git clone --depth 1 https://github.com/dragoscocos-hash/blender-game-skills.git /tmp/bgs &&
  export SKILL=/tmp/bgs/skills/blender-image-to-3d`. The fork adds the platform profiles, the
  platform checker and the web optimizer to the upstream MIT skill by Majid Manzarpour.

- Where to run: the cloud workspace, by default, always. Install the module there
  (`python3 -m pip install bpy`) and run every script headless through `scripts/run_bpy.py`, even
  when the session is linked to the user's computer and a Blender MCP or a local Blender app is
  available. The user chose this: nothing to keep open on their side, no frozen viewport during
  renders, and every build is reproducible from the scripts. Use the user's local Blender only
  when they ask for it in this session (to watch the build live or tweak by hand); a linked
  computer or a connected Blender MCP is not that request. The cloud workspace is temporary, so
  at the end of every asset session send the user the master and baked `.blend` files, the
  `build/` scripts, the brief and the exports (and save them to the project or their computer when
  one is linked); an asset that only lives in the workspace is lost when the session ends.
- Blender 4.2 or newer (used through 5.2), run headless: `blender --background --python <script> -- <args>`.
  No Blender app (a cloud container): `python3 -m pip install bpy` (5.0.x wheel for Python 3.11)
  and run every script through `python3 scripts/run_bpy.py <script> <args>`; wherever this file
  says `$BLENDER_BIN --background --python X --`, read `python3 scripts/run_bpy.py X`. Workbench
  may lack a GL context there; pass `--engine cycles` to review_render.py (CPU, about 10 s per
  view at review size).
  Blender 5.x changed several APIs these builds touch; `references/blender-5-notes.md` lists them
  with runtime, baking and review lessons.
  Resolve the binary once: `$BLENDER_BIN`, then `blender` on PATH, then
  `/Applications/Blender.app/Contents/MacOS/Blender`. Workbench renders need no GPU on macOS or
  Windows; on a headless Linux box without a GPU, pass `--engine cycles` to review_render.py.
- A live Blender session through an MCP server (execute-Python tool) is optional, used only when
  the user asks for local work (see "Where to run"), and useful for inspection. Even then, build through the numbered scripts and save the same master file, so the
  build stays reproducible. In a live session, `exec(open(path).read())` a script and call its
  functions instead of the command line.
- All modelling is written as bpy code in `<asset>/build/NN_<phase>.py`, copied from
  `assets/build_template.py`. Each script opens the master, deletes what it owns, rebuilds it,
  saves. Rerunning any phase is safe. Constants are measured metres with a comment naming the
  reference view they came from, or `# inferred`.
- Skill scripts (all take `-- --help`):

| Script | Purpose |
| --- | --- |
| `scripts/init_master.py` | master .blend: units, collections, calibration proxies, reference planes at real scale, game camera |
| `scripts/review_render.py` | clay / silhouette / wire / checker / material renders from fixed views, the reference-matched camera, gameplay pixel size, turntables, posed frames |
| `scripts/compose_review.py` | compare sheet (reference, render, overlay, gameplay strip) plus silhouette IoU and width-profile numbers; plain Python with Pillow |
| `scripts/world_gate.py` | world-registered silhouette IoU for orthographic reference views: the camera covers the reference matte's exact world window, so scale and placement errors count |
| `scripts/validate.py` | topology, transforms, UVs, weights, armature, sockets, colliders, naming, tri budget; exit 1 on FAIL |
| `scripts/bake_maps.py` | normal and AO from HIGH to LOW, base colour, roughness, metallic; rebuilds delivery materials |
| `scripts/export_delivery.py` | GLB/FBX export with asset-manifest.json and animation-contract.json |
| `scripts/roundtrip.py` | imports the export into a blank Blender, reports what arrived, renders a check |
| `scripts/check_platform.py` | plain Python: checks a GLB against a platform profile (tris per mesh/part, texture size, skin, R15 names, cages, bytes, compression); exit 1 on FAIL |
| `scripts/optimize_web.sh` | gltf-transform meshopt + WebP/KTX2 + texture resize for web profiles; `--rigged` keeps nodes and materials |
| `scripts/run_bpy.py` | runs any Blender script above with the `bpy` module when no Blender binary exists |
| `scripts/sheet_qa.py` | plain Python + Pillow: checks a generated reference sheet (panel count, equal heights, shared ground line, flat background, front/back width) and crops it into `ref/<view>.png` mattes with world_gate numbers; exit 1 on FAIL |

Read `references/categories.md` for the asset's category and `references/platform-targets.md`
for the target platform before Phase 0, and `references/reference-sheets.md` whenever there is
no usable orthographic reference. Read
`references/rigging-animation.md` before Phase 6 and `references/delivery-and-acceptance.md`
before Phases 1, 5 and 9. Read `references/blender-5-notes.md` when a script fails on a 5.x API or
before long renders and bakes.

## Gate protocol (used at the end of every phase)

1. `review_render.py` with `--ref-cam AZ EL LENS` (estimated in Phase 0) plus
   `front,side,threequarter`, in the mode the phase asks for, with `--gameplay-px` set to the
   subject's on-screen height in the game (default 128).
2. `compose_review.py --measure` against the reference view that matches the camera. Read the
   sheet and the numbers. Look at the images; the numbers catch drift the eye forgives.
   compose_review aligns the two silhouettes by their bounding boxes, so it cannot see a model
   that is too short or off its axis. For orthographic sheets, also run `world_gate.py` on
   cleaned reference mattes (crops from `sheet_qa.py` already are, with axis, ground row and
   scale in `00_sheet_qa.json`; otherwise erase labels, rulers, floor lines and anything the
   model does not include) and hold that number to the phase tolerance. When the reference's own views disagree
   (a cape wider in the front view than in the back view), record the conflict and the per-view
   ceiling as a deviation instead of chasing both.
3. Write the mismatches as measurements, not adjectives: "head 12 percent too tall", "wheelbase
   0.3 m short", "band 4 width +0.06". Fix the constants in the build script, rerun the phase,
   re-render. Repeat until every mismatch is inside the phase tolerance.
4. Show the user the compare sheet, the remaining deviations, and what was inferred. Continue on
   approval. If the user said not to ask, continue when the tolerance is met and keep the sheets
   in `review/` for them. If the user reviews in a live viewport, reload the master there after
   each rebuild: anything hidden only for rendering (a mannequin under the costume) still shows
   in their view.

Tolerances: blockout IoU 0.85 and every band width within 0.05 of the reference (0.90 and 0.03
for forms); proportions within 5 percent (blockout) and 2 percent (forms) on the measurements
listed in the brief; materials pass when each role reads correctly under the moving light of a
material turntable and in greyscale at gameplay size.

## Phase 0: read the reference, write the brief

First decide whether the references are good enough to measure. A usable reference is an
orthographic sheet with at least front and side views at one scale on one ground line (a
turnaround or model sheet, an exact product drawing). A single concept, a perspective render, a
photo, a video frame, a sketch or a description in words is not: the build would copy guesses.
In that case run the reference sheet loop in `references/reference-sheets.md` before anything
else: write the partial brief, write the sheet prompt with the platform's style lock, hand it to
the user to generate (the agent never calls an image generator), stop and wait. When the sheet
comes back, `scripts/sheet_qa.py` checks it and crops the views; on FAIL, hand back a
regeneration prompt that names the measured defects. Keep any original concept as a detail and
colour reference next to the sheet. The user can skip the loop by saying so; then record in the
brief that proportions come from a non-orthographic reference and widen nothing else.

Look at every supplied image before touching Blender. Write `<asset>/asset-brief.md` in this
exact structure:

```text
ASSET      prefix and name (CH_, CR_, AR_, VH_, PR_, WP_, EN_)
CATEGORY   character | creature | architecture | vehicle | prop | weapon | environment, plus subtype (biped, quadruped, winged, wheeled, tracked, modular kit, hinged prop)
VIEWS      per image: view type (front, side, back, top, three-quarter, concept), estimated camera azimuth, elevation, lens (0 = orthographic), how much of the image height the subject fills, where the ground line sits
SCALE      real size along each axis with the evidence (human height, door, wheel, brick course, weapon grip); state the number used
PROPORTIONS 8 to 15 ratios measured in the image that the blockout gate will check (head heights, shoulder width to height, wheelbase to length, storey height to width)
PARTS      every part in construction and overlap order; for each: separate object yes/no, rigid/deforming/simulated, attaches to, moves about (pivot)
SILHOUETTE the 3 to 5 features that make it read at gameplay size
MATERIALS  per part: role (skin, scales, worn leather, painted metal, carved stone, glass), colour, roughness range, wear pattern
ARTICULATION rig family, joints or pivots, sockets needed, animation needs (none / idle only / full library)
INFERRED   every side, dimension or part the images do not show and the prior used to fill it
TARGET     one line per platform profile from references/platform-targets.md (roblox-prop, roblox-rig, roblox-accessory, roblox-layered, roblox-body, spawn, crazygames, astrocade, unity, unreal, godot, threejs): format, LOD0 tri budget, max texture, byte budget for web, rig map, game camera (elevation, distance, lens), subject height in pixels at typical gameplay distance
POLICY     for anything sold or published: originality (no franchise names, marks, characters or signature designs), the platform's content rules that apply (Roblox body modesty and proportion rules, one item per accessory, no gore), any generator used and the disclosure it needs; state PASS or the change needed before modelling
```

Platform comes first because it changes the whole build: a Roblox accessory is 4,000 triangles
at 2048, a Roblox avatar body is 15 named parts on an exact skeleton, a CrazyGames hero is
budgeted in megabytes, and a Spawn humanoid needs Mixamo-style bone names for IK. If the user
names several platforms, list each profile; build one master for all of them (section 10 of
the platform file). If a reference would fail a platform policy gate (for example an armoured
female body with exaggerated proportions sold as one Roblox bundle), say so now and propose the
compliant split before any modelling; finding out at upload costs fees that are not refunded.

Paid generators (Hyper3D Rodin, Hunyuan3D, FAL, anything that spends credits) are never called
by the agent. When a generated blockout would help, write the prompt and the reference crop,
hand them to the user to run, and import the file they return into HIGH as a starting mass. It
still goes through every gate.

Ask the user only for what the images cannot tell: target platform (or engine and format), real size when no
scale cue exists, budget tier, whether rigging and animation are needed, the game camera. Offer
these defaults and proceed with them when the user says to just go: 1 unit = 1 m, Z up in
Blender with the subject facing -Y, GLB export, the named platform's profile (standard tier from
the budgets table when no platform is named), a
three-quarter overhead camera at 50 mm, 128 px subject height, rig only if the category deforms,
no animation unless asked.

Keep every reference as a file in `<asset>/ref/` under a descriptive name before Phase 1: the
scripts load references from disk, and images pasted into the conversation arrive as temporary
files, so copy them there first.

Multi-image references: any number of images can come in one request. Mark which views are
orthographic sheets (measure from these) and which are perspective concepts (silhouette and
detail only, never proportions). Conflicting images: the orthographic sheet wins for dimensions,
the concept wins for surface detail; say which was used where. One image can also hold several
views (a turnaround or model sheet with front, side and back panels and detail callouts): give
each panel its own VIEWS entry with its pixel box, crop the orthographic panels into separate
files that share one scale and ground line (`ref/front.png`, `ref/side.png`, `ref/back.png`) for
`init_master.py` and the gates, and use the callouts for surface detail. Photographs: estimate the lens from perspective convergence (long lens for
telephoto product shots, 24 to 35 mm for phone photos), and match it in `--ref-cam`.

For a request covering several assets, run one asset per category through all phases first
(one character, one creature, one kit piece, one vehicle), get those approved, then apply the
proven scale, rig, material and export rules to the rest. Each role still gets its own forms and
motion; a shared rig family does not mean shared proportions.

## Phase 1: calibration and master file

Decide the canonical unit before any modelling and keep it: 1 unit = 1 m, Z up, -Y forward,
origin at the ground contact point (ground centre for vehicles, grid corner for kit pieces).
If the target game uses other logical units, choose once between converting every dependent
value (movement speed, reach, cell size, colliders, camera offsets) with a documented factor, or
mapping only at the render boundary. Never shrink the asset alone while gameplay metrics stay
in old units.

The commands in this file use an illustrative 1.85 m knight (`CH_Knight`, Unity); take every
asset-specific value (name, height, camera, budget, engine, inferred list) from the brief.

```bash
$BLENDER_BIN --background --python scripts/init_master.py -- \
  --out CH_Knight/CH_Knight_master.blend --name CH_Knight --height 1.85 \
  --ref-front ref/front.png --ref-right ref/side.png --ref-extra ref/concept.png \
  --subject-frac 0.88 --ground-frac 0.04 --cell 2.0 --cam-elev 50 --cam-az 30 --cam-dist 12 --cam-lens 50
```

This writes the collections (REF, HIGH, LOW, RIG_CTRL, RIG_DEF, COLLISION, SOCKETS, EXPORT),
a ruler at the target height with metre ticks, a grid cell, door clearance, a collision capsule,
the game camera, and the reference images as standing planes at real scale with their ground
line on z = 0. Every asset passes through this calibration; a hero, an enemy and a doorway that
were never in the same file at the same scale will not fit each other in the engine.

Naming from `references/delivery-and-acceptance.md`: `CH_Knight_Body_LOD0`, `DEF-upper_arm.L`,
`SOCKET_hand.R`, `COL_torso`, `CUT_window`. No `.001` names in anything that ships.

## Phase 2: blockout and silhouette gate

Build `build/02_blockout.py` from the template. Primary masses only: torso, head, pelvis and
limbs as simple volumes; body shell, wheels and cabin for a vehicle; floor, walls, roof and
openings for a kit piece. Hands, feet, jaw, horns, wings, doors, turrets and other appendages
are separate rough objects from the start. Joint centres and pivots are placed now, at the
positions the brief measured, because everything later hangs off them.

Check weight and balance: feet and hips that can support the mass, a forward driving line for a
runner, a ribcage and pelvis for a quadruped, a neck and wing root that can carry the intended
action, wheels under the mass of a vehicle. Add costume, armour, cladding and panels as distinct
volumes. Check weapon reach, hand clearance, door swing and the silhouette in the most extreme
pose or state the asset will hit (attack, crouch, turn, full steering lock, door open).

Gate in clay and silhouette modes, LOW collection, `--show-ref` once to confirm scale against
the ruler. The category must read from the game camera without texture, particles or labels.
For multi-asset work, render the greybox lineup at relative scale and check that roles differ
in shoulder width, head shape, posture and stance, not only colour.

```bash
$BLENDER_BIN --background --python scripts/review_render.py -- --blend CH_Knight/CH_Knight_master.blend \
  --out CH_Knight/review/02_blockout --collections LOW --views front,side,threequarter \
  --ref-cam 35 12 50 --mode clay --gameplay-px 128
python scripts/compose_review.py --ref ref/front.png --render CH_Knight/review/02_blockout/clay_front.png \
  --out CH_Knight/review/02_blockout/compare_front.png --measure --gameplay-px 128
```

## Phase 3: forms

`build/03_forms.py`. Order: primary anatomy or body masses, then secondary forms (cloth masses,
armour construction, panel breaks, mouldings), then tertiary detail (folds, damage, rivets,
pores, weave) last and only at a scale that survives the texture resolution and the game camera.
Large random noise hides form and shimmers at distance.

Organic: join the blockout into a fused base (voxel Remesh at about 1/200 of the height) in HIGH
and shape it with `push`, or keep the skin-chain base and refine its radii and joint positions.
Hard surface: loft, extrude, spin and cut with real panel gaps, plate thickness and bevels that
catch light. Model the real overlap order for layered parts. Eyes, teeth, claws, horns, glass,
lights and membranes stay separate where they need independent shading, deformation or
articulation; consolidate only the export copy.

Keep the complete underlying body or hull in the master even where a costume or panel covers it;
author coverage cuts on the export copy and test every equipment combination for holes.

Characters: `references/categories.md` section 2 covers faces fitted to calibrated blueprints,
hands, the neck join, armour fitted to the garment underneath, and strand hair colliders and
shading. Review close-ups of the neck, hands and every armour overlap from several angles with
everything the viewport shows; check clearances with mesh overlap tests.

Stylised flat-colour props (the usual Roblox, Astrocade and casual web look): skip HIGH and the
normal bake. Build the forms directly as the LOW delivery meshes, one flat material per role, and
in Phase 5 bake only the colours into one small atlas per MeshPart (512 is plenty for a hand-held
prop). The worked example in `examples/PR_CrownMoleKing/` does exactly this, sheet to Roblox GLB,
and its three build scripts are the fastest starting point for any similar prop: copy them, change
the constants, keep the structure.

Gate: clay from the reference camera and all fixed views, forms tolerance, plus a `--turntable 8`
clay pass. The silhouette at gameplay size must still match Phase 2; if forms shifted it, fix the
forms, not the reference.

## Phase 4: topology

`build/04_topology.py` produces the LOW delivery meshes over the approved forms. Place topology
where silhouette, joint bending, facial movement, cloth folding, panel edges or material
boundaries need it. A uniform remesh of a sculpt is not deformation topology (Blender retopology
notes: https://docs.blender.org/manual/en/latest/modeling/meshes/retopology.html). Practical route:
a clean base cage with loops at every joint (a skin-chain mesh at Subdivision 1 already has
them), Shrinkwrap to the HIGH form, Subdivision 1, then edit loops at joints and creases.
Rigid parts and rubble can use controlled Decimate; hero shoulders, hands, faces, hinges and
simulated cloth get deliberate loops.

Quads in the source, triangulated delivery; lock the triangulation before baking so shading does
not change later. Run the cleanup: doubles, stray islands, zero-area faces, flipped normals,
overlapping interior shells. Open boundaries are fine on cloth sheets, hair cards and decals;
collision proxies must be closed. Build LOD1 and LOD2 now with `lod_copy` and fix their outlines
by hand, keeping head, shoulder, weapon, wheel and doorway silhouettes.

Budget: the smallest LOD0 among the brief's TARGET profiles is the hard ceiling for that
profile's export; build LOD0 for the most generous target and `lod_copy` down for the others
(Roblox accessories, bodies and Astrocade usually land on what the generic tier calls LOD1 or
LOD2). Roblox bodies are budgeted per part (head, torso, each arm, each leg), so keep the 15
parts as separate LOW objects named `<Part>_Geo` from this phase on.

Gate: `validate.py` with the budget tier's tri count (exit 0, warnings explained), wire mode
render of LOW, and a clay compare against Phase 3 renders showing no silhouette loss.

```bash
$BLENDER_BIN --background --python scripts/validate.py -- --blend CH_Knight/CH_Knight_master.blend \
  --collections LOW,COLLISION,SOCKETS --out CH_Knight/review/04_validate.json --budget-tris 60000 --require-uv
```

## Phase 5: UVs, baking, materials

`build/05_materials.py`. Seams where construction and visibility support them; unique space for
faces, focal costume, hero surfaces; trims and tiles for repeated edges and large surfaces;
atlases for small props; one texel density per asset family. Check distortion with the checker
render at joints, hems, face and grip. Inspect padding at the lowest useful mip.

Author original materials in Blender (procedural or painted) starting from the role named in the
brief: skin, dry bone, woven cloth, worn leather, corroded metal, painted steel, carved stone,
glass. Roughness ranges that match the role; edge wear that follows construction and contact,
not a white outline around every edge; no baked directional lighting in base colour. Then bake
the portable set and rebuild the delivery materials:

```bash
$BLENDER_BIN --background --python scripts/bake_maps.py -- --blend CH_Knight/CH_Knight_master.blend \
  --low LOW --high HIGH --res 2048 --maps normal,ao,basecolor,roughness,metallic \
  --out CH_Knight/textures --extrusion 0.02 --ray-dist 0.05 --margin 16 --samples 64 \
  --match-by-name --rebuild-material --save CH_Knight/CH_Knight_baked.blend
```

Bake by named group where projections cross onto neighbours (teeth, layered garments); keep
transparent shells (corneas, visors, glass) out of the sources with `--exclude-sources`. LOD0 is
baked; LOD1 and LOD2 reuse its material and maps (they came from `lod_copy`, same UV layout).
Pass `--all-lods` only when a LOD has its own UVs. Document colour space per map, normal-map
green convention and any channel packing in the manifest.

Gate: material mode render with `--turntable 12` (moving light across the surface), greyscale
compare at gameplay size, checker render clean at the joints. Hard edges and UV seams inspected
in the normal-mapped turntable.

## Phase 6: articulation

Skip only for static props and kit pieces without moving parts. Platform rig rules first:
Roblox bodies and layered clothing need the exact R15 hierarchy (build with the R15 family, or
deliver an unrigged A/T-pose mesh to Studio's Avatar Setup); Spawn humanoids need Mixamo-style
names; both are produced from the DEF- master through the maps in
`references/platform-targets.md` section 9. Rigid mechanisms for Roblox (blades, trapdoors, lids)
are usually better as separate parts with pivots driven by constraints in code than as skins.
Otherwise `build/06_rig.py`:
deformation skeleton in RIG_DEF from the rig family in `references/rigging-animation.md`,
controls in RIG_CTRL, real pivots for every hinge, wheel, door and turret, sockets in SOCKETS
with the axis convention (+Y forward of the attachment, +Z up). Bind every deforming piece to the
same skeleton, normalise weights, four influences per vertex as the delivery target, rigid armour
to one bone. Apply scale and rotation before binding; never apply an Armature modifier as
cleanup.

Gate: extreme-pose sheet (`review_render.py --action <pose_action> --frame N` for every pose the
reference file lists), all separate parts visible together; `validate.py` shows no unweighted
or over-influenced vertices; each socket tested with its real attachment in at least one pose.

## Phase 7: secondary motion

Only for garments, chains, tails, wings, cables, tracks or antennae that the brief marked as
simulated or secondary. Follow section 6 of `references/rigging-animation.md`: separate render,
simulation and collision representations, pinned attachment areas with real clearance, one owner
per vertex's motion, a bone-chain fallback. Gate: posed renders in the extreme poses show no
body or weapon penetration, and the fallback chain alone still reads as the same garment.

## Phase 8: animation

Only when requested. `build/08_anim.py` or the live session. Named Actions with deliberate
ranges, loop flags and pose markers for events; in-place locomotion tagged with its speed;
upper-body layers with a reference pose and mask; bake IK to the deformation skeleton for
delivery and keep the unbaked master. Gate: each clip rendered as a short turntable-free sequence
at the game camera, loop seams checked for root drift and pops, event timings read back from
`animation-contract.json`.

## Phase 9: export and round trip

Export the explicit selection (LOW, RIG_DEF, SOCKETS, COLLISION) with the manifest, then import
it into a blank Blender and compare against the manifest. Nothing from REF, HIGH or RIG_CTRL
ships.

```bash
$BLENDER_BIN --background --python scripts/export_delivery.py -- --blend CH_Knight/CH_Knight_baked.blend \
  --out CH_Knight/exports --name CH_Knight --format GLB --split-lods \
  --inferred "back of cloak from symmetry, sole tread generic" --engine unity
$BLENDER_BIN --background --python scripts/roundtrip.py -- --file CH_Knight/exports/CH_Knight.glb \
  --out CH_Knight/review/09_roundtrip --expect-height 1.85
```

Per platform: export each TARGET profile to `exports/<profile>/` from its own delivery copy
(LOD, texture size, bone map, axis and unit factor from the platform file), pass `--engine
<profile>` so the manifest records it, then:

```bash
bash scripts/optimize_web.sh exports/crazygames/CH_Knight.glb exports/crazygames/CH_Knight.opt.glb crazygames --rigged   # web profiles only
python3 scripts/check_platform.py exports/crazygames/CH_Knight.opt.glb --profile crazygames --json review/09_crazygames.json
python3 scripts/check_platform.py exports/roblox-rig/CH_Knight.glb --profile roblox-rig --json review/09_roblox.json
```

Blender cannot import meshopt files, so run `roundtrip.py` on the uncompressed export and check the
compressed copy with `npx -y @gltf-transform/cli@4 validate <file>` plus `check_platform.py`.
Roblox exports stay uncompressed (the importer recompresses; check_platform fails on meshopt or
Draco in a Roblox profile). FBX deliveries: check a GLB exported with the same settings.

Gate: roundtrip exit 0 (tri counts per LOD, bone names, clip lengths, images all match the
manifest; height within 1 percent; nothing below the ground plane), `check_platform.py` exit 0
for every profile, and the roundtrip clay render matches the Phase 3 clay render. Then import into a clean project of the target engine if one is
available and play every clip with the real weapon or garment combination. Handover to the
platform's own build skill when one exists: Roblox Studio work goes to `roblox-game-creation`
(upload via the Roblox Blender plugin or the 3D Importer, then place and verify by code),
Spawn to `spawn-build` (asset PUT, `model.forward`, clip and socket names), CrazyGames to
`game-foundation` / `crazygames-port` (bundle byte budget), Astrocade to `astrocade-3d-build`
(GLTFLoader in the paste file). Give that skill the file paths, node, socket, material and clip
names, the unit factor and the axis decision.

## Phase 10: acceptance and handover

Run the checklist in `references/delivery-and-acceptance.md` section 4. Produce
`review/final/`: the compare sheets from the reference camera and fixed views, the gameplay-size
greyscale strip, the material turntable, the extreme-pose sheet, validate.json and roundtrip.json.
Report to the user in this order: what matches, the measured deviations that remain, everything
inferred without reference coverage, budgets used versus each platform profile, the exact files
delivered per platform, and for anything to be sold the remaining upload costs and policy risks
from the platform file.
Do not describe the asset as matching the reference where a measurement says otherwise.

## Working rules

- Measure, then model. Every constant comes from the brief or is marked inferred.
- Silhouette before form, form before detail, topology before texture, bind before animation.
- Render evidence at every gate; the viewport is not evidence.
- One file, one scale: every asset passes through the calibration file with the ruler.
- Separate what moves, shades or simulates independently; consolidate only the export copy.
- Keep the master non-destructive; apply modifiers on the delivery copy.
- Never rename an export to satisfy a loader that expects a different skeleton; provide a mapping.
- Say what was not visible in the reference. A guessed back is a guess in the manifest.
- The platform limit is a wall, the budget tier is a suggestion; check every export with
  `check_platform.py`, never by reading the Blender stats.
- Original designs only for anything published or sold: borrow a genre, never a franchise's names,
  marks, characters or signature looks.
- Never spend credits: paid generators are run by the user from prompts the agent writes.
- No usable orthographic reference, no modelling: write the sheet prompt first and wait for the
  sheet.
- When a sheet's own views disagree and every fix for one view breaks another, keep the views that
  agree inside tolerance, record the other as a deviation with its numbers, and move on; show the
  user rather than looping.
