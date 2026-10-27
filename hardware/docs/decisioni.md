# Decisioni e storia del progetto

Registro delle scelte fatte con Alberto, con il motivo. Le voci più recenti sono in fondo. Quando cambi qualcosa di sostanziale, aggiungi una voce datata.

## Requisiti di partenza (ottobre 2026)

- Nodo per la domotica CAN del fienile, montato **dietro i pulsanti in una scatola 503**: legge 6 pulsanti e comunica sul bus CAN (125 kbit/s nell'esempio ESPHome).
- Alimentazione dai **24 V del bus**, regolati a 5 V; transceiver **TJA1051** (Alberto aveva un modulo AliExpress; si è scelto il chip TJA1051T/3 in SOIC-8 con VIO a 3,3 V, che rende inutile la resistenza da 4,7 kΩ su RXD degli schemi ESPHome).
- **Niente terminazione 120 Ω** a bordo (il bus si termina agli estremi). **Un solo morsetto** per 24 V + CAN (la continuità verso i nodi successivi si fa fuori dalla scheda).
- Progetto in **KiCad**. Inizialmente al massimo 5 × 5 cm; poi esteso a 56 × 41 mm (vedi sotto).

## Evoluzione

1. **Rev A — XIAO ESP32-C6 (abbandonata).** Modulo Seeed XIAO su pin header, regolatore TRACO TSR 1-2450 scartato perché costoso → **MORNSUN K7805-500R3** (switching, pin 7805). Aggiunta porta **Qwiic**. Lo XIAO non è nel catalogo JLCPCB: va montato a mano.
2. **Rev B — ESP32-C6-MINI-1 (abbandonata).** Modulo saldato direttamente per l'assemblaggio completo JLCPCB, ma il MINI-1 non era a magazzino.
3. **Rev C — ESP32-C6-WROOM-1-N8 (attuale).** Modulo a magazzino (C5366877), più grande: scheda 48 × 44 mm con tutti i componenti su un lato. Aggiunti LDO AP2112K-3.3 e "OR" a diodi (D3, D5) per alimentare il modulo dal pettine USB senza 24 V; RC su EN e pull-up su GPIO8 come da Espressif; pettine di programmazione 1×6 con pin BOOT (ponticello 5–6 = download).
4. **Librerie JLCPCB.** Sostituzioni dirette verso parti Basic dove possibile; tutto in BOM con codice LCSC ("non voglio montare nulla a mano"), THT inclusi (saldatura a onda). Creata anche la variante solo SMD.
5. **ESP32-C3 valutato e scartato.** Zigbee non serve, ma il risparmio sarebbe ~0,50 €/scheda: non vale la perdita di capacità.
6. **Revisione di un esperto.** `cleanup.py` per micro-segmenti e sovrapposizioni, coordinate arrotondate a 1 µm, verifica dei pad dei ponticelli e dell'ingresso fili di J1.
7. **Solo rev C.** Rev A e B abbandonate: non vanno più mantenute.
8. **Morsetto del bus.** Il codice C42400616 (Kefa KF350) esiste solo nel catalogo JLCPCB e non su LCSC → **DORABO DB125-3.5-4P-GN-S (C2757925)**, stesso passo e footprint. *(Superata dalla 15: J1 ora è una presa estraibile Kefa.)*
9. **56 × 41 mm con 4 fori M3.** Richiesta: fori agli angoli per un case stampato in 3D, senza superare la **CANBed RP2040 (56 × 41 mm)**. La vecchia 48 × 44 superava già i 41 mm in altezza, quindi la scheda è stata ridisposta: modulo in alto a sinistra, J1 sul bordo destro, pulsanti sul bordo inferiore. Fori a 3,5 mm dai bordi (interasse 49 × 34 mm), keepout piste/via di 3,3 mm.
10. **Tolti i pull-up I²C** opzionali (R + ponticelli a saldare): Alberto usa il **QwiicBus**, che li ha già.
11. **GPIO riassegnati** per sbrogliare meglio: pulsanti 1–3 sul lato sinistro del modulo, 4–6 sul destro, CAN TX/RX scambiati per allinearli ai pin 1 e 4 del TJA1051. Risultato: meno via, retro quasi tutto massa.
12. **Connettore dei pulsanti.** La scheda sta dietro i pulsanti, quindi servono fili che entrano **dall'alto** e un modo rapido per staccarla: scelto il **morsetto estraibile verticale** (presa KF2EDGV-3.5 + spina a vite KF2EDGK-3.5). Scartato il push-in KF141V-2.54 (alto 13,6 mm, footprint a due file non verificabile, fili solo sottili). Poi passati da 2 × 4 poli a **un 7 poli con un solo GND** (un'unica spina, niente rischio di scambiare le spine, 6 mm in meno). Rischio: magazzino basso (presa 485, spina 234 al 2026-10-14); riserva = due 4 poli, ma richiede di rifare il PCB.
13. **Filo consigliato per i pulsanti:** cordina 0,5 mm² (corrente ~1 mA, vedi voce del 2026-10-18); isolamento adatto ai 230 V se condivide scatola o tubi con la rete.
14. **Designatori rinumerati** senza buchi (J1 bus, J2 pulsanti, J3 Qwiic, J4 programmazione; R13 EN, R14 GPIO8) e riferimenti J1/J2 spostati lontano dalle etichette dei pin.
15. **J1 estraibile (2026-10-16).** Su richiesta di Alberto il morsetto a vite del bus è diventato un **morsetto estraibile ad angolo**: presa Kefa KF2EDGR-3.5-4P (C441173, 7 295 pz su LCSC al 2026-10-18) + spina KF2EDGK-3.5-4P (C440849, 12 196 pz, da ordinare a parte). Scelto l'innesto orizzontale (fili sempre dal bordo destro) invece del verticale come J2: lo stock è molto più alto e il piazzamento cambia poco. Footprint Phoenix MC 1,5/4-G-3,5 orizzontale, pin a x = 48 mm per avere il fronte della presa a filo del bordo; spostati di poco F1 (−1 mm) e D4 (−0,3 mm), etichette dei pin a sinistra dei pad, pad GND di U2 collegato pieno (`SOLID_GND`) per un thermal incompleto. Risbrogliato con `route.sh`.

