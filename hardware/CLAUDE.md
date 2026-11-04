# CLAUDE.md — Nodo CAN 503 (rev C)

Contesto per le sessioni di Claude Code che riprendono questo progetto. Leggi questo file per intero prima di toccare qualcosa; i dettagli sono in [docs/pipeline.md](docs/pipeline.md) (come funzionano gli script) e [docs/decisioni.md](docs/decisioni.md) (perché il progetto è fatto così).

## Cos'è

PCB di un nodo per la domotica CAN di un fienile ristrutturato, da montare dietro i pulsanti in una scatola elettrica italiana **503**. Una sola scheda, revisione **C** (le rev A e B sono state abbandonate: non ricrearle).

- ESP32-C6-WROOM-1-N8 (Wi-Fi, ESPHome/OTA), TJA1051T/3 per il CAN (VIO a 3,3 V), 24 V dal bus → K7805-500R3 (5 V) → AP2112K-3.3.
- 6 ingressi pulsante (pull-up 3,3k, serie 1k, 100 nF) su due JST PH a 4 poli (1–3 e 4–6, ognuno con il suo GND), porta Qwiic senza pull-up, pettine di programmazione USB non montato.
- 55 × 33,5 mm, 2 strati, componenti solo sul lato superiore, 2 fori M2,5 in diagonale.
- Pensata per l'assemblaggio completo da JLCPCB (SMD + THT a onda).

L'utente è **Alberto**, scrive in **italiano**: rispondi in italiano. Documentazione e README sono in italiano; codice e commenti degli script in inglese.

## Regola fondamentale: il progetto è generato da script

`hardware/nodo503.kicad_sch` e `hardware/nodo503.kicad_pcb` sono **file generati**. Non modificarli a mano e non modificarli in KiCad GUI: la prossima esecuzione degli script li sovrascrive. Ogni modifica va fatta in:

- `hardware/design.py` — **unica fonte di verità**: componenti, net di ogni pin, posizioni su schema e PCB, codici LCSC, netclass, piste pre-sbrogliate, fori.
- `hardware/gen_sch.py`, `gen_pcb.py`, `route_import.py`, `gen_bom.py` — logica di generazione (serigrafie e posizioni dei riferimenti sono in `gen_pcb.py`).

Se l'utente modifica il PCB in KiCad e vuole conservare le modifiche, vanno riportate in `design.py`/`gen_pcb.py` (oppure si smette di rigenerare: chiedi prima).

## Comandi

Prerequisiti (una volta, Ubuntu 24.04): `sudo tools/setup.sh` — KiCad 7.0.x con modulo Python `pcbnew`, `kicad-cli`, Freerouting **1.9.0** in `tools/`, xvfb, Java, cairosvg.

Da `hardware/`:

