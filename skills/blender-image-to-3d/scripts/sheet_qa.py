#!/usr/bin/env python3
"""Check a generated orthographic reference sheet and crop it into per-view references.

Plain Python 3 + Pillow (+ numpy if present, faster). Finds the subject panels on the flat
background by the empty gaps between them, compares their heights, ground lines and widths, and on
PASS writes one crop per view that shares a single scale and ground line, with the subject mask in
the alpha channel (usable directly as a world_gate.py matte). Exit 1 on any FAIL.

    python3 scripts/sheet_qa.py --sheet PR_Crown/ref/sheet_v1.png --views front,side,back \
      --out PR_Crown/ref --json PR_Crown/review/00_sheet_qa.json --height 0.35

Options worth knowing:
  --height H        real height of the subject in metres: prints m-per-px, axis-col and ground-row
                    per crop for world_gate.py
  --expect-ratio    width ratios the brief knows, e.g. side:front=0.62 (5% tolerance)
  --symmetric       also check left/right symmetry of the front view
  --trim-shadow     treat faint grey (low-saturation, near-background) pixels as background
  --force           write crops even when checks fail (for a hand-accepted sheet; record why)
"""
import argparse
import json
import os
import sys

from PIL import Image

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


def mask_of(img, tol, trim_shadow):
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    border = [px[x, 0] for x in range(0, w, 4)] + [px[x, h - 1] for x in range(0, w, 4)] + \
             [px[0, y] for y in range(0, h, 4)] + [px[w - 1, y] for y in range(0, h, 4)]
    bg = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    dist_border = [max(abs(c[i] - bg[i]) for i in range(3)) for c in border]
    noise = sorted(dist_border)[int(len(dist_border) * 0.95)]
    if np is not None:
        a = np.asarray(rgb).astype(np.int16)
        d = np.abs(a - np.array(bg, dtype=np.int16)).max(axis=2)
        m = d > tol
        if trim_shadow:
            sat = a.max(axis=2) - a.min(axis=2)
            lum = a.mean(axis=2)
            shadow = (sat < 14) & (lum < sum(bg) / 3) & (d < tol * 3)
            m &= ~shadow
        return m, bg, noise
    m = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            d = max(abs(c[i] - bg[i]) for i in range(3))
            if d > tol:
                if trim_shadow and max(c) - min(c) < 14 and sum(c) / 3 < sum(bg) / 3 and d < tol * 3:
                    continue
                m[y][x] = True
    return m, bg, noise


def col_counts(m, h, w):
    if np is not None:
        return m.sum(axis=0).tolist()
    return [sum(1 for y in range(h) if m[y][x]) for x in range(w)]