## Scelte tecniche che non vanno cambiate senza motivo

| Scelta | Perché |
|---|---|
| TJA1051T/3 con VIO a 3,3 V | Uscita RXD già a 3,3 V, niente partitore; pin S a GND (modalità normale). |
| K7805-500R3 + AP2112K | 5 V per il transceiver, 3,3 V puliti per il modulo; il K7805 regge fino a 36 V in ingresso. |
| PTC 0,5 A, SS34, SMBJ26CA, NUP2105L | Protezione da sovracorrente, inversione, sovratensione sul 24 V e ESD sulle linee CAN. |
| RC sui pulsanti (3,3k / 1k / 100 nF) | Filtro dei disturbi sulle linee lunghe verso i pulsanti; antirimbalzo fine in ESPHome (`delayed_on_off`). |
| Antenna a filo del bordo superiore, keepout Espressif | Prestazioni Wi-Fi; nessun rame e nessun componente davanti all'antenna. |
| Fori M3 non metallizzati | Case in plastica; la testa della vite poggia su massa coperta da solder mask. Vite in nylon consigliata nel foro vicino all'antenna. |
| Freerouting 1.9.0 | Unica versione che funziona headless in questo ambiente (vedi CLAUDE.md). |

## Punti aperti

- Verifiche nell'anteprima di assemblaggio JLCPCB: rotazioni (U3, U2, U4, J1, J2, J3, diodi, C1), orientamento del corpo di J1 (fili dal bordo destro), lato dell'incastro di J2, via-in-pad tappate sotto il modulo.
- Diametro dei fori di J1 e J2 (1,2 mm nei footprint Phoenix) da confrontare con i footprint EasyEDA delle prese Kefa.
- J3 (JST SH, C160404) ha pochi pezzi: alternative C7430446, C2845363, C18077910 (da confrontare col footprint).
- Firmware ESPHome da scrivere (c'è solo l'esempio nel README).
- Case stampato in 3D da progettare (2 fori M2,5, interasse 49 × 27,5 mm, altezza massima componenti ≈ 11 mm per K7805 e morsetti; la spina di J2 sporge di più; la spina di J1 sporge di circa 1 cm oltre il bordo destro).

## 2026-10-18 — Origine ausiliaria e testi Qwiic

- **Origine ausiliaria** del PCB nell'angolo in basso a sinistra (`gen_pcb.py`). `export.sh` ora esporta Gerber e foratura con quell'origine (`--use-drill-file-origin`, `--drill-origin plot`): prima erano in coordinate assolute (scheda a 100,100) mentre il CPL è relativo all'angolo in basso a sinistra con Y verso l'alto, quindi i due file non coincidevano. Ora Gerber, foratura e CPL hanno la stessa origine.
- Corretti i testi dello schema e il commento in `design.py`: I²C è SDA=GPIO3, SCL=GPIO2 (restavano GPIO20/21 di una revisione precedente).

## 2026-10-18 — Serigrafie di J1 e controlli