| Quando | Comando | Cosa fa |
|---|---|---|
| Cambiano componenti, net, valori, testi dello schema | `python3 gen_sch.py` | Riscrive simbolo del modulo, lib-table, `.kicad_pro` (netclass/regole) e `.kicad_sch`. Va eseguito **prima** di `gen_pcb.py` se aggiungi componenti (crea l'UUID in `.comp_uuid.json`). |
| Cambiano piazzamento, footprint, net, contorno, keepout | `./route.sh` | Piazza da zero, esporta DSN, sbroglia con Freerouting (≈1 min, timeout 560 s), importa, versa le masse, DRC. Sovrascrive `nodo503.ses`. |
| Cambiano solo serigrafie/testi/attributi | `./build_pcb.sh` | Piazza da zero e reimporta lo sbroglio salvato `nodo503.ses` (riproducibile), DRC. **Non usarlo** se hai spostato componenti o cambiato net: lo sbroglio salvato non corrisponderebbe. |
| Sempre, alla fine | `./export.sh` | Controllo parità schema↔PCB, Gerber+foratura zip, BOM/CPL (completo e solo SMD), PDF dello schema, anteprime PNG in `out/`. |

Criteri di accettazione prima di consegnare o fare commit — tutti obbligatori:

1. `drc.py` (chiamato da `route.sh`/`build_pcb.sh`) stampa `Found 0 DRC violations` e `Found 0 unconnected pads`.
2. `export.sh` stampa `parita schema/PCB, discrepanze: 0`.
3. Guarda le anteprime `out/anteprima_lato_top.png` e `_bottom.png` (strumento Read sull'immagine): niente piste assurde, serigrafie leggibili e non sovrapposte alle etichette dei connettori.
4. `out/` è versionato: rigeneralo e committalo insieme alle modifiche agli script.

## Stato attuale (2026-10-19)

- DRC pulito, parità 0, pronto per l'ordine dopo le verifiche nell'anteprima JLCPCB (vedi README, "Da verificare prima dell'ordine").
- Connettori: J1 bus (presa estraibile ad angolo KF2EDGR-3.5-4P, spina laterale dal bordo destro, dall'alto 24V-GND-H-L; spina KF2EDGK-3.5-4P C440849 a parte), J3 pulsanti 1–3 + GND e J4 pulsanti 4–6 + GND (JST PH 4 poli verticale B4B-PH-K-S C131334, bordo inferiore sotto il modulo; i cavi PH crimpati si ordinano a parte, non sono in BOM; J4 serve solo con più di 3 pulsanti), J2 Qwiic (JST SH, bordo superiore), J5 pettine di programmazione 1×6 orizzontale in basso a destra (DNP; ponticello 5–6 = download).
- Pinout GPIO: vedi tabella nel README. Pulsanti 1–3 su GPIO7/0/1 (lato sinistro del modulo), 4–6 su GPIO20/19/18 (lato destro); CAN TX GPIO23, RX GPIO22; I²C SDA GPIO3, SCL GPIO2.
- Studio di compattazione del 2026-10-19 (`docs/decisioni.md`): applicato il concetto A, poi J3 diviso in due JST PH (55 × 33,5 mm); scartati il buck a 3,3 V con transceiver a 3,3 V (non convinceva Alberto) e il MINI-1 (esaurito). I pogo pin per la programmazione sono stati provati e tolti: J5 è di nuovo un pettine.
- Aperti / da fare: verifiche nell'anteprima JLCPCB; scarsa disponibilità di J2 (C160404); firmware ESPHome non ancora scritto (c'è solo l'esempio nel README).

## Mappa del PCB (mm, origine in alto a sinistra, y verso il basso)

- Modulo U3 in alto a sinistra (`MODX, MODY = 16.3, 15.9`), antenna a filo del bordo superiore: **nessun rame** davanti all'antenna (keepout nel footprint Espressif). Non spostare parti o piste in quella zona.
- Striscia sinistra (x 0–6.3): disaccoppiamento 3V3 (C15, C16), RC su EN (R13, C17), colonne RC dei pulsanti 1–3 (`btn_xy`), pull-up GPIO8 (R14) sotto.
- Subito sotto il modulo, sul bordo inferiore: J3 (x 6–17) e J4 (x 17–28), JST PH con le etichette dei pin sopra. A destra di J4, sul bordo inferiore: J5 orizzontale (pin 1 a x 30, y 31.7).
- Colonne RC dei pulsanti 4–6 a destra del modulo (x 27–31, y 20–27), con le piste BTN fisse in `PREROUTE`.
- Destra del modulo: U1 K7805 in alto, J2 Qwiic in alto a destra, D2/C2/C3/C4, gruppo LDO (D3, D5, C13, C14, U4), F1/D1 sulla riga di J1, U2 TJA1051 + C5/C6/D4 in basso; C1 (5 × 5,4 mm) in alto a destra, sopra J1.
- Fori M2,5 in alto a destra e in basso a sinistra, a 3 mm dai bordi (`HOLES`), keepout di raggio 2,8 mm per piste, via e componenti (`HOLE_KEEPOUT_R`, controllato anche da `check_placement.py`). L'angolo dell'antenna non ha fori.

## Vincoli e preferenze dell'utente (non violarli senza chiedere)

- Dimensione massima: **56 × 41 mm** (quella della CANBed RP2040); oggi 55 × 33,5 mm. Due viti **M2,5** in diagonale per un case stampato in 3D (scelta del 2026-10-19).
- Assemblaggio **completo** da JLCPCB ("non voglio montare nulla a mano"): ogni parte montata ha un codice LCSC; preferire Basic, poi Preferred, poi Extended. Esiste anche la variante solo SMD (BOM_SMD/CPL_SMD).
- Resta su **ESP32-C6** (scartato il C3: risparmio irrilevante). Zigbee non usato per ora.
- Nessuna terminazione 120 Ω a bordo. Un solo morsetto per il bus. Niente pull-up I²C (usa QwiicBus). Ingressi pulsante su due connettori da 4 poli (3 pulsanti + GND ciascuno): di solito si usa solo J3 (scelta del 2026-10-19). Nelle scatole dei pulsanti non ci sono 230 V (per questo vanno bene i fili sottili dei cavi PH).
- Lavora solo sulla rev C. Prima di rifare piazzamento/sbroglio per richieste ambigue o che toccano i vincoli, fai una domanda breve con le opzioni (l'utente risponde in fretta).
- Quando cerchi componenti, verifica stock e libreria su lcsc.com e jlcpcb.com/partdetail/Cxxxx e cita le fonti.

## Insidie note (risparmiano ore)

- **Freerouting**: usa la **1.9.0** con `xvfb-run` (senza display va in HeadlessException). La 2.x in headless produce percorsi a un solo punto. Non lanciare mai `pkill -f freerouting`: uccide anche la shell che lo invoca. Per la stessa DSN il risultato è deterministico; piccoli spostamenti cambiano molto l'esito. Se restano collegamenti aperti: sposta di poco i componenti coinvolti o aggiungi piste fisse in `PREROUTE` (esempio: bus +3V3 sulle colonne dei pull-up).
- **API pcbnew (KiCad 7)**: `board.Zones()` non è iterabile → `GetAreaCount()`/`GetArea(i)`. `ImportSpecctraSES` non è usabile → c'è un parser SES in `route_import.py`. L'angolo dei testi dei footprint è **relativo** alla rotazione del footprint (per un riferimento orizzontale su un footprint ruotato di `rot` usa `-rot`). Rotazione positiva = antioraria sullo schermo (y verso il basso).
- **Presa MC 1,5-G-3,5 orizzontale** (J1): a rotazione 0 l'imbocco della spina è verso +y (corpo da −1,2 a +8 mm dai pin); a 90° verso +x (bordo destro), per questo i pin stanno a x = 48 e il courtyard sporge 0,5 mm (`EDGE_OVERHANG` in `design.py`: `check_placement.py` lo tollera e `gen_pcb.py` ritaglia la serigrafia del contorno a 0,2 mm dal bordo). La numerazione dei pin di J1 è invertita apposta (pin 4 = 24V in alto).
- **Serigrafie nel DRC:** `silk_edge_clearance` è un errore; `silk_overlap` e `silk_over_copper` sono ignorate (riferimenti dei passivi nella zona fitta). Le etichette dei connettori le controlla `check_placement.py` (almeno 0,15 mm dai pad): eseguilo anche dopo aver toccato le serigrafie.
- **Starved thermal** su pad GND: aggiungi il riferimento a `SOLID_GND` in `design.py`.
- Fori di montaggio: footprint board-only, esclusi da BOM e CPL; le rule area attorno ai fori vengono esportate nella DSN come keepout.
- `gen_sch.py` è deterministico (UUID derivati con uuid5): a parità di `design.py` lo schema è identico byte per byte; lo stesso vale per il PCB prodotto da `build_pcb.sh` (generatore di UUID KiCad inizializzato con un seme). Un diff su `.kicad_sch`/`.kicad_pcb` quindi indica modifiche reali. Gli UUID dei simboli stanno in `.comp_uuid.json`: non cancellarlo, collega i simboli dello schema ai footprint del PCB.
- Lo sbroglio salvato (`nodo503.ses`) corrisponde allo stato attuale (rifatto con `route.sh` il 2026-10-19 per la scheda 55 × 33,5 con J3/J4 JST PH e il pettine J5): `build_pcb.sh` lo reimporta fedelmente.
- **Footprint sul retro** (`BOTTOM` in `design.py`, oggi vuoto: J5 è tornato un pettine sul lato superiore): `gen_pcb.py` li capovolge con `Flip` **dopo** `board.Add`; chiamare `Flip` su un footprint non ancora aggiunto alla scheda fa andare in crash pcbnew (segmentation fault). Dopo ogni modifica che richiede `route.sh` controlla DRC e anteprime come al solito.
- Rete del sandbox cloud: datasheet LCSC e API EasyEDA sono bloccati; le pagine prodotto di lcsc.com e jlcpcb.com/partdetail funzionano con WebFetch. Le pagine JLCPCB mostrano "Extended" anche per i Preferred. Alcuni codici esistono solo nel catalogo JLCPCB e non su LCSC (es. C42400616): verifica sempre entrambi.
- Elenco ufficiale Basic/Preferred: `scraped/assembly-details.csv` del repo GitHub CDFER/jlcpcb-parts-database (`base` = Basic, `expand` = Preferred). La classificazione usata è in `hardware/jlc_library.json` (aggiungi lì ogni nuovo codice).

## Bridge CAN (`bridge/`, dal 2026-10-31)

Seconda scheda, indipendente dal nodo: bridge tra backbone e segmento di zona con i due controller TWAI dell'ESP32-C6. Dettagli in [bridge/README.md](bridge/README.md).
- Stessa pipeline e stesse regole del nodo, ma in `bridge/hardware/`; il progetto si chiama `bridgecan`. Fonte di verità: `bridge/hardware/design.py`. Freerouting è in `../../tools/`.
- 56 × 36 mm. J1 backbone sul bordo destro, identico alla rev C; è l'unica alimentazione. J2 zona sul bordo sinistro, con la posizione dei 24 V non collegata. Terminazioni da 120 Ω attivate dal dip switch SW1: posizione 1 = backbone, 2 = zona. Pettine J5 non montato sul bordo inferiore.
- `EDGE_OVERHANG` e il ritaglio della serigrafia valgono qui per il bordo destro, il sinistro e l'inferiore.
- `gen_pcb.py` del bridge aggiunge una fascia di 0,6 mm lungo il contorno, vietata a piste e via (`EDGE_BAND`). Senza, Freerouting fa passare piste lungo il bordo e il DRC dà `copper_edge_clearance`.
- Firmware: profilo bridge di `afmotta/esphome-devices`. La bozza del file scheda è in `bridge/esphome/`.
- Le modifiche al nodo **non** si riportano automaticamente sul bridge, e viceversa.

## Git

- Repository GitHub `afmotta/can-bus-node` (privato), branch principale `main`. Contiene solo l'ultima iterazione; la storia precedente è riassunta in `docs/decisioni.md`.
- Branch **`variante/kefa`**: la stessa scheda con il morsetto estraibile Kefa a 7 poli per i pulsanti (55 × 37 mm), conservata come variante il 2026-10-19. Non viene aggiornata con le modifiche di `main`: se serve, riportale a mano e rifai `route.sh`.
- Committa script, file KiCad generati e `hardware/out/` insieme, dopo aver soddisfatto i criteri di accettazione. Messaggi di commit in italiano, brevi, che dicano cosa cambia sulla scheda.
- Aggiorna `docs/decisioni.md` (nuova voce datata) e, se cambia qualcosa per l'utente, il README.
