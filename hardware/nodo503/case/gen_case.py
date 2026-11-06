"""3D-printable enclosure for nodo503 (rev C): base + snap-on lid, generated from design.py.

Board size and mounting holes come from ../design.py; connector openings are sized from the
courtyards in ../nodo503.kicad_pcb, so the case follows the board when the board is regenerated.
Component heights are not in the KiCad project: they are the PARTS table below (check them with
calipers on the first assembled board).

Run from hardware/nodo503/case/:  python3 gen_case.py
Writes nodo503_case_base.stl, nodo503_case_lid.stl (both in print orientation) and the preview
anteprima_case.png, and fails if the case intersects any modelled part, plug or cable.

Requires: pip install manifold3d numpy matplotlib
"""
import math
import os
import re
import struct
import sys

import numpy as np
from manifold3d import Manifold

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import design  # noqa: E402

W, H = design.W, design.H
HOLES = design.HOLES

# ---------------------------------------------------------------------------
# Parameters (mm)
# ---------------------------------------------------------------------------
CL = 0.5          # board edge to inner wall
WALL = 1.8
FLOOR = 2.0
STANDOFF = 4.0    # floor to PCB bottom: THT pins stick out ~2 mm under the board
PCB_T = 1.6
TOP_CLEAR = 11.0  # PCB top to lid underside: K7805 (10 mm) is the tallest part
LID_T = 1.6
LIP_H = 2.0       # locating lip under the lid, inside the walls
LIP_T = 1.2
LIP_GAP = 0.2     # lip to wall clearance
BUMP_R = 0.5      # snap bump on the lip (sphere radius), 0.4 mm proud of the lip
BUMP_PROUD = 0.4
BOSS_D = 5.2      # under the 2.8 mm keepout radius of the holes
PILOT_D = 2.2     # M2.5 self-tapping into PLA/PETG (3.6 for an M2.5 heat-set insert)
POST_D = 3.2      # extra supports under the two corners without a screw
OPEN_MARGIN = 0.4 # extra clearance around connector openings
SEG = 48

PCB_Z0 = FLOOR + STANDOFF          # PCB bottom
PCB_Z1 = PCB_Z0 + PCB_T            # PCB top
BASE_TOP = PCB_Z1 + TOP_CLEAR      # top of the walls = lid underside
LID_TOP = BASE_TOP + LID_T

# inner cavity and outer box in board coordinates (x right, y down from the top-left corner)
IX0, IY0, IX1, IY1 = -CL, -CL, W + CL, H + CL
OX0, OY0, OX1, OY1 = IX0 - WALL, IY0 - WALL, IX1 + WALL, IY1 + WALL

# Modelled parts for the collision check: ref -> height above PCB top. Footprint = courtyard.
PARTS = {
    "U1": 10.0,   # MORNSUN K7805-500R3, measured 10 mm on the demo board (2026-11-06)
    "U3": 3.2,    # ESP32-C6-WROOM-1
    "C1": 5.6,    # electrolytic 5 x 5.4
    "J1": 8.6,    # Kefa KF2EDGR-3.5-4P (verify)
    "J2": 2.9,    # JST SM04B-SRSS-TB
    "J3": 6.0,    # JST B4B-PH-K-S
    "J4": 6.0,
    "U2": 1.8,
}
PLUG_J1_OUT = 11.0   # how far the KF2EDGK plug sticks out past the right edge
PLUG_J1_H = 9.5      # plug height above PCB top
QWIIC_H = 3.0        # SHR-04V housing thickness


# ---------------------------------------------------------------------------
# Courtyards from the generated PCB
# ---------------------------------------------------------------------------
def _blocks(s, key):
    out, idx = [], 0
    while (j := s.find("(" + key + " ", idx)) >= 0:
        d, k = 0, j
        while True:
            if s[k] == "(":
                d += 1
            elif s[k] == ")":
                d -= 1
                if d == 0:
                    break
            k += 1
        out.append(s[j:k + 1])
        idx = k + 1
    return out


