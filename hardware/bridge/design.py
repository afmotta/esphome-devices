"""Single source of truth for the CAN bridge: components, nets, schematic and PCB placement."""

PROJECT = "bridgecan"

# Board size (mm)
W, H = 56.0, 36.0
OX, OY = 100.0, 100.0   # board origin in KiCad page coordinates

# ---------------------------------------------------------------------------
# Components
#   ref: (lib_id, value, footprint, {pin: net}, sch(x,y), pcb(x,y,rot), extra)
#   pcb coordinates are relative to the board's top-left corner.
# ---------------------------------------------------------------------------
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
PLUG4H = "Connector_Phoenix_MC:PhoenixContact_MC_1,5_4-G-3.5_1x04_P3.50mm_Horizontal"   # pluggable header, plug from the side
SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"

COMP = {}

def add(ref, lib, value, fp, pins, sch, pcb, mpn="", lcsc="", note=""):
    COMP[ref] = dict(lib=lib, value=value, fp=fp, pins=pins, sch=sch, pcb=pcb,
                     mpn=mpn, lcsc=lcsc, note=note)

_kefa = ("Presa per morsetto estraibile ad angolo 4 poli passo 3,5 mm, Kefa KF2EDGR-3.5-4P (THT); "
         "spina KF2EDGK-3.5-4P C440849 da ordinare a parte")

# --- Bus terminals -----------------------------------------------------------
# J1 backbone: 24 V + CAN, the only power input (same terminal and pin order as the 503 node)
add("J1", "Connector:Screw_Terminal_01x04", "BACKBONE 24V CAN", PLUG4H,
    {"4": "VBUS24", "3": "GND", "2": "CANH_A", "1": "CANL_A"}, (25.4, 45.72), (48.0, 29.0, 90),
    mpn=_kefa, lcsc="C441173")
# J2 zone segment on the opposite short edge (plug from the left): same 4-way plug, the 24 V position
# is not connected (the zone is powered on its own)
add("J2", "Connector:Screw_Terminal_01x04", "ZONA CAN", PLUG4H,
    {"1": None, "2": "GND", "3": "CANH_B", "4": "CANL_B"}, (25.4, 127.0), (8.0, 16.5, 270),
    mpn=_kefa, lcsc="C441173")

# Parts that appear only in the BOM (not on the PCB, no footprint, no CPL row): JLCPCB ships them with the boards.
#   ref: (value, footprint label, mpn, lcsc)
_plug = "Spina per morsetto estraibile 4 poli passo 3,5 mm, Kefa KF2EDGK-3.5-4P (non montata: spedita con i PCB)"
BOM_ONLY = {
    "P1": ("KF2EDGK-3.5-4P", "Spina 3,5 mm 4 poli (per J1)", _plug, "C440849"),
    "P2": ("KF2EDGK-3.5-4P", "Spina 3,5 mm 4 poli (per J2)", _plug, "C440849"),
}

# --- Power input protection + 5 V regulator (unchanged from the 503 node rev C) --------------
add("F1", "Device:Polyfuse", "PTC 0.5A 30V", "Fuse:Fuse_1812_4532Metric",
    {"1": "VBUS24", "2": "V24F"}, (55.88, 45.72), (41.6, 18.5, 180),
    mpn="PTC 1812 RUILON SMD1812P050TF/30 (0,5 A hold, 30 V)", lcsc="C12559")
add("D1", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123",
    {"1": "V24P", "2": "V24F"}, (76.2, 45.72), (35.0, 18.5, 0),
    mpn="B5819W (40 V 1 A) - protezione inversione polarita'", lcsc="C8598")
add("D2", "Device:D_TVS", "SMBJ26CA", "Diode_SMD:D_SMB",
    {"1": "V24P", "2": "GND"}, (96.52, 45.72), (34.4, 12.2, 0),
    mpn="SMBJ26CA TVS bidirezionale 26 V, SMB (hongjiacheng)", lcsc="C19077581")
