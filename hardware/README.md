# hardware/ — PCB dei nodi CAN

Sorgenti KiCad delle schede del bus CAN della casa. Ogni scheda è **generata da script Python** (`design.py` è l'unica fonte di verità): i file `.kicad_*` non si modificano a mano. I file di produzione per JLCPCB (Gerber, BOM, CPL, anteprime) sono versionati in `out/` di ciascuna scheda.

| Scheda | Cartella | Cos'è | Dimensioni | Firmware |
|---|---|---|---|---|
| **Nodo CAN 503** (rev C) | [`nodo503/`](nodo503/README.md) | Nodo da scatola 503: 6 ingressi pulsante, Qwiic, ESP32-C6, 24 V + CAN su un morsetto estraibile | 55 × 33,5 mm | profilo `buttons-c6`, [`boards/esp32-c6-nodo503.yaml`](../boards/esp32-c6-nodo503.yaml) |
| **Bridge CAN** (rev A) | [`bridge/`](bridge/README.md) | Bridge store-and-forward tra backbone e segmento di zona, due controller TWAI dell'ESP32-C6 | 56 × 36 mm | profilo `bridge-c6`, [`boards/bridge-c6-twai.yaml`](../boards/bridge-c6-twai.yaml) |

Il contesto architetturale (profili dei nodi, topologia segmentata del bus) è in [ADR-0005](../docs/adr/0005-can-bus-topology-segmented-multi-bus.md), [ADR-0017](../docs/adr/0017-node-profiles-and-canbed-bridge.md) e [ADR-0025](../docs/adr/0025-esp32-c6-node-and-bridge-boards.md); il protocollo in [`canbus/`](../canbus/CLAUDE.md).

## Struttura

```
hardware/
├── nodo503/     # progetto KiCad "nodo503": script, .kicad_*, .ses, out/, firmware/ (bring-up)
├── bridge/      # progetto KiCad "bridgecan": stessa struttura
├── docs/
│   ├── pipeline.md    # come funzionano gli script e come rigenerare tutto
│   └── decisioni.md   # storia e motivazioni delle scelte (voci datate, per scheda)
├── tools/setup.sh     # installa KiCad 7, Freerouting 1.9.0, xvfb, Java, cairosvg
└── CLAUDE.md          # regole per le sessioni di Claude Code (italiano)
```

Le due schede hanno ciascuna la propria copia degli script (stessa struttura, differenze di nome del progetto e di dettagli di piazzamento): una correzione a uno script va portata a mano sull'altra.

## Rigenerare una scheda

Una sola volta, dalla radice del repo (Ubuntu 24.04):

```bash
sudo hardware/tools/setup.sh
```

Poi, dalla cartella della scheda:

```bash
cd hardware/nodo503   # oppure hardware/bridge
python3 gen_sch.py    # se cambiano componenti, net, valori
./route.sh            # se cambiano piazzamento o net (sbroglio con Freerouting, ≈1 min)
./build_pcb.sh        # se cambiano solo serigrafie: reimporta lo sbroglio salvato
./export.sh           # sempre alla fine: parità schema/PCB, Gerber, BOM/CPL, PDF, PNG
```

Criteri di accettazione (DRC 0, parità 0, anteprime controllate) e dettagli in [CLAUDE.md](CLAUDE.md) e [docs/pipeline.md](docs/pipeline.md).

## Cosa è versionato

- Sì: `design.py` e gli altri script, i `.kicad_*` generati, `<progetto>.ses` (sbroglio salvato), `.comp_uuid.json`, `jlc_library.json`, `out/` (tranne `out/gerber/`).
- No (vedi `.gitignore`): `*.dsn`, `*.net`, `drc.rpt`, `logs/`, `out/gerber/`, backup di KiCad, il jar di Freerouting, `firmware/secrets.yaml`.

`hardware/` non è coperto dalla CI né da `scripts/verification-battery.sh`: i controlli si fanno a mano.
