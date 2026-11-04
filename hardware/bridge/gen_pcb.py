"""Place footprints for bridgecan (unrouted board)."""
import json, os, pcbnew
from design import *

ROOT = os.path.dirname(os.path.abspath(__file__))
FPROOT = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
MM = pcbnew.FromMM
pcbnew.KIID.SeedGenerator(504)   # deterministic UUIDs -> reproducible .kicad_pcb
def P(x, y): return pcbnew.VECTOR2I(int(round((OX + x) * 1000)) * 1000, int(round((OY + y) * 1000)) * 1000)

REF_POS = {"J1": (52.5, 34.2), "J2": (3.2, 9.0), "U1": (34.0, 2.4),   # (x, y[, angle on the board])
           "C1": (49.3, 10.5, 90), "D3": (42.6, 8.4), "J5": (10.0, 31.2), "U5": (32.0, 29.9)}
HIDE_REF = {"SW1"}   # the switch legend below names it
comp_uuid = json.load(open(f"{ROOT}/.comp_uuid.json"))
path = f"{ROOT}/{PROJECT}.kicad_pcb"
if os.path.exists(path):
    os.remove(path)
board = pcbnew.NewBoard(path)

# nets
nets = {}
for c in COMP.values():
    for n in c["pins"].values():
        if n and n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni)
            nets[n] = ni

for ref, c in COMP.items():
    lib, name = c["fp"].split(":")
    libpath = f"{ROOT}/bridgecan.pretty" if lib == "bridgecan" else f"{FPROOT}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(libpath, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref)
    fp.SetValue(c["value"])
    fp.SetPath(pcbnew.KIID_PATH(f"/{comp_uuid[ref]}"))
    x, y, rot = c["pcb"]
    fp.SetPosition(P(x, y))
    fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        if ref in SOLID_GND and c['pins'].get(pad.GetNumber()) == 'GND':
            pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        n = c["pins"].get(pad.GetNumber())
        if n:
            pad.SetNet(nets[n])
    r = fp.Reference()
    if (ref[0] in 'RC' and c['fp'].endswith('0402_1005Metric')) or ref in HIDE_REF:
        r.SetVisible(False)
    r.SetTextSize(pcbnew.VECTOR2I(MM(0.7), MM(0.7)))
    r.SetTextThickness(MM(0.12))
    if ref in REF_POS:      # keep the designator away from the pin legends
        rx, ry, *ang = REF_POS[ref]
        r.SetPosition(P(rx, ry)); r.SetTextAngleDegrees((ang[0] if ang else 0) - rot)   # FP text angle is relative to the footprint
    if ref in EDGE_OVERHANG:   # body flush with the edge: clip the silk outline so it stays on the board
        xmin, xmax, ymax = MM(OX + 0.2), MM(OX + W - 0.2), MM(OY + H - 0.2)
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() == "MTEXT":
                continue
            s, e = g.GetStart(), g.GetEnd()
            s.x, e.x = max(min(s.x, xmax), xmin), max(min(e.x, xmax), xmin)   # J1 on the right edge, J2 on the left
            s.y, e.y = min(s.y, ymax), min(e.y, ymax)
            g.SetStart(s); g.SetEnd(e); g.SetLocalCoord()   # FP_SHAPE saves its footprint-local coords
    board.Add(fp)
    if ref in BOTTOM:          # pads-only footprints on the back (flip top/bottom keeps the pad order along x)
        fp.Flip(fp.GetPosition(), False)