def courtyards():
    """ref -> (x0, y0, x1, y1) of the F.CrtYd outline, board coordinates."""
    s = open(os.path.join(os.path.dirname(HERE), design.PROJECT + ".kicad_pcb")).read()
    res = {}
    for fp in _blocks(s, "footprint"):
        ref = re.search(r'\(fp_text reference "([^"]+)"', fp)   # KiCad 7 syntax
        at = re.search(r'\n\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', fp)
        if not ref or not at:
            continue
        x, y = float(at.group(1)) - design.OX, float(at.group(2)) - design.OY
        a = math.radians(-float(at.group(3) or 0))
        pts = []
        for g in _blocks(fp, "fp_line") + _blocks(fp, "fp_rect") + _blocks(fp, "fp_poly"):
            if "CrtYd" in g:
                pts += [(float(m.group(1)), float(m.group(2)))
                        for m in re.finditer(r'\((?:start|end|xy) ([-\d.]+) ([-\d.]+)\)', g)]
        if pts:
            t = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a))
                 for px, py in pts]
            res[ref.group(1)] = (min(p[0] for p in t), min(p[1] for p in t),
                                 max(p[0] for p in t), max(p[1] for p in t))
    return res


# ---------------------------------------------------------------------------
# Geometry helpers. 3D frame: X = x, Y = H - y (the board seen from above as in KiCad), Z up.
# ---------------------------------------------------------------------------
def box(x0, y0, x1, y1, z0, z1):
    """Box from board-coordinate rectangle and a Z range."""
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, H - y1, z0])


def cyl(x, y, d, z0, z1):
    return Manifold.cylinder(z1 - z0, d / 2, circular_segments=SEG).translate([x, H - y, z0])