- **Etichette dei pin di J1** (24V, GND, H, L): allineate a destra 0,2 mm prima dei pad, caratteri più stretti (0,45 × 0,6 mm) perché "24V" stia tra F1 e J1. Prima "24V" toccava il pad e "GND" lo copriva per 0,1 mm: JLCPCB avrebbe tagliato le lettere.
- **Contorno serigrafato di J1** ritagliato a 0,2 mm dal bordo destro (usciva di 0,11 mm). Vale per ogni componente in `EDGE_OVERHANG` (`design.py`), che sostituisce l'eccezione scritta a mano per J1 in `check_placement.py`.
- **Riferimento di U1** spostato dentro il corpo del K7805: era fuori dal bordo superiore.
- **Controlli:** la regola DRC `silk_edge_clearance` passa da ignorata a errore; `check_placement.py` segnala le etichette dei connettori a meno di 0,15 mm da un pad. `silk_overlap` e `silk_over_copper` restano ignorate: segnalano riferimenti dei passivi nella zona fitta a destra del modulo, già presenti prima.
- README: nota sulla catena del bus (due fili per polo nella spina di J1, la scheda si stacca senza interrompere il bus), magazzino aggiornato, verifica del diametro dei fori.

## 2026-10-18 — Pull-up dei pulsanti da 10k a 3,3k

- **R1–R6 da 10 kΩ a 3,3 kΩ** (UNI-ROYAL 0402WGF3301TCE, C25890, Basic). Motivo: con 10k nel contatto passavano ~0,3 mA, poco per i contatti in argento dei pulsanti da rete, che invecchiando possono dare falsi contatti; con 3,3k passa ~1 mA. A 3,3 V resta comunque un "circuito secco": è un miglioramento, non una cura.
- Un contatto viene ancora letto come chiuso fino a ~1,1 kΩ di resistenza (soglia bassa 0,825 V; con 10k era ~3,3 kΩ). Assorbimento solo a pulsante premuto (max ~6 mA con tutti premuti). Filtro invariato (1k × 100 nF).
- Stesso footprint 0402 e stesse piste: PCB rigenerato con `build_pcb.sh` sullo sbroglio salvato. R13 (EN) e R14 (GPIO8) restano 10k.

## 2026-10-19 — Scheda più compatta: 55 × 37 mm (concetto A)

- **Studio.** Misurati i courtyard della scheda 56 × 41: il modulo WROOM-1 occupa il 23 % della superficie, J2 il 10 %, J1 l'8 %, il K7805 il 4 %; i 18 passivi 0402 dei pulsanti solo 31 mm². Valutati tre concetti: A (stessa elettronica, 55 × 37), B (buck 24 → 3,3 V e transceiver a 3,3 V, circa 50 × 36), C (B + ESP32-C6-MINI-1, circa 45 × 32). **Scelto A.** B scartato da Alberto (un convertitore da progettare e un transceiver diverso; il TCAN334 proposto all'inizio era sbagliato perché regge solo ±14 V sul bus, l'alternativa giusta sarebbe stata il TCAN3414). C scartato: MINI-1 esaurito.
- **Fori:** da 4 × M3 negli angoli a **2 × M2,5** in diagonale (alto a destra, basso a sinistra), centro a 3 mm dai bordi, keepout 2,8 mm per piste, via e componenti. L'angolo dell'antenna resta senza vite.
- **J4:** il pettine 1×6 (mai montato) diventa sei piazzole Ø 1,6 mm sul retro, sotto il modulo, a passo 2,54 mm, per una maschera a pogo pin. Stesso ordine dei segnali. Libera la striscia sinistra.
- **Pulsanti:** i gruppi RC diventano tre colonne per lato (C in alto verso massa, R serie, pull-up in basso), 1–3 nella striscia sinistra e 4–6 a destra del modulo; J2 sale subito sotto il modulo. Le piste BTN tra colonne e modulo sono fisse in `PREROUTE` (le colonne lontane passano sul retro): con il primo piazzamento Freerouting faceva girare BTN1 per 54 mm tra i pin di J2.
- **D1:** SS34 (SMA) → **B5819W** (SOD-123, C8598, Basic, già in BOM). 1 A basta con il PTC da 0,5 A.
- **C1:** 22 µF Ø 6,3 → **10 µF 50 V Ø 5 × 5,4** (Honor Elec RVT1H100M0505, C86603, Extended come il precedente). Con C2 da 10 µF resta capacità sufficiente all'ingresso del K7805.
- Pinout GPIO invariato. `check_placement.py` ora segnala anche componenti sotto le teste delle viti. Risbrogliato con `route.sh`: DRC 0, collegamenti aperti 0, parità 0.
- Le pagine prodotto di LCSC e JLCPCB erano bloccate dal proxy della sessione: lo stock di C86603 (circa 6 000 pezzi) viene da un risultato di ricerca, da ricontrollare al caricamento della BOM.

