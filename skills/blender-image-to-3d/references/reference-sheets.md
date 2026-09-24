# Reference sheets: prompt, generate, check

Read in Phase 0 whenever the user has no usable orthographic reference: an idea in words, a single
concept or perspective image, a photo, or a sheet that failed the checks below. The build is only
as good as the sheet it measures against; a crude or inconsistent sheet produces a crude or
inconsistent model however well the gates are run.

## Contents

1. The loop
2. Who generates
3. Sheet layout (the contract the scripts rely on)
4. Prompt template
5. Category blocks
6. Style locks per platform
7. Sheet check (`scripts/sheet_qa.py`) and regeneration prompts
8. Known failure modes of image generators

## 1. The loop

1. Write the brief's ASSET, CATEGORY, SCALE, PARTS, SILHOUETTE, MATERIALS and TARGET lines from
   the user's description first (a partial brief is fine). The prompt is written from the brief,
   so the sheet shows exactly what the build needs to measure.
2. Write the sheet prompt (section 4) and hand it to the user with the generator, aspect ratio and
   what to send back. Stop and wait. Do not model from imagination while waiting.
3. When the sheet arrives, save it as `<asset>/ref/sheet_v1.png` and run `scripts/sheet_qa.py`.
4. PASS: the script has cropped the panels into `ref/front.png`, `ref/side.png`, `ref/back.png`
   (and `top.png` when present) on one shared scale and ground line. Continue Phase 0 with those.
   FAIL: write a regeneration prompt that names the exact defects (section 7), hand it over,
   repeat. Two failed rounds on the same defect: crop the best panels by hand, record the
   conflict as a deviation in the brief, and continue rather than looping.
5. Record in the brief which generator made the sheet and the prompt used (INFERRED and POLICY
   lines), so the manifest says the reference was AI-generated.

## 2. Who generates

The agent never calls an image API. It writes the prompt; the user runs it (Gemini / NanoBanana 2
by default, or any generator the user names) and sends the image back. Say which generator the
prompt is written for, because phrasing differs: NanoBanana 2 / Gemini reads plain language, puts
weight on what comes first, and takes aspect ratio as words in the body, not flags. When the user
has an existing concept image, tell them to attach it to the generation as the style and design
reference and say so in the prompt ("match the design in the attached image exactly").

## 3. Sheet layout (the contract)

One image, all views generated together. Separate generations per view drift in proportions and
details; one image keeps them consistent.

- Aspect: landscape 16:9 for props, weapons, vehicles and creatures; 3:2 for characters.
- Panels left to right, in this order: FRONT, SIDE (right side, facing right), BACK, then optional
  TOP for props and vehicles. Characters and creatures: FRONT, SIDE, BACK only.
- Every panel: orthographic, camera at the subject's mid-height, no perspective, no tilt.
- Same scale in every panel. The elevation panels (front, side, back) share the same total
  height, top and bottom aligned, standing on one shared horizontal ground line. A top view is a
  plan: its vertical size is the object's depth, so it differs from the others by design.
- Plain flat light-grey background (about #D0D0D0), no floor texture, no shadow on the ground,
  no vignette, no scenery.
- Even, flat studio lighting from the front; no dramatic rim or coloured light (the sheet is for
  shape and colour, not mood).
- Clear empty gaps between panels (the script finds panels by these gaps).
- No text, no labels, no arrows, no rulers inside the image (labels break the silhouette matte).
- Characters: A-pose (arms 30 to 45 degrees down from horizontal, legs slightly apart), neutral
  face, hands open, feet flat, no weapon in hand (weapons are their own sheet).
- Hinged or moving parts shown closed in the main panels.
- Optional second image (only when detail matters): the same asset as a 3/4 beauty render plus
  close-up callouts of materials and small parts. Used for surface detail only, never measured.

## 4. Prompt template (NanoBanana 2 / Gemini)

Fill every bracket from the brief. Keep the order: subject first, then layout, then constraints.

```text
Orthographic 3D model reference sheet of [ASSET, one line: what it is, overall shape, the 3 to 5
silhouette features from the brief], [real size, e.g. "1.2 metres wide and 0.85 metres tall"].

Show exactly [3 or 4] views of the same single object side by side from left to right: front view,
right side view, back view[, top view]. Every view is a true orthographic projection with no
perspective, camera level with the middle of the object. All views are drawn at exactly the same
scale, the same height, standing on one shared straight horizontal ground line, evenly spaced with
clear empty gaps between them.

Design details: [PARTS in overlap order, with materials and colours from the brief, e.g. "oak
plank body with visible board seams, three hammered iron bands, a gold lock plate with a keyhole
at front centre, a domed lid of curved planks"]. The design is identical in every view: same
number of bands, same lock, same proportions.

Style: [STYLE LOCK from section 6].

Plain flat light grey background, even soft studio lighting from the front, no cast shadows on the
ground, no scenery, no props, no people, no text, no labels, no numbers, no watermark, no border.
Wide landscape image in [16:9 or 3:2] aspect ratio.
```

For a regeneration, keep the original prompt and append one paragraph that names the defects
(section 7). Always attach the previous sheet or concept when the design itself was right.

## 5. Category blocks

Add the matching block to the Design details paragraph.

- **Prop / loot / hinged prop:** "Lid, doors and moving parts closed. Chunky readable shapes,
  bevelled edges, [2 to 3] main materials." Add a TOP view for anything with a meaningful top
  (chests, tables, vehicles).
- **Weapon:** stand the weapon upright, point or head up, grip at the bottom, in every view:
  "front view showing the flat of the blade, side view showing the edge, back view". All three
  are the weapon's full length tall, so the height and ground-line checks work unchanged.
  Mention the grip length for a hand.
- **Character (biped):** "Standing in a relaxed A-pose, arms angled 40 degrees down, palms facing
  the thighs, feet shoulder-width apart, neutral expression, looking straight ahead. Full body,
  head to feet, nothing cropped. Clothing and armour fitted to the body with clear layering."
  For anything that will be a Roblox body, add: "Wearing an opaque, simple sports top and shorts
  in [a colour different from the skin]; athletic, non-exaggerated proportions." Armour and
  accessories then get their own prop-style sheets.
- **Creature (quadruped, winged):** "Standing neutral pose, all legs visible, tail and wings
  relaxed and extended so their full length reads in the side view." Side view is the key
  panel; mention it first in the design details.
- **Vehicle:** "Wheels straight, doors closed, ground clearance visible." Views: front, side,
  back, top.
- **Modular kit piece:** one sheet per piece. "Shown as a flat front elevation, side section and
  top plan, on a [2 metre] grid module, edges straight and square so pieces tile."

## 6. Style locks per platform

Pick from the brief's TARGET line and keep the same lock for every asset in a game.

- **Roblox (default):** "stylised low-poly 3D game asset, chunky bold shapes, bevelled edges,
  bright saturated flat colours with simple painted shading, clean readable silhouette, blocky
  toy-like proportions". For a named game, add its palette ("warm dungeon golds and dark stone").
- **CrazyGames / three.js stylised:** "stylised low-poly 3D game asset, hand-painted textures,
  clean shapes, soft colour gradients, readable at small size".
- **Astrocade (small, mobile):** "very simple chunky low-poly 3D toy style, 3 to 4 flat colours,
  thick shapes, no fine detail".
- **Spawn:** same as CrazyGames stylised unless the world has its own look; name the world's
  palette.
- **Realistic / PBR:** "realistic 3D game asset render, physically based materials, [material
  list with wear], neutral studio light". Use only when the brief asks for it; realistic sheets
  need far more modelling time for the same score at the gates.
