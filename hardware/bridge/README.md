# Bridge CAN – ESP32-C6-WROOM-1 (rev A)

Scheda per unire due segmenti del bus CAN (backbone e zona) con un bridge store-and-forward, in sostituzione della LilyGO T-2CAN. Usa i **due controller TWAI** dell'ESP32-C6, quindi non serve l'MCP2515: entrambi i lati sono gestiti a interrupt con code del driver. Il firmware è il profilo bridge di [afmotta/esphome-devices](https://github.com/afmotta/esphome-devices) (`canbus/packages/bridge.yaml`); qui c'è solo l'hardware e la bozza del file scheda per ESPHome.

È nata dal nodo 503 rev C (cartella `hardware/` di questo repository): stesso modulo, stessa catena di alimentazione, stesso transceiver e stessa pipeline a script. Per ora è un progetto separato; l'eventuale unione con il nodo si valuterà più avanti.

- **Dimensioni:** 56 × 36 mm (entro i 56 × 41 mm della CANBed RP2040), 2 strati, componenti solo sul lato superiore
- **Fissaggio:** 2 fori M2,5 in diagonale (in alto a destra e in basso a sinistra), centro a 3 mm dai bordi: interasse **50 × 30 mm**; keepout di 2,8 mm come sul nodo
- **Montaggio:** completo da JLCPCB (SMD + THT), stessa logica del nodo
- **Uso previsto:** scatola di derivazione o quadro (variante "A": solo bridge, niente pulsanti)

## Connettori

I due morsetti stanno sui **lati corti opposti**.

- **J1 BACKBONE (bordo destro):** identico al nodo rev C. Presa Kefa KF2EDGR-3.5-4P ad angolo, spina KF2EDGK-3.5-4P (C440849) di lato da destra. Dall'alto: **24V – GND – CAN-H – CAN-L**. È l'**unica alimentazione** della scheda.
- **J2 ZONA (bordo sinistro):** stessa presa e stessa spina, innesto da sinistra. Dall'alto: **NC – GND – CAN-H – CAN-L**. La posizione dei 24 V **non è collegata**: la zona si alimenta per conto suo, e il bridge non passa i 24 V da un segmento all'altro. Le masse dei due segmenti sono invece collegate tra loro (bus non isolati, come già previsto nell'ADR-0017). Accanto ai pin non c'è spazio per le etichette: l'ordine è scritto sopra il morsetto ("ZONA NC/G/H/L").
- **J5 PROG (bordo inferiore, sotto il modulo):** pettine 1×6 non montato, come sul nodo: 5V, D−, D+, GND, BOOT, GND; ponticello 5–6 = download. Sul bridge è l'**unico accesso** a log e firmware (niente Wi-Fi né OTA, per l'ADR-0005).

Spine da ordinare: due KF2EDGK-3.5-4P (righe P1 e P2 della BOM, spedite con i PCB).

## Terminazioni da 120 Ω

Una resistenza da 120 Ω per canale (R1 backbone, R2 zona, 0603, C22787 Basic), inserita da un **dip switch SMD a 2 vie** (SW1, KINGTEK DSHP02TSGET, C40735):

| SW1 | Terminazione |
|---|---|
| 1 | backbone (tra CANH_A e CANL_A) |
| 2 | zona (tra CANH_B e CANL_B) |

Accendi la posizione solo se il bridge è a un estremo di quel segmento. La serigrafia sotto lo switch riporta "TERM 120R: 1 BB 2 ZONA"; il lato ON è stampato sul corpo dello switch. La corrente è di circa 17 mA, dentro i 25 mA dello switch.

Se per un errore di cablaggio CANH finisce sui 24 V, la resistenza da 120 Ω dissipa circa 5 W e brucia, mentre il TJA1051 regge fino a ±58 V.

## Circuito

- **Alimentazione:** identica al nodo rev C, da J1 (PTC 0,5 A, diodo contro l'inversione, TVS SMBJ26CA, K7805-500R3, AP2112K-3.3, OR a diodi con il 5 V del pettine USB).
- **CAN A (backbone):** U2 TJA1051T/3, ESD D4 NUP2105L, collegato a TWAI0.
- **CAN B (zona):** U5 TJA1051T/3, ESD D6 NUP2105L, collegato a TWAI1.
- **Modulo:** ESP32-C6-WROOM-1-N8, RC su EN, pull-up su GPIO8, BOOT su J5, come sul nodo.

## Pinout

| Funzione | GPIO | Pin modulo |
|---|---|---|
| CAN A TX (backbone, `can0`) | GPIO23 | 21 |
| CAN A RX (backbone, `can0`) | GPIO22 | 20 |
| CAN B TX (zona, `can1`) | GPIO20 | 18 |
| CAN B RX (zona, `can1`) | GPIO19 | 17 |
| USB D− / D+ (J5) | GPIO12 / GPIO13 | 13 / 14 |
| BOOT (J5 pin 5) | GPIO9 | 15 |

## Firmware

Il file scheda è `boards/bridge-c6-twai.yaml` (profilo `bridge-c6` del registry, ADR-0025); la fixture di compilazione è `canbus/tests/compile_bridge_c6.yaml`. In breve:

- due voci `esp32_can`, `can0` per il backbone e `can1` per la zona;
- `bridge_hf_loop: "false"`, perché entrambi i lati sono a interrupt;
- watchdog e brownout fissati come sulla T-2CAN;
- nessuna radio.

Dalla versione 2026.8.0, ESPHome assegna a ogni voce `esp32_can` il controller TWAI successivo, nell'ordine in cui sono dichiarate (`controller_id = next_twai_ctrl_num++` in `esp32_can.cpp`).

In `esphome-devices` restano da aggiungere a mano la riga del profilo in `generate_nodes.py` e un test di compilazione (`canbus/tests/compile_bridge_c6.yaml`). `bridge.yaml`, `bridge_forwarding.h` e `node_core.yaml` non cambiano.

## Da verificare prima dell'ordine

1. **Codici LCSC.** La rete del sandbox non raggiunge lcsc.com e jlcpcb.com, quindi stock e classe dei componenti nuovi sono verificati solo tramite motori di ricerca:
   - **C40735** (DSHP02TSGET): presente su LCSC, classe Extended perché assente dall'elenco Basic/Preferred;
   - **C22787** (0603WAF1200T5E): Basic.

   Gli altri codici sono quelli del nodo rev C.
2. **Footprint di SW1.** È il footprint KiCad `SW_DIP_SPSTx02_Slide_KingTek_DSHP02TS_W7.62mm_P1.27mm`. Va confrontato con quello EasyEDA di C40735 e con il lato ON nell'anteprima JLCPCB.
3. **Rotazioni nel CPL.**
   - J2 è ruotato di 270° (imbocco verso sinistra): controlla che il modello 3D JLCPCB abbia l'imbocco sul bordo sinistro.
   - U5 è ruotato di 180°; D6 di 90°; C1 di 90°.
   - Il resto come sul nodo (J1 a 90°, U4 a 180°).
4. **Via nel pad di massa del modulo** e **fori dei morsetti** (1,2 mm): come sul nodo, vedi il README principale.

## Disposizione

- **In alto a sinistra:** condensatori del 3,3 V e RC su EN.
- **Bordo sinistro:** J2 zona, con D6 (ESD della zona) subito sotto.
- **Sotto il modulo:** J5.
- **In alto a destra:** K7805, gruppo LDO e C1.
- **A destra del modulo:** U2 backbone con F1 e D1, sulla riga di J1.
- **Fascia in basso a destra:** U5 zona con C7/C8, dip switch SW1 e le due resistenze da 120 Ω, sotto J1.

Le piste CAN della zona attraversano la scheda da J2 a U5 e SW1, circa 35 mm: a 125 kbit/s non è un problema.

Alcune piste sono fisse in `PREROUTE` perché Freerouting le lasciava aperte:
- EN verso R13;
- BOOT verso J5, sul retro;
- CAN_TX_B verso U5, sul retro;
- via di massa di C17.

Lungo tutto il contorno c'è una fascia di 0,6 mm senza piste né via (`EDGE_BAND` in `gen_pcb.py`): Freerouting non conosce la regola dei 0,3 mm dal bordo.

## File e comandi

La pipeline è la stessa del nodo (vedi [docs/pipeline.md](../docs/pipeline.md)), ma lavora in `hardware/bridge/` con il progetto `bridgecan`:

| Percorso | Cosa contiene |
|---|---|
| `hardware/design.py` | Fonte di verità: componenti, net, posizioni |
| `hardware/bridgecan.kicad_*` | Progetto KiCad generato (non modificarlo a mano) |
| `hardware/bridgecan.ses` | Sbroglio salvato (Freerouting 1.9.0) |
| `hardware/out/` | Gerber, BOM/CPL (completo e solo SMD), PDF dello schema, anteprime |

```bash
cd hardware/bridge && python3 gen_sch.py && ./route.sh && ./export.sh
```

Stato al 2026-10-31: DRC 0 violazioni e 0 collegamenti mancanti, parità schema/PCB 0, `check_placement.py` 0 problemi.