## 2026-10-19 — J2 diviso in due JST PH a 4 poli: 55 × 33,5 mm

- **Motivo.** La presa Kefa a 7 poli era profonda 8,2 mm sulla scheda e, con la spina innestata, era il componente più alto (stima 16–20 mm; il K7805 è 10,4 mm). Ogni filo veniva poi serrato due volte, sul frutto e nella spina. Alberto di solito usa 3 pulsanti, solo a volte 6.
- **Scelta.** Due JST PH 2 mm a 4 poli verticali (B4B-PH-K-S, C131334, circa 95 000 pezzi su LCSC dalla ricerca): **J2** = pulsanti 1–3 + GND, **J5** = pulsanti 4–6 + GND, affiancati sotto il modulo. Profondi 5,5 mm, alti 6 mm, 8 mm con il cavo: il componente più alto torna il K7805. Scheda da 55 × 37 a **55 × 33,5 mm**. C1 spostato in alto a destra, sopra J1. Pinout GPIO invariato.
- **Compromessi accettati.** Fili fino a 0,2 mm² (AWG 24) con puntale da 0,25 mm² nei morsetti a vite dei frutti Vimar Linea; aggancio solo per attrito; cavi da crimpare o comprare già crimpati; un GND per gruppo invece di un solo comune. I fili sottili (isolamento tipico 300 V) vanno bene perché **nelle scatole dei pulsanti non ci sono 230 V**.
- **Scartati.** JST XH (fili fino a 0,33 mm², ma due connettori da 13,4 mm non stanno sotto il modulo: scheda a circa 35 mm); morsetto estraibile a passo 2,5 mm (guadagno di circa 1 mm e stesso rischio di magazzino del 7 poli).
- Risbrogliato con `route.sh` al primo tentativo: DRC 0, collegamenti aperti 0, parità 0.

## 2026-10-19 — Torna il pettine di programmazione

- Alberto non vuole programmare con i pogo pin: J4 torna un **pettine 1×6 a passo 2,54 mm non montato**, con la stessa piedinatura di prima (5V, D−, D+, GND, BOOT, GND; ponticello 5–6 = download). È orizzontale sul bordo inferiore a destra, accanto a J5 (pin 1 a x 30, y 31,7: il posto c'è esattamente, tra J5, C5/C6/D4 e J1). I testi sul retro sono scesi sotto il modulo. Eliminato il footprint `Pogo_1x06_P2.54mm`; il meccanismo `BOTTOM` resta, vuoto.
- Scheda invariata a 55 × 33,5 mm. Freerouting lasciava aperti BOOT e un tratto di +3V3 (anche con il pettine girato di 180°): la pista BOOT dal pin 15 del modulo al pin 5 di J4 è ora fissa in `PREROUTE`, sul retro sotto le colonne RC dei pulsanti 4–6. Con quella, sbroglio completo: DRC 0, collegamenti aperti 0, parità 0; CANL 10 mm.
- Sul branch della scheda 55 × 37 (`claude/pcb-compatto-a`) la stessa modifica ha J4 con il pin 1 a x 36, y 35 e C1 sopra J1.

## 2026-10-19 — La versione con la Kefa resta come variante

- La scheda con i due JST PH (55 × 33,5 mm) diventa quella di `main`. La versione precedente, con la presa estraibile Kefa a 7 poli (55 × 37 mm, pettine J4 in basso a destra), è conservata nel branch **`variante/kefa`**, completa di file di produzione. Non segue le modifiche future di `main`.

## 2026-10-27 — CPL: J2 e J5 ruotati di 180°

- Nell'anteprima JLCPCB la sagoma dei JST PH (C131334) di J2 e J5 non copriva la serigrafia: il modello 3D di JLCPCB è girato di 180° rispetto al footprint KiCad. `gen_bom.py` ora scrive nel CPL 180° per J2 e J5 (`CPL_ROT_FIX`); il PCB e le serigrafie non cambiano. Se l'anteprima mostra ancora uno scarto, correggere anche la posizione (Mid X/Y) del CPL, calcolata sul centro dei pad.

## 2026-10-27 — Connettori rinumerati

- Su richiesta di Alberto: J1 bus (invariato), **J2 Qwiic** (era J3), **J3 pulsanti 1–3** (era J2), **J4 pulsanti 4–6** (era J5), **J5 pettine di programmazione** (era J4). Cambiano solo i designatori: piazzamento e sbroglio sono invariati (`build_pcb.sh`, DRC 0, parità 0). Le voci più vecchie di questo file usano ancora la numerazione precedente.
