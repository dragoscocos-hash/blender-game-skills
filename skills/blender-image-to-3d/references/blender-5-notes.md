# Blender 5.x notes

API changes and runtime behaviour met while building assets with this skill on Blender 5.2, plus
review and look-development lessons that are easy to lose between sessions. Read this when a
script fails on a 5.x API, before long renders or bakes, and when the review renders and the
user's viewport disagree.

## 1. API changes that break older bpy code

- Geometry Nodes modifier inputs are no longer ID properties: `mod["Socket_2"] = v` raises
  "id properties not supported". Set `getattr(mod.properties.inputs, identifier).value = v`, where
  `identifier` comes from the node group's interface socket (`socket.identifier`). Keep a fallback
  to `mod[identifier]` for 4.x.
- Actions are layered: `action.fcurves` is gone. Walk `action.layers[*].strips[*].channelbags[*].fcurves`
  (or keyframe through `keyframe_insert` and let Blender create the channelbag).
- Materials and worlds always use nodes; `use_nodes` is deprecated. Guard it with
  `bpy.app.version < (5, 0, 0)`.
- Vertex group names live on the mesh data. A copied mesh already carries the names, so creating
  the same group again yields `Group.001`; check `ob.vertex_groups.get(name)` first, and merge any
  `.001` groups before export.
- EEVEE's engine identifier differs between versions (`BLENDER_EEVEE_NEXT` in the 4.2-era
  releases, `BLENDER_EEVEE` in 5.x, where the other is rejected); try both inside
  `try/except TypeError`.
- EEVEE does not support the Principled Hair BSDF. Give hair (and anything else EEVEE cannot shade)
  two Material Output nodes, one with target EEVEE and one with target CYCLES. Cycles renders the
  CYCLES-target output even when the EEVEE one is active; anything that rewires an output for
  baking must pick the same node (`scripts/bake_maps.py` does).
- Look nodes up by type (`n.type == "BSDF_PRINCIPLED"`, `"OUTPUT_MATERIAL"`, `"BACKGROUND"`), never by
  display name: names are translated in non-English UIs.
- Command-line values that start with a minus sign need the `--arg=-0.28,0,1` form, or argparse
  reads them as a new option.

## 2. Runtime and performance

- Cycles on Apple Silicon: enable only the METAL device. Adding the CPU as a second device made
  frames about twice as slow (M-series Pro, 1080p, 48 to 64 samples with OpenImageDenoise ran at
  12 to 20 s per frame GPU-only).
- `render.use_persistent_data = True` speeds up animations where only the camera or a few objects
  move.
- Selected-to-active bakes spend most of their time syncing the scene: hide every renderable that
  is neither a source nor the target (except for AO, where neighbours should occlude). Strand hair
  with tens of thousands of curves is the usual culprit.
- Transparent shells (corneas, visors, glass) catch bake rays in front of what they cover; leave
  them out of the sources (`bake_maps.py --exclude-sources`) and give the delivery copy its own
  simple transparent material.
- A long headless render should write numbered frames and skip frames that already exist, so it
  can be stopped, fixed and resumed; encode with ffmpeg at the end.

## 3. Review and look-development lessons

- The viewport is what the user sees. An object hidden only with `hide_render` (a body mannequin
  under the costume, a helper) still shows in the user's viewport and pokes through there; hide
  it for both viewport and render, and review close-ups with everything the viewport shows.
- Match painted concept colours by numbers: sample the median sRGB of the same world-space box
  in the reference and in a render under the review lights, and adjust albedo until they agree.
  Grey-looking leather was specular sheen and edge-wear masks firing over whole thin straps, not
  the base colour.
- Painted concept metal usually reads brown-lit: give glossy rays their own warm studio (Light
  Path "Is Glossy Ray" in the world shader) while diffuse rays keep a dark environment.
- The Standard view transform keeps saturated skin and hair close to a painted sheet; AgX washes
  them out. Pick one for the look and keep it for every comparison.
- When a colour looks wrong, test hypotheses one at a time on a small render border (lighting,
  reflections, clipping, the shader itself) and give each object a flat emission debug colour to
  find which object is at fault before changing materials.

## Lessons from the platform eval runs (Blender 5.0.1, bpy module, 2026-09-24)

- `smart_project` with sharp-edge seams can shatter a bevelled hard-surface part into hundreds of
  UV islands; turn the sharp-seam option off for props and check island count in validate.json.
- Baking base colour from fully metallic surfaces returns black (no diffuse). Bake colour from a
  copy with Metallic set to 0, then bake metallic separately.
- `review_render.py --action` does not see clips that live only on muted NLA tracks; render poses
  from a copy with the action assigned directly.
- `roundtrip.py` measures height in whichever clip the importer leaves active; for files with
  clips, read height from the rest pose (or export a clip-free copy for the height check).
- Blender cannot import EXT_meshopt_compression GLBs; validate compressed files with gltf-transform.
- AO baked from HIGH to LOW where the two meshes coincide exactly comes out black; for props with
  no separate HIGH detail, skip the AO bake or bake AO from the LOW mesh onto itself.

## Lessons from the first sheet-to-model build (PR_CrownMoleKing, 2026-09-24)

- Material colours set from bpy (`Base Color` default_value) are linear. Colours picked from an
  sRGB reference must be converted (`((c + 0.055) / 1.055) ** 2.4`) or every material renders
  washed out (purple velvet came out lilac).
- Swept tubes (claws, horns, handles, tails) need a fixed reference vector for the ring frame, for
  example the part's outward direction. Building the frame from `tangent x world up` flips when
  the tangent turns vertical and leaves dark cracks where rings twist.
- Fully metallic stylised gold goes copper-orange under the review world. For a flat-colour
  stylised look use metallic about 0.5 and roughness about 0.35, then check at gameplay size.
- Small lumpy parts sitting on a curved surface (a nugget on a dome) float once noise is applied:
  sink them into the surface by about a third of their radius and recheck the round-trip height,
  since the top of that part is often the asset's highest point.
- The top of a turnaround's topmost part sets the delivered height: after moving it, rerun
  `roundtrip.py --expect-height` (a 0.03 m drop on a 0.34 m crown failed the 1 percent check).