def sphere(x, y, z, r):
    return Manifold.sphere(r, SEG // 2).translate([x, H - y, z])


def rounded_rect(x0, y0, x1, y1, z0, z1, r):
    core = box(x0 + r, y0, x1 - r, y1, z0, z1) + box(x0, y0 + r, x1, y1 - r, z0, z1)
    for cx, cy in [(x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)]:
        core += cyl(cx, cy, 2 * r, z0, z1)
    return core


def openings(cy):
    """Cuts shared by base and lid (assembly coordinates)."""
    m = OPEN_MARGIN
    cuts = []
    # J1: the plug goes in from the right edge; window from PCB top to the top of the wall
    j1 = cy["J1"]
    cuts.append(box(W - 2, j1[1] - m, OX1 + 1, j1[3] + m, PCB_Z1 - 0.3, LID_TOP + 1))
    # J2 Qwiic: opens towards the top edge (y = 0)
    j2 = cy["J2"]
    cuts.append(box(j2[0] - m, OY0 - 1, j2[2] + m, 1.0, PCB_Z1 - 0.3, BASE_TOP + 0.01))
    # J3/J4: PH cables leave upwards; slot through the lid, open towards the bottom edge so the
    # lid goes on with the cables plugged in
    x0 = min(cy["J3"][0], cy["J4"][0]) - m
    x1 = max(cy["J3"][2], cy["J4"][2]) + m
    y0 = min(cy["J3"][1], cy["J4"][1]) - m
    cuts.append(box(x0, y0, x1, OY1 + 1, BASE_TOP - LIP_H - 0.5, LID_TOP + 1))
    return cuts


def lip_gaps(cy):
    """Lip segments removed where a tall part sits at the board edge (U1 under the top lip)."""
    x0, y0, x1, y1 = cy["U1"]
    return [box(x0 - 0.5, OY0, x1 + 0.5, y1, BASE_TOP - LIP_H - 0.5, BASE_TOP + 0.01)]


def bumps():
    """Snap bumps on the lip, one per side, away from the openings: (x, y, outward normal)."""
    zc = BASE_TOP - LIP_H / 2
    lx0, ly0 = IX0 + LIP_GAP, IY0 + LIP_GAP
    lx1, ly1 = IX1 - LIP_GAP, IY1 - LIP_GAP
    return [(15.0, ly0, (0, -1)), (36.0, ly1, (0, 1)), (lx0, H / 2, (-1, 0)), (lx1, 7.0, (1, 0))], zc


def make_base(cy):
    outer = rounded_rect(OX0, OY0, OX1, OY1, 0, BASE_TOP, 1.5)
    inner = box(IX0, IY0, IX1, IY1, FLOOR, BASE_TOP + 1)
    b = outer - inner
    for hx, hy in HOLES:
        b += cyl(hx, hy, BOSS_D, FLOOR - 0.01, PCB_Z0)
    for px, py in [(2.0, 2.0), (W - 2.0, H - 1.8)]:   # antenna corner and J1 corner
        b += cyl(px, py, POST_D, FLOOR - 0.01, PCB_Z0)
    for hx, hy in HOLES:   # blind pilot, 0.6 mm of floor left
        b -= cyl(hx, hy, PILOT_D, 0.6, PCB_Z0 + 0.1)
    pts, zc = bumps()
    for x, y, (nx, ny) in pts:   # dimples for the lid bumps, same centre, 0.15 mm larger
        b -= sphere(x + nx * (BUMP_PROUD - BUMP_R), y + ny * (BUMP_PROUD - BUMP_R), zc, BUMP_R + 0.15)
    for c in openings(cy):
        b -= c
    return b


def make_lid(cy):
    lid = rounded_rect(OX0, OY0, OX1, OY1, BASE_TOP, LID_TOP, 1.5)
    lx0, ly0, lx1, ly1 = IX0 + LIP_GAP, IY0 + LIP_GAP, IX1 - LIP_GAP, IY1 - LIP_GAP
    lip = box(lx0, ly0, lx1, ly1, BASE_TOP - LIP_H, BASE_TOP + 0.01) - \
        box(lx0 + LIP_T, ly0 + LIP_T, lx1 - LIP_T, ly1 - LIP_T, BASE_TOP - LIP_H - 1, BASE_TOP + 1)
    pts, zc = bumps()
    for x, y, (nx, ny) in pts:
        lip += sphere(x + nx * (BUMP_PROUD - BUMP_R), y + ny * (BUMP_PROUD - BUMP_R), zc, BUMP_R)
    for g in lip_gaps(cy):
        lip -= g
    lid += lip
    # pry notch on the left edge, to lift the lid with a screwdriver
    lid -= box(OX0 - 1, H / 2 - 4, OX0 + 0.8, H / 2 + 4, BASE_TOP - 0.01, BASE_TOP + 0.6)
    for c in openings(cy):
        lid -= c
    return lid


def obstacles(cy):
    """Parts, plugs and cables that must not touch the case (assembly coordinates)."""
    obs = {"PCB": box(0, 0, W, H, PCB_Z0, PCB_Z1)}
    for ref, h in PARTS.items():
        x0, y0, x1, y1 = cy[ref]
        obs[ref] = box(max(x0, 0), max(y0, 0), min(x1, W), min(y1, H), PCB_Z1, PCB_Z1 + h)
    j1 = cy["J1"]
    obs["plug J1"] = box(W, j1[1] + 0.3, W + PLUG_J1_OUT, j1[3] - 0.3, PCB_Z1, PCB_Z1 + PLUG_J1_H)
    j2 = cy["J2"]
    obs["plug J2"] = box(j2[0] + 1.0, -8, j2[2] - 1.0, 1.0, PCB_Z1, PCB_Z1 + QWIIC_H)
    for ref in ("J3", "J4"):   # PHR-4 housing (8 mm with the cable) and the wires going up
        x0, y0, x1, y1 = cy[ref]
        obs[f"cavo {ref}"] = box(x0 + 0.5, y0 + 0.5, x1 - 0.5, min(y1, H) - 0.3, PCB_Z1, PCB_Z1 + 25)
    for hx, hy in HOLES:   # M2.5 pan head on the PCB, 5 mm
        obs[f"vite {hx:.0f},{hy:.0f}"] = cyl(hx, hy, 5.0, PCB_Z1, PCB_Z1 + 2.0)
    return obs


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    with open(path, "wb") as f:
        f.write(b"nodo503 case".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(t)))
        for a, b, c in t:
            p0, p1, p2 = v[a], v[b], v[c]
            n = np.cross(p1 - p0, p2 - p0)
            n = n / (np.linalg.norm(n) or 1)
            f.write(struct.pack("<12fH", *n, *p0, *p1, *p2, 0))


