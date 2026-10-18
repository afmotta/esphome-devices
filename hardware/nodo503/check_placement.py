"""Placement sanity check: courtyard overlaps, parts outside the board, silk legends too close to pads. Run from hardware/ after gen_pcb.py."""
import itertools, pcbnew
from design import W, H, OX, OY, EDGE_OVERHANG

b = pcbnew.LoadBoard("nodo503.kicad_pcb")
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
    xmax = W + EDGE_OVERHANG.get(fp.GetReference(), 0) + 0.01   # flush-mounted connectors: courtyard margin overhangs
    if x0 < -0.2 or y0 < -0.2 or x1 > xmax or y1 > H + 0.01:   # antenna keep-out may touch the edge
        print("outside", fp.GetReference(), round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)); bad += 1
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