- Never name a franchise, studio, game or artist as the style ("in the style of X"). Describe the
  look in plain words. Originality is part of the POLICY line.

## 7. Sheet check and regeneration

```bash
python3 scripts/sheet_qa.py --sheet PR_Crown/ref/sheet_v1.png --views front,side,back \
  --out PR_Crown/ref --json PR_Crown/review/00_sheet_qa.json
```

It finds the subject panels against the background, reports each panel's box, compares heights
and ground lines of the elevation views (a `top` view is a plan: it is checked instead against the
front width and the side depth, so it may be shorter or taller than the elevations), and on PASS
writes `ref/<view>.png` crops that share one scale and ground line.
Add `--expect-ratio side:front=0.62` style checks when the brief knows a proportion.

Each crop's `axis_col` is the centre of the subject's base (2 to 8% of the height above the
ground), not the centre of its bounding box: a part that sticks out on one side (a medallion on a
crown seen from the side, a nose, a handle) drags the box centre off the real axis and shows up
in `world_gate.py` as a model shifted sideways. Pass `axis_col`, `ground_row` and `m_per_px` from
`00_sheet_qa.json` straight to `world_gate.py`; `bbox_axis_col` is kept for comparison only. For
a subject whose base is not centred on its axis (a leaning tower, a character mid-stride), set the
axis by hand and say why in the brief.

Checks and the regeneration line to append when one fails:

| Check | FAIL when | Append to the prompt |
|---|---|---|
| Panel count | not the number of views asked for | "Exactly [N] separate views with clear empty gaps between them, nothing else in the image." |
| Height match | panel heights differ by more than 3% | "All views must be exactly the same height and scale; the [view] view is currently [x]% taller." |
| Ground line | bottoms differ by more than 2% of height | "Every view stands on the same straight horizontal ground line." |
| Background | background not flat (noise, gradient, floor) | "Plain flat light grey background only, no floor, no shadows, no gradient." |
| Front/back width | front and back widths differ by more than 5% | "Front and back views must be the same width; they are mirror projections of the same object." |
| Symmetry (optional `--symmetric`) | front view left/right halves differ by more than 8% | "The front view is perfectly symmetrical left to right." |
| Text | the user or the agent sees labels, numbers, logos | "No text, letters, numbers or labels anywhere." |

The agent also looks at the crops itself before accepting them: perspective (visible top or
underside in a side view, converging lines), details that change between views (band count,
buckle side), and anything cropped at the image edge. Script PASS plus a clean visual check is
the gate.

## 8. Known failure modes of image generators

- Drifts into a three-quarter view in the "side" panel. Fix: "true side profile, camera at 90
  degrees, only one side visible".
- Back view invents a different design. Fix: attach the first good sheet and ask for "the back
  view of this exact object".
- Adds a floor shadow or reflection under each panel, which joins into the silhouette. Fix: the
  background line in section 7; `sheet_qa.py` also trims a thin shadow band if `--trim-shadow`.
- Scales panels to fill space (tall front, short side). Fix: the height-match line.
- Characters come out in T-pose with foreshortened arms, or with weapons in hand. Fix: restate
  A-pose and "empty open hands".
- Very thin parts (antennae, sword tips, whiskers) vanish at sheet resolution. Ask for the
  highest resolution the generator offers, and a separate callout image for thin parts.