def bbox(m, x0, x1, h):
    if np is not None:
        sub = m[:, x0:x1]
        rows = np.where(sub.any(axis=1))[0]
        cols = np.where(sub.any(axis=0))[0]
        if len(rows) == 0:
            return None
        return (x0 + int(cols[0]), int(rows[0]), x0 + int(cols[-1]) + 1, int(rows[-1]) + 1, int(sub.sum()))
    ys = [y for y in range(h) if any(m[y][x] for x in range(x0, x1))]
    xs = [x for x in range(x0, x1) if any(m[y][x] for y in range(h))]
    if not ys:
        return None
    n = sum(1 for y in range(h) for x in range(x0, x1) if m[y][x])
    return (xs[0], ys[0], xs[-1] + 1, ys[-1] + 1, n)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--views", default="front,side,back", help="panel names left to right")
    ap.add_argument("--out", help="folder for the per-view crops (ref/)")
    ap.add_argument("--json")
    ap.add_argument("--tol", type=int, default=28, help="background colour tolerance 0-255")
    ap.add_argument("--gap", type=float, default=0.006, help="min empty gap between panels, fraction of width")
    ap.add_argument("--height", type=float, default=0.0, help="real subject height in metres")
    ap.add_argument("--height-tol", type=float, default=0.03)
    ap.add_argument("--ground-tol", type=float, default=0.02)
    ap.add_argument("--width-tol", type=float, default=0.05)
    ap.add_argument("--expect-ratio", action="append", default=[], help="a:b=r width ratio, repeatable")
    ap.add_argument("--symmetric", action="store_true")
    ap.add_argument("--trim-shadow", action="store_true")
    ap.add_argument("--margin", type=float, default=0.04, help="crop margin, fraction of subject height")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    img = Image.open(a.sheet)
    w, h = img.size
    views = [v.strip() for v in a.views.split(",") if v.strip()]
    m, bg, noise = mask_of(img, a.tol, a.trim_shadow)
    fails, warns = [], []
    fh, fw = max(2, int(h * 0.03)), max(2, int(w * 0.03))
    if np is not None:
        frame = np.concatenate([m[:fh].ravel(), m[-fh:].ravel(), m[:, :fw].ravel(), m[:, -fw:].ravel()])
        frame_frac = float(frame.mean())
    else:
        cells = [m[y][x] for y in list(range(fh)) + list(range(h - fh, h)) for x in range(w)]
        frame_frac = sum(cells) / len(cells)
    if noise > a.tol * 0.6 or frame_frac > 0.01:
        fails.append(f"background not flat: {frame_frac:.1%} of the outer frame differs from the background "
                     f"(noise, floor, gradient, vignette or a subject touching the edge)")

    counts = col_counts(m, h, w)
    base = sorted(counts)[len(counts) // 10]  # background level: low percentile, panels may fill most columns
    thresh = max(2, int(h * 0.002), base * 3)
    occupied = [c >= thresh for c in counts]
    gap = max(3, int(w * a.gap))
    runs, x = [], 0
    while x < w:
        if occupied[x]:
            s = x
            last = x
            while x < w and (occupied[x] or (x - last) < gap):
                if occupied[x]:
                    last = x
                x += 1
            runs.append((s, last + 1))
        else:
            x += 1
    boxes = [b for b in (bbox(m, s, e, h) for s, e in runs) if b]
    if boxes:
        big = max(b[4] for b in boxes)
        dropped = [b for b in boxes if b[4] < big * 0.03]
        boxes = [b for b in boxes if b[4] >= big * 0.03]
        if dropped:
            warns.append(f"ignored {len(dropped)} specks (text, dust or stray marks?)")
    panels = [{"x0": b[0], "y0": b[1], "x1": b[2], "y1": b[3], "w": b[2] - b[0], "h": b[3] - b[1],
               "pixels": b[4]} for b in boxes]
    if len(panels) != len(views):
        fails.append(f"found {len(panels)} panels, expected {len(views)} ({', '.join(views)})")

    named = dict(zip(views, panels))
    # plan views (top, bottom) show depth vertically: they are checked against the elevations'
    # widths instead of sharing the height and ground-line checks
    PLAN = {"top", "plan", "bottom"}
    elev = [v for v in views if v not in PLAN]
    if len(panels) == len(views) and elev:
        hs = [named[v]["h"] for v in elev]
        hmed = sorted(hs)[len(hs) // 2]
        spread = (max(hs) - min(hs)) / hmed
        if spread > a.height_tol:
            tall = elev[hs.index(max(hs))]
            fails.append(f"panel heights differ by {spread:.1%} (> {a.height_tol:.0%}); tallest: {tall}")
        grounds = [named[v]["y1"] for v in elev]
        gspread = (max(grounds) - min(grounds)) / hmed
        if gspread > a.ground_tol:
            fails.append(f"ground lines differ by {gspread:.1%} of height (> {a.ground_tol:.0%})")
        for pv in [v for v in views if v in PLAN]:
            t = named[pv]
            if "front" in named and abs(t["w"] - named["front"]["w"]) / named["front"]["w"] > a.width_tol:
                fails.append(f"{pv} view width {t['w']} does not match front width {named['front']['w']}")
            if "side" in named and abs(t["h"] - named["side"]["w"]) / named["side"]["w"] > a.width_tol:
                fails.append(f"{pv} view depth {t['h']} does not match side width {named['side']['w']}")
        for v, p in named.items():
            if p["x0"] <= 1 or p["x1"] >= w - 1 or p["y0"] <= 1 or p["y1"] >= h - 1:
                fails.append(f"{v} panel touches the image edge (cropped subject?)")
        if "front" in named and "back" in named:
            fw, bw = named["front"]["w"], named["back"]["w"]
            d = abs(fw - bw) / max(fw, bw)
            if d > a.width_tol:
                fails.append(f"front/back widths differ by {d:.1%} (> {a.width_tol:.0%})")
        for spec in a.expect_ratio:
            try:
                pair, r = spec.split("=")
                va, vb = pair.split(":")
                r = float(r)
                got = named[va]["w"] / named[vb]["w"]
                if abs(got - r) / r > 0.05:
                    fails.append(f"width ratio {va}:{vb} is {got:.3f}, brief expects {r:.3f}")
            except (KeyError, ValueError, ZeroDivisionError):
                warns.append(f"could not evaluate --expect-ratio {spec}")
        if a.symmetric and "front" in named:
            p = named["front"]
            if np is not None:
                sub = m[p["y0"]:p["y1"], p["x0"]:p["x1"]]
                mir = sub[:, ::-1]
                inter = (sub & mir).sum()
                union = (sub | mir).sum()
                asym = 1 - inter / union if union else 0
            else:
                asym = 0
                warns.append("symmetry check needs numpy")
            if asym > 0.08:
                fails.append(f"front view asymmetric: mirror IoU loss {asym:.1%} (> 8%)")

    report = {"sheet": os.path.abspath(a.sheet), "size": [w, h], "background": bg,
              "border_noise": noise, "views": views, "panels": named if len(panels) == len(views) else panels,
              "fails": fails, "warns": warns, "crops": {}}

    if a.out and len(panels) == len(views) and (not fails or a.force):
        os.makedirs(a.out, exist_ok=True)
        top = min(named[v]["y0"] for v in elev)
        ground = max(named[v]["y1"] for v in elev)
        sub_h = ground - top
        mg = int(sub_h * a.margin)
        y0, y1 = max(0, top - mg), min(h, ground + mg)
        rgba = img.convert("RGBA")
        if np is not None:
            alpha = Image.fromarray((m * 255).astype("uint8"), "L")
        else:
            alpha = Image.new("L", (w, h))
            alpha.putdata([255 if m[y][x] else 0 for y in range(h) for x in range(w)])
        rgba.putalpha(alpha)
        for v, p in named.items():
            x0, x1 = max(0, p["x0"] - mg), min(w, p["x1"] + mg)
            if v in PLAN:
                crop = rgba.crop((x0, max(0, p["y0"] - mg), x1, min(h, p["y1"] + mg)))
                path = os.path.join(a.out, f"{v}.png")
                crop.save(path)
                report["crops"][v] = {"file": path, "size": list(crop.size), "plan_view": True}
                continue
            crop = rgba.crop((x0, y0, x1, y1))
            path = os.path.join(a.out, f"{v}.png")
            crop.save(path)
            # axis: centre of the subject's base (rows 2-8% of height above the ground), not the
            # bbox centre, which a part sticking out one side (an emblem, a nose, a handle) drags off
            cs = []
            for yy in range(max(0, ground - int(sub_h * 0.08)), ground - int(sub_h * 0.02)):
                if np is not None:
                    xs = np.where(m[yy, p["x0"]:p["x1"]])[0]
                    if len(xs):
                        cs.append((xs[0] + xs[-1]) / 2 + p["x0"])
            base_axis = sorted(cs)[len(cs) // 2] if cs else (p["x0"] + p["x1"]) / 2
            info = {"file": path, "size": list(crop.size), "ground_row": ground - y0,
                    "axis_col": round(base_axis - x0, 1),
                    "bbox_axis_col": round((p["x0"] + p["x1"]) / 2 - x0, 1)}
            if a.height > 0:
                info["m_per_px"] = round(a.height / sub_h, 7)
            report["crops"][v] = info

    for x in warns:
        print("WARN", x)
    for x in fails:
        print("FAIL", x)
    for v, p in (named.items() if len(panels) == len(views) else []):
        print(f"{v:6s} box {p['x0']},{p['y0']} to {p['x1']},{p['y1']}  w {p['w']}  h {p['h']}")
    for v, c in report["crops"].items():
        if c.get("plan_view"):
            print(f"crop {c['file']}  (plan view, not a world_gate matte)")
            continue
        extra = f"  m-per-px {c['m_per_px']}" if "m_per_px" in c else ""
        print(f"crop {c['file']}  ground-row {c['ground_row']}  axis-col {c['axis_col']}{extra}")
    print(f"sheet_qa: panels {len(panels)}/{len(views)}, WARN {len(warns)}, FAIL {len(fails)}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(report, open(a.json, "w"), indent=2)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