add("C1", "Device:C_Polarized", "10uF 50V", "Capacitor_SMD:CP_Elec_5x5.4",
    {"1": "V24P", "2": "GND"}, (109.22, 45.72), (52.9, 10.5, 90),
    mpn="Honor Elec RVT1H100M0505, elettrolitico SMD 10 uF 50 V, D5x5.4 mm, 105 C", lcsc="C86603")
add("C2", "Device:C", "10uF 50V", C1206,
    {"1": "V24P", "2": "GND"}, (121.92, 45.72), (33.0, 15.6, 0),
    mpn="MLCC 10 uF 50 V X5R 1206 (Samsung CL31A106KBHNNNE)", lcsc="C13585")
add("U1", "Regulator_Switching:TSR_1-2450", "K7805-500R3", "Converter_DCDC:Converter_DCDC_TRACO_TSR-1_THT",
    {"1": "V24P", "2": "GND", "3": "+5V"}, (142.24, 45.72), (34.0, 6.6, 0),
    mpn="MORNSUN K7805-500R3 (6,5-36 V -> 5 V 0,5 A, SIP-3, pin 78xx)", lcsc="C86735")
add("C3", "Device:C", "10uF", C0805, {"1": "+5V", "2": "GND"}, (167.64, 45.72), (40.5, 10.6, 0),
    mpn="MLCC 10 uF 25 V 0805", lcsc="C15850")
