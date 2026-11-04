"""Placement sanity check: courtyard overlaps, parts outside the board or under the screws, silk legends too close to pads. Run from the project folder (hardware/nodo503/ or hardware/bridge/) after gen_pcb.py."""
import itertools, pcbnew
from design import W, H, OX, OY, EDGE_OVERHANG, HOLES, HOLE_KEEPOUT_R

b = pcbnew.LoadBoard("bridgecan.kicad_pcb")
fps = list(b.GetFootprints())
bad = 0
for a, c in itertools.combinations(fps, 2):
    A, C = a.GetCourtyard(pcbnew.F_CrtYd), c.GetCourtyard(pcbnew.F_CrtYd)
    if A.OutlineCount() and C.OutlineCount() and A.Collide(C, 0):
        print("overlap", a.GetReference(), c.GetReference()); bad += 1
for fp in fps:
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetX()) - OX, pcbnew.ToMM(bb.GetRight()) - OX
    y0, y1 = pcbnew.ToMM(bb.GetY()) - OY, pcbnew.ToMM(bb.GetBottom()) - OY
    ov = EDGE_OVERHANG.get(fp.GetReference(), 0)   # flush-mounted connectors: courtyard margin overhangs
    if x0 < -0.2 - ov or y0 < -0.2 or x1 > W + ov + 0.01 or y1 > H + ov + 0.01:   # antenna keep-out may touch the edge
        print("outside", fp.GetReference(), round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)); bad += 1
# nothing under the screw heads: courtyards (either side) clear of the hole keep-out circles
for fp in fps:
    if fp.GetReference().startswith("H"):
        continue
    for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        cy = fp.GetCourtyard(layer)
        if not cy.OutlineCount():
            continue
        for hx, hy in HOLES:
            c = pcbnew.VECTOR2I(pcbnew.FromMM(OX + hx), pcbnew.FromMM(OY + hy))
            if cy.Collide(c, pcbnew.FromMM(HOLE_KEEPOUT_R)):
                print("under screw", fp.GetReference(), hx, hy); bad += 1
# board-level legends (gen_pcb.py) must keep clear of pads: JLCPCB clips silk on exposed copper
GAP = pcbnew.FromMM(0.15)
pads = [(f.GetReference(), p.GetNumber(), p.GetBoundingBox()) for f in fps for p in f.Pads()]
for d in b.GetDrawings():
    if d.GetClass() != "PCB_TEXT" or d.GetLayer() != pcbnew.F_SilkS:
        continue
    tb = d.GetBoundingBox()
    for ref, num, pb in pads:
        pb = pcbnew.BOX2I(pb.GetPosition(), pb.GetSize()); pb.Inflate(GAP)
        if tb.Intersects(pb):
            print("legend on pad", repr(d.GetText()), ref, num); bad += 1
print("problems", bad)