# outline with rounded corners
R = 1.5
def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
def arc(cx, cy, sx, sy, ang):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(P(cx, cy)); s.SetStart(P(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
seg(R, 0, W - R, 0); seg(W, R, W, H - R); seg(W - R, H, R, H); seg(0, H - R, 0, R)
arc(R, R, 0, R, 90); arc(W - R, R, W - R, 0, 90); arc(W - R, H - R, W, H - R, 90); arc(R, H - R, R, H, 90)

# antenna keep-out comes with the Espressif module footprint

# mounting holes (NPTH, board-only) + no-track/no-via area under the screw head
import math
for k, (hx, hy) in enumerate(HOLES, 1):
    fp = pcbnew.FootprintLoad(f"{FPROOT}/MountingHole.pretty", HOLE_FP)
    fp.SetFPID(pcbnew.LIB_ID("MountingHole", HOLE_FP))
    fp.SetReference(f"H{k}"); fp.SetValue(HOLE_FP.split("_")[-1]); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    fp.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
    fp.SetPosition(P(hx, hy)); board.Add(fp)
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowFootprints(False); z.SetZoneName(f"VITE_H{k}")
    o = z.Outline(); o.NewOutline()
    for a in range(0, 360, 15):
        o.Append(P(hx + HOLE_KEEPOUT_R * math.cos(math.radians(a)), hy + HOLE_KEEPOUT_R * math.sin(math.radians(a))))
    board.Add(z)

# no tracks/vias in a 0.6 mm band along the outline: Freerouting does not know the 0.3 mm copper-to-edge
# rule and otherwise runs tracks along the bottom edge
EDGE_BAND = 0.6
for k, (x0, y0, x1, y1) in enumerate([(0, 0, W, EDGE_BAND), (0, H - EDGE_BAND, W, H),
                                       (0, 0, EDGE_BAND, H), (W - EDGE_BAND, 0, W, H)]):
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowFootprints(False); z.SetZoneName(f"BORDO_{k}")
    o = z.Outline(); o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(P(x, y))
    board.Add(z)

# silkscreen legends
def text(t, x, y, size=0.8, rot=0, layer=pcbnew.F_SilkS, mirror=False, width=None, right=False):
    tx = pcbnew.PCB_TEXT(board); tx.SetText(t); tx.SetPosition(P(x, y)); tx.SetLayer(layer)
    tx.SetTextSize(pcbnew.VECTOR2I(MM(width or size), MM(size))); tx.SetTextThickness(MM(size * 0.15))
    tx.SetTextAngleDegrees(rot)
    if right: tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)   # x is the right end of the text
    if mirror: tx.SetMirrored(True)
    board.Add(tx)
x0, y0, _ = COMP["J1"]["pcb"]
for k, t in enumerate(["24V", "GND", "H", "L"]):      # J1 on the right edge, top to bottom
    # right-aligned 0.2 mm short of the pads (x0 - 1.8); "L" also clear of the pin-1 marker;
    # narrow glyphs so "24V" fits between F1 and J1
    text(t, x0 - 2.0 - (0.85 if t == "L" else 0), y0 - 10.5 + 3.5 * k, 0.6, width=0.45, right=True)
text("BACKBONE", 52.4, 14.9, 0.6, width=0.45)
x0, y0, _ = COMP["J2"]["pcb"]      # J2 on the left edge, top to bottom; the "24V" position is not connected
# no room for per-pin legends between the pads and the module: pin order above the terminal
text("ZONA", 3.2, 10.4, 0.6, width=0.45)
text("NC/G/H/L", 3.2, 11.8, 0.6, width=0.45)
x0, y0, _ = COMP["SW1"]["pcb"]     # termination switch: position 1 = backbone, 2 = zone
text("SW1: 1 BB  2 ZONA", x0, y0 - 3.3, 0.55, width=0.45)
x0, y0, _ = COMP["J5"]["pcb"]      # horizontal header on the bottom edge: legends above the pins
for k, t in enumerate(["5V", "D-", "D+", "G", "BT", "G"]):
    text(t, x0 + 2.54 * k, y0 - 2.0, 0.55)
text("BRIDGE CAN", 16.3, 17.5, 1.0, layer=pcbnew.B_SilkS, mirror=True)        # on the back, under the module
text("ESP32-C6 + 2x TJA1051T/3", 16.3, 19.2, 0.7, layer=pcbnew.B_SilkS, mirror=True)
text(f"rev A - {W:g} x {H:g} mm", 16.3, 20.6, 0.7, layer=pcbnew.B_SilkS, mirror=True)

# pre-routed GND tie for the TJA1051 / C5 pocket (too tight for the pour to reach a via)
def trk(x1, y1, x2, y2, net, w=0.3, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(board); t.SetStart(P(x1, y1)); t.SetEnd(P(x2, y2)); t.SetWidth(MM(w))
    t.SetLayer(layer); t.SetNet(nets[net]); board.Add(t)
def via(x, y, net):
    v = pcbnew.PCB_VIA(board); v.SetPosition(P(x, y)); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[net]); board.Add(v)
for pre in PREROUTE:
    if pre[0] == "via":
        via(*pre[1:])
    elif pre[0] == "trkn":
        trk(*pre[1:], w=0.2)
    elif pre[0] == "trkb":
        trk(*pre[1:], w=0.25, layer=pcbnew.B_Cu)
    else:
        trk(*pre[1:])

# auxiliary origin at the board's bottom-left corner: Gerber/drill and CPL share it (y up)
board.GetDesignSettings().SetAuxOrigin(P(0, H))
pcbnew.SaveBoard(path, board)
print("saved", path)