def preview(base, lid, obs, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    light = np.array([-0.4, -0.6, 0.7]) / np.linalg.norm([-0.4, -0.6, 0.7])

    def tris(m, color, dz=0.0):
        mesh = m.refine_to_length(1.2).to_mesh()   # small faces: matplotlib depth-sorts by face centroid
        v = np.asarray(mesh.vert_properties)[:, :3] + [0, 0, dz]
        t = v[np.asarray(mesh.tri_verts)]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        shade = 0.45 + 0.55 * np.clip(np.abs(n @ light), 0, 1)
        rgb = np.array(matplotlib.colors.to_rgb(color))
        return t, np.clip(rgb * shade[:, None], 0, 1)

    def obs_color(name):
        if name == "PCB":
            return "#2e7d32"
        return "#c62828" if name.startswith(("plug", "cavo")) else "#455a64"

    cut = box(OX0 - 5, H / 2, OX1 + 20, OY1 + 20, -1, 50)   # front half removed: section at mid-board
    views = [
        ("Fondo con scheda, parti e cavi", (40, -55), [(base, "#9fb3c8")], True),
        ("Assemblato", (30, -55), [(base, "#9fb3c8"), (lid, "#e0b878")], True),
        ("Sezione a metà scheda", (12, -80), [(base - cut, "#9fb3c8"), (lid - cut, "#e0b878")], "cut"),
        ("Coperchio, lato interno", (-55, -55), [(lid, "#e0b878")], False),
    ]
    fig = plt.figure(figsize=(14, 10), dpi=110)
    for i, (title, (el, az), parts, show_obs) in enumerate(views):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        polys, cols = [], []
        for m, c in parts:
            t, col = tris(m, c)
            polys.append(t)
            cols.append(col)
        if show_obs:
            for name, o in obs.items():
                t, col = tris(o - cut if show_obs == "cut" else o, obs_color(name))
                polys.append(t)
                cols.append(col)
        ax.add_collection3d(Poly3DCollection(np.concatenate(polys), facecolors=np.concatenate(cols),
                                             edgecolor="none"))
        ax.set_xlim(OX0 - 2, OX1 + PLUG_J1_OUT)
        ax.set_ylim(-9, H + 4)
        ax.set_zlim(-3, 30)
        ax.set_box_aspect((OX1 + PLUG_J1_OUT - OX0 + 2, H + 13, 33))
        ax.view_init(el, az)
        ax.set_title(title, fontsize=11)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path)


def main():
    cy = courtyards()
    base, lid = make_base(cy), make_lid(cy)

    clashes = []
    for name, o in obstacles(cy).items():
        if name == "PCB":   # the board must sit on the bosses and posts, not in the walls
            continue
        for part, m in (("fondo", base), ("coperchio", lid)):
            vol = (m ^ o).volume()
            if vol > 1e-3:
                clashes.append(f"{part} / {name}: {vol:.2f} mm3")
    pcb_clash = (base ^ box(0, 0, W, H, PCB_Z0 + 0.01, PCB_Z1)).volume() + (lid ^ box(0, 0, W, H, PCB_Z0, PCB_Z1)).volume()
    if pcb_clash > 1e-3:
        clashes.append(f"PCB: {pcb_clash:.2f} mm3")
    if (base ^ lid).volume() > 1e-3:
        clashes.append(f"fondo / coperchio: {(base ^ lid).volume():.2f} mm3")

    write_stl(base, os.path.join(HERE, "nodo503_case_base.stl"))
    # lid printed upside down: flat top on the bed
    write_stl(lid.rotate([180, 0, 0]).translate([0, 0, LID_TOP]), os.path.join(HERE, "nodo503_case_lid.stl"))
    preview(base, lid, obstacles(cy), os.path.join(HERE, "anteprima_case.png"))

    grip = PCB_T
    print(f"esterno {OX1 - OX0:.1f} x {OY1 - OY0:.1f} x {LID_TOP:.1f} mm "
          f"(+{PLUG_J1_OUT:.0f} mm di spina J1 sul lato destro)")
    print(f"viti: 2x M2,5 autofilettanti testa cilindrica, lunghezza 6 mm "
          f"(presa nella colonnina {6 - grip:.1f} mm su {PCB_Z0 - 0.6:.1f} mm di foro)")
    print(f"fondo {base.volume() / 1000:.1f} cm3, coperchio {lid.volume() / 1000:.1f} cm3")
    if clashes:
        print("INTERFERENZE:\n  " + "\n  ".join(clashes))
        sys.exit(1)
    print("interferenze: 0")


if __name__ == "__main__":
    main()