add("C4", "Device:C", "100nF", C0603, {"1": "+5V", "2": "GND"}, (180.34, 45.72), (40.5, 12.6, 0),
    mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")
add("D3", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123",
    {"1": "5V_LDO", "2": "+5V"}, (205.74, 45.72), (45.6, 8.5, 0),
    mpn="B5819W - OR alimentazione LDO (da 5 V bus)", lcsc="C8598")
add("D5", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123",
    {"1": "5V_LDO", "2": "VBUS_PROG"}, (205.74, 60.96), (45.6, 10.8, 0),
    mpn="B5819W - OR alimentazione LDO (da USB di programmazione)", lcsc="C8598")
add("C13", "Device:C", "1uF", C0603, {"1": "5V_LDO", "2": "GND"}, (220.98, 45.72), (44.0, 13.0, 0),
    mpn="MLCC 1 uF 50 V X5R 0603 (Samsung CL10A105KB8NNNC)", lcsc="C15849")
add("U4", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
    {"1": "5V_LDO", "2": "GND", "3": "5V_LDO", "4": None, "5": "+3V3"}, (246.38, 45.72), (47.6, 13.75, 180),
    mpn="Diodes AP2112K-3.3TRG1 (LDO 600 mA)", lcsc="C51118")
add("C14", "Device:C", "1uF", C0603, {"1": "+3V3", "2": "GND"}, (271.78, 45.72), (44.0, 14.8, 0),
    mpn="MLCC 1 uF 50 V X5R 0603 (Samsung CL10A105KB8NNNC)", lcsc="C15849")
add("C15", "Device:C", "10uF", C0603, {"1": "+3V3", "2": "GND"}, (284.48, 45.72), (9.3, 9.6, 90),
    mpn="MLCC 10 uF 10 V X5R 0603 (Samsung CL10A106KP8NNNC), vicino al modulo", lcsc="C19702")
add("C16", "Device:C", "100nF", C0603, {"1": "+3V3", "2": "GND"}, (297.18, 45.72), (7.5, 9.6, 90),
    mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")

# --- CAN transceivers: A = backbone (TWAI0, can0), B = zone (TWAI1, can1) ----------------------
# U2 a little higher than on the 503 node; U5, its caps and the termination switch in the bottom band
# to the right of J5, D6 next to J2
def transceiver(u, c5v, c3v, esd, ch, sch_y, pos):
    (ux, uy, urot), (c5x, c5y), (c3x, c3y, c3r), (ex, ey, er) = pos
    add(u, "Interface_CAN_LIN:TJA1051T-3", "TJA1051T/3", SOIC8,
        {"1": f"CAN_TX_{ch}", "2": "GND", "3": "+5V", "4": f"CAN_RX_{ch}", "5": "+3V3",
         "6": f"CANL_{ch}", "7": f"CANH_{ch}", "8": "GND"}, (76.2, sch_y), (ux, uy, urot),
        mpn="NXP TJA1051T/3/1J", lcsc="C38695")
    add(c5v, "Device:C", "100nF", C0603, {"1": "+5V", "2": "GND"}, (106.68, sch_y), (c5x, c5y, 0),
        mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")
    add(c3v, "Device:C", "100nF", C0603, {"1": "+3V3", "2": "GND"}, (119.38, sch_y), (c3x, c3y, c3r),
        mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")
    add(esd, "Power_Protection:NUP2105L", "NUP2105L", "Package_TO_SOT_SMD:SOT-23",
        {"1": f"CANH_{ch}", "2": f"CANL_{ch}", "3": "GND"}, (139.7, sch_y), (ex, ey, er),
        mpn="onsemi NUP2105LT1G - ESD bus CAN 24 V", lcsc="C14486")

transceiver("U2", "C5", "C6", "D4", "A", 96.52, ((37.4, 24.4, 0), (36.1, 28.6), (39.6, 28.6, 0), (43.1, 27.1, 0)))
transceiver("U5", "C7", "C8", "D6", "B", 127.0, ((32.0, 32.8, 180), (32.0, 28.5), (29.0, 28.5, 0), (8.1, 32.9, 90)))

# --- 120 ohm terminations, switched per channel by a 2-way DIP switch (SW1: 1 = backbone, 2 = zone) ---
add("R1", "Device:R", "120", R0603, {"1": "CANH_A", "2": "TERM_A"}, (165.1, 96.52), (47.0, 34.0, 90),
    mpn="120 Ohm 1% 0603 (UNI-ROYAL 0603WAF1200T5E) - terminazione backbone", lcsc="C22787")
add("R2", "Device:R", "120", R0603, {"1": "CANH_B", "2": "TERM_B"}, (165.1, 127.0), (49.0, 34.0, 90),
    mpn="120 Ohm 1% 0603 (UNI-ROYAL 0603WAF1200T5E) - terminazione zona", lcsc="C22787")
add("SW1", "Switch:SW_DIP_x02", "TERM 120R",
    "Button_Switch_SMD:SW_DIP_SPSTx02_Slide_KingTek_DSHP02TS_W7.62mm_P1.27mm",
    {"1": "TERM_A", "4": "CANL_A", "2": "TERM_B", "3": "CANL_B"}, (190.5, 111.76), (40.9, 33.3, 0),
    mpn="DIP switch SMD 2 vie passo 1,27 mm, KINGTEK DSHP02TSGET - 1 = terminazione backbone, 2 = zona",
    lcsc="C40735")

# --- MCU ---------------------------------------------------------------------
mod = {"1": "GND", "28": "GND", "29": "GND", "2": "+3V3", "3": "EN",
       "13": "USB_DN", "14": "USB_DP", "10": "STRAP8", "15": "BOOT",
       "21": "CAN_TX_A", "20": "CAN_RX_A",     # GPIO23 / GPIO22 (as on the 503 node)
       "18": "CAN_TX_B", "17": "CAN_RX_B"}     # GPIO20 / GPIO19, right-hand pins (U5 is below the module's right corner)
for n in ["4", "5", "6", "7", "8", "9", "11", "12", "16", "19", "22", "23", "24", "25", "26", "27"]:
    mod[n] = None
MODX, MODY = 20.2, 15.9      # module origin; antenna keep-out flush with the top edge
add("U3", "bridgecan:ESP32-C6-WROOM-1", "ESP32-C6-WROOM-1-N8", "bridgecan:ESP32-C6-WROOM-1", mod,
    (345.44, 106.68), (MODX, MODY, 0), mpn="Espressif ESP32-C6-WROOM-1-N8", lcsc="C5366877")
add("R13", "Device:R", "10k", R0402, {"1": "+3V3", "2": "EN"}, (289.56, 86.36), (9.3, 12.4, 90),
    mpn="10 kOhm 1% 0402", lcsc="C25744")
add("C17", "Device:C", "1uF", C0402, {"1": "EN", "2": "GND"}, (302.26, 86.36), (7.8, 12.4, 90),
    mpn="MLCC 1 uF 25 V X5R 0402 (Samsung CL05A105KA5NQNC) - RC su EN", lcsc="C52923")
add("R14", "Device:R", "10k", R0402, {"1": "+3V3", "2": "STRAP8"}, (289.56, 111.76), (10.9, 27.9, 90),
    mpn="10 kOhm 1% 0402 (GPIO8 alto al boot)", lcsc="C25744")
add("J5", "Connector_Generic:Conn_01x06", "PROG USB", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    {"1": "VBUS_PROG", "2": "USB_DN", "3": "USB_DP", "4": "GND", "5": "BOOT", "6": "GND"}, (325.12, 185.42), (12.5, 34.2, 90),
    mpn="Pettine 1x6 2,54 mm (non montato): 5V, D-, D+, GND, BOOT, GND - ponticello 5-6 = download")

# power flags (schematic only)
FLAGS = [("#FLG01", "VBUS24", (200.66, 25.4)), ("#FLG02", "GND", (220.98, 25.4)),
         ("#FLG03", "V24P", (241.3, 25.4)), ("#FLG04", "5V_LDO", (261.62, 25.4)),
         ("#FLG05", "VBUS_PROG", (281.94, 25.4))]

NETCLASSES = {
    "Bus":   dict(track=0.6, clearance=0.25, nets=["VBUS24", "GND"]),
    "CAN":   dict(track=0.4, clearance=0.2, nets=["CANH_A", "CANL_A", "CANH_B", "CANL_B", "TERM_A", "TERM_B"]),
    "Power": dict(track=0.6, clearance=0.2, nets=["V24F", "V24P", "+5V", "5V_LDO", "VBUS_PROG", "+3V3"]),
}

SCH_TEXT = [
    ("BACKBONE: 24 V + CAN (unica alimentazione)", (17.78, 22.86)),
    ("ALIMENTAZIONE 24 V -> 5 V -> 3,3 V", (78.74, 30.48)),
    ("CAN A = BACKBONE (TWAI0: TX GPIO23, RX GPIO22)", (17.78, 82.55)),
    ("CAN B = ZONA (TWAI1: TX GPIO20, RX GPIO19); J2 pin 1 non collegato", (17.78, 107.95)),
    ("TERMINAZIONI 120 ohm: SW1-1 backbone, SW1-2 zona", (152.4, 87.63)),
    ("MCU ESP32-C6-WROOM-1: EN RC 10k/1uF, GPIO8 pull-up, BOOT=GPIO9 su J5", (284.48, 71.12)),
    ("PROGRAMMAZIONE: USB nativo (GPIO12/13) su J5, ponticello 5-6 = BOOT", (284.48, 175.26)),
]

# fixed copper placed before autorouting: (kind, ...)
# GND for the module's exposed pad (3x3 grid of pads "29"): tie the grid, via to the bottom plane
PREROUTE = []
_ex = [MODX - 2.75, MODX - 1.5, MODX - 0.26]
_ey = [MODY - 3.79, MODY - 2.54, MODY - 1.29]
for x in _ex:
    PREROUTE.append(("trk", x, _ey[0], x, _ey[2], "GND"))
for y in _ey:
    PREROUTE.append(("trk", _ex[0], y, _ex[2], y, "GND"))
PREROUTE += [("via", _ex[0], _ey[0], "GND"), ("via", _ex[2], _ey[0], "GND"),
             ("via", _ex[0], _ey[2], "GND"), ("via", _ex[2], _ey[2], "GND"), ("via", _ex[1], _ey[1], "GND")]

# parts whose body is flush with the board edge: allowed courtyard overhang (mm) in check_placement.py;
# gen_pcb.py clips their silk outline to the board
EDGE_OVERHANG = {"J1": 0.5, "J2": 0.5}

# decoupling caps whose GND pad gets a solid (non-thermal) pour connection
SOLID_GND = {"J5", "U1", "U2", "U5"}

# AP2112K: EN (pin 3) tied to VIN (pin 1) around the GND pin
_ux, _uy = 47.6, 13.75
PREROUTE += [("trk", _ux + 1.1375, _uy + 0.95, _ux + 2.35, _uy + 0.95, "5V_LDO"),
             ("trk", _ux + 2.35, _uy + 0.95, _ux + 2.35, _uy - 0.95, "5V_LDO"),
             ("trk", _ux + 2.35, _uy - 0.95, _ux + 1.1375, _uy - 0.95, "5V_LDO")]


# M2.5 mounting holes (board only, no schematic symbol): two, on the diagonal away from the antenna,
# centre 3 mm from the edges
HOLES = [(W - 3.0, 3.0), (3.0, H - 3.0)]
HOLE_FP = "MountingHole_2.7mm_M2.5"
HOLE_KEEPOUT_R = 2.8   # no tracks/vias/parts under the screw head (M2.5 pan head up to 5 mm)

# footprints mounted on the bottom side (none; gen_pcb.py flips them)
BOTTOM = set()


# EN (module pin 3) to the RC network R13/C17: fixed, the router leaves it open in the corner by J2
_en = (MODX - 8.75, MODY - 5.72)                           # module pad 3
_r13 = (COMP["R13"]["pcb"][0], COMP["R13"]["pcb"][1] - 0.51)  # R13 pin 2 (rotation 90: pin 1 down)
PREROUTE += [("trkn", _en[0], _en[1], 10.3, _en[1], "EN"), ("trkn", 10.3, _en[1], 10.3, _r13[1], "EN"),
             ("trkn", 10.3, _r13[1], _r13[0], _r13[1], "EN")]

# BOOT (module pin 15) to pin 5 of J5: via beside the pad, then on the back straight down to the header
_bt = (MODX + 8.75, MODY + 8.25)                           # module pad 15
_j5 = (COMP["J5"]["pcb"][0] + 4 * 2.54, COMP["J5"]["pcb"][1])
PREROUTE += [("trkn", _bt[0], _bt[1], _bt[0] + 1.45, _bt[1], "BOOT"), ("via", _bt[0] + 1.45, _bt[1], "BOOT"),
             ("trkb", _bt[0] + 1.45, _bt[1], _j5[0], _j5[1] - 2.3, "BOOT"), ("trkb", _j5[0], _j5[1] - 2.3, _j5[0], _j5[1], "BOOT")]

# CAN_TX_B (module pin 18) to U5 pin 1, which faces the corner between SW1 and the bottom edge:
# via beside the module pad, straight run on the back, via beside the transceiver pin
_tx = (MODX + 8.75, MODY + 4.44)                           # module pad 18
_u5 = (COMP["U5"]["pcb"][0] + 2.475, COMP["U5"]["pcb"][1] + 1.905)   # U5 pin 1 (rotation 180)
PREROUTE += [("trkn", _tx[0], _tx[1], _tx[0] + 1.45, _tx[1], "CAN_TX_B"), ("via", _tx[0] + 1.45, _tx[1], "CAN_TX_B"),
             ("trkb", _tx[0] + 1.45, _tx[1], _u5[0] + 1.475, _u5[1], "CAN_TX_B"),
             ("via", _u5[0] + 1.475, _u5[1], "CAN_TX_B"), ("trkn", _u5[0] + 1.475, _u5[1], _u5[0], _u5[1], "CAN_TX_B")]

# C17 GND pad: boxed in by C16, J2 and the module, the front pour cannot reach it -> via to the back plane
_c17 = (COMP["C17"]["pcb"][0], COMP["C17"]["pcb"][1] - 0.51)   # pin 2 (rotation 90: pin 1 down)
PREROUTE += [("trk", _c17[0], _c17[1], _c17[0] - 1.2, _c17[1], "GND"), ("via", _c17[0] - 1.2, _c17[1], "GND")]
