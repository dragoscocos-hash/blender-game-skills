# Worked example: PR_CrownMoleKing (sheet to Roblox GLB)

First asset built end to end with the reference sheet loop, 2026-09-24. A stylised loot crown for
a Roblox dungeon game: 6,032 triangles in two MeshParts (Body 5,428, Jewels 604), one 512 colour
atlas each, 292 KB GLB, `check_platform.py --profile roblox-prop` PASS, round trip height 0.338 m
against 0.34 m.

Use it as the template for any stylised flat-colour prop: copy `build/`, change the constants,
keep the structure (02 gated masses, 03 forms straight into LOW, 05 join, unwrap, colour bake,
export).

## 1. Sheet (user-generated in Gemini / NanoBanana 2)

Prompt v1 is the section 4 template of `references/reference-sheets.md` filled from the brief
(3 views, 42 x 34 cm, Roblox style lock). v1 FAILED `sheet_qa.py`: heights 3.5% apart and ground
lines 3.5% apart, caused by dirt clumps and a root hanging below the base. Fixed with one edit
prompt on the attached v1 (cheaper than regenerating, keeps the design):

```text
Edit the attached reference sheet. Keep the crown design, colours, style, layout, spacing and grey
background exactly the same. Fix only these points:
1. Every view stands on the same straight ground line with its bottom rim touching it. Remove the
dirt clumps and the root that hang below the crown's bottom rim or stick out past its sides; dirt
only sits on top of the lower rim and in the crooks of the claws, never below or outside the
crown's base.
2. All three views are exactly the same height.
3. The dirt clumps sit in the same places on the object in every view, like one physical object
seen from three angles.
4. Exactly six gems around the band, each colour appearing once: amber, grey, pink, purple,
black, orange.
No text, no labels, no watermark.
```

v2 PASSED: all three panels 275 px tall on one ground line. The side panel was a view from -X
(the front appears on the right), so it is `--ref-left` / `left` (az 270) in the scripts.

## 2. Commands

```bash
SK=<skill dir>; A=PR_CrownMoleKing
python3 $SK/scripts/sheet_qa.py --sheet $A/ref/sheet_v2.png --views front,side,back \
  --out $A/ref --json $A/review/00_sheet_qa.json --height 0.34 --trim-shadow
python3 $SK/scripts/run_bpy.py $SK/scripts/init_master.py --out $A/${A}_master.blend --name $A \
  --height 0.34 --ref-front $A/ref/front.png --ref-left $A/ref/side.png --ref-back $A/ref/back.png \
  --subject-frac 0.926 --ground-frac 0.037 --cam-elev 40 --cam-az 30 --cam-dist 2 --cam-lens 50
python3 $SK/scripts/run_bpy.py build/02_blockout.py --master ${A}_master.blend
# gate, per view (front az 0, left az 270, back az 180), numbers from 00_sheet_qa.json
python3 $SK/scripts/run_bpy.py $SK/scripts/world_gate.py --blend ${A}_master.blend --out review/02_blockout \
  --matte ref/front.png --az 0 --m-per-px <m_per_px> --axis-col <axis_col> --ground-row <ground_row> \
  --collections LOW --name front
python3 $SK/scripts/run_bpy.py build/03_forms.py --master ${A}_master.blend
python3 $SK/scripts/run_bpy.py build/05_bake_export.py --master ${A}_master.blend --out exports/roblox-prop
python3 $SK/scripts/check_platform.py exports/roblox-prop/$A.glb --profile roblox-prop
python3 $SK/scripts/run_bpy.py $SK/scripts/roundtrip.py --file exports/roblox-prop/$A.glb \
  --out review/09_roundtrip --expect-height 0.34
```

## 3. Gate history (world-registered IoU, band widths)

| Step | Front | Side (left) | Back | What changed |
|---|---|---|---|---|
| Blockout v1 | 0.850 | 0.845 | 0.866 | claws leaned inward (rotation sign bug) |
| Blockout v2 | 0.832 | 0.844 | 0.830 | lean fixed but 17 deg: tips overshot outward |
| Blockout v3 | 0.888 | 0.836 | 0.883 | lean 9 deg, talons curl in, wider rim |
| Axis fix | 0.888 | 0.852 | 0.883 | side axis from the base, not the bbox (medallion drags the bbox) |
| Blockout final | 0.908 | 0.876 | 0.907 | per-claw lean {0: 5, 45: 13, 90: 6, 135: 20}, band ellipse 0.88/0.95, tilted medallion |
| Forms | 0.898 | 0.847 | 0.876 | talons, knuckled fingers, lobed velvet, nugget, mole face, gems, dirt |

Accepted deviation: the drawn side view disagrees with the front about claw lean; every fix for
the side broke the front, so front and back were kept within tolerance and the side recorded
(claw-tip bands up to 0.08 short). The user judged the result "gorgeous" at this point.

## 4. What still separates it from the sheet

Painted outlines and hand shading (the model is flat colour), mole face detail, knuckle grooves
on the gold fingers, a faceted nugget, one material per MeshPart (velvet as glossy as the gold).
A second forms pass would take these on.
