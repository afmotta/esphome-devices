# Nodo CAN 503 – ESP32-C6-WROOM-1 (rev C)

Nodo per la domotica CAN del fienile, da montare in scatola 503: un morsetto per 24 V e bus CAN, transceiver TJA1051T/3, 6 ingressi pulsante, porta Qwiic (I²C) e modulo **ESP32-C6-WROOM-1-N8** (LCSC C5366877) con Wi-Fi per ESPHome e aggiornamenti OTA. È pensato per il montaggio completo da JLCPCB, con tutti i componenti su un solo lato.

- **Dimensioni:** 55 × 33,5 mm (entro i 56 × 41 mm della CANBed RP2040), 2 strati, spessore 1,6 mm, rame 1 oz
- **Fissaggio:** 2 fori M2,5 non metallizzati (Ø 2,7 mm) in diagonale, in alto a destra e in basso a sinistra, con il centro a 3 mm dai bordi: interasse **49 × 27,5 mm**. Entro 2,8 mm dal centro di ogni foro non ci sono componenti, piste né via, così la testa della vite (fino a Ø 5 mm) appoggia solo su piano di massa coperto da solder mask. L'angolo dell'antenna (in alto a sinistra) resta senza vite: nel case conviene un appoggio o un incastro sugli altri due angoli.
- **Progetto:** KiCad 7 (si apre anche in KiCad 8/9)
- **Simbolo e footprint del modulo:** dalla libreria ufficiale [espressif/kicad-libraries](https://github.com/espressif/kicad-libraries), licenza CC-BY-SA 4.0. Il footprint comprende anche l'area dell'antenna senza rame.

## Contenuto del repository

| Percorso | Cosa contiene |
|---|---|
| `hardware/nodo503.kicad_pro / .kicad_sch / .kicad_pcb` | Progetto KiCad 7 completo (si apre con KiCad 7, 8 o 9) |
| `hardware/nodo503.kicad_sym`, `hardware/nodo503.pretty/` | Simbolo e footprint del modulo ESP32-C6-WROOM-1 (libreria di progetto) |
| `hardware/out/gerber_JLCPCB.zip` | Gerber + foratura, da caricare così com'è su JLCPCB |
| `hardware/out/BOM.csv`, `CPL_JLCPCB.csv` | Distinta e piazzamento per il montaggio completo (SMD + THT) |
| `hardware/out/BOM_SMD.csv`, `CPL_SMD.csv` | Distinta e piazzamento solo SMD |
| `hardware/out/nodo503_schema.pdf`, `anteprima_lato_*.png` | Schema elettrico e anteprime rame + serigrafia |
| `hardware/jlc_library.json` | Libreria JLCPCB (Basic / Preferred / Extended) di ogni codice LCSC |
| `hardware/*.py`, `hardware/*.sh` | Script che generano schema, PCB, sbroglio e file di produzione (vedi [docs/pipeline.md](docs/pipeline.md)) |
| `docs/decisioni.md` | Storia del progetto e motivazioni delle scelte |
| `docs/pipeline.md` | Come rigenerare tutto, struttura degli script, problemi noti |
| `CLAUDE.md` | Contesto per le sessioni di Claude Code che lavoreranno sul progetto |
| `tools/setup.sh` | Installa KiCad 7, Freerouting 1.9.0 e le dipendenze Python |

Per rigenerare i file di produzione dopo una modifica: `sudo tools/setup.sh` (una volta), poi `hardware/route.sh` se cambiano piazzamento o collegamenti, `hardware/build_pcb.sh` se basta lo sbroglio salvato, e infine `hardware/export.sh`.

## Circuito

- **Ingresso 24 V:** PTC da 0,5 A (F1), diodo B5819W contro l'inversione di polarità (D1, 1 A: basta per il PTC da 0,5 A), TVS SMBJ26CA (D2), elettrolitico da 10 µF 50 V e MLCC da 10 µF 50 V in ingresso.
- **5 V:** MORNSUN K7805-500R3 (U1), switching con pin compatibili 7805. Alimenta il TJA1051.
- **3,3 V:** LDO AP2112K-3.3 (U4, 600 mA). Due diodi B5819W (D3, D5) in "OR" lo alimentano dai 5 V del K7805 oppure dai 5 V del pettine di programmazione: il modulo si programma anche senza i 24 V, e la tensione dell'USB non risale verso il K7805.
- **CAN:** TJA1051T/3 con VIO a 3,3 V (nessun partitore sulle linee logiche), pin S a GND, protezione ESD NUP2105L sulle linee del bus. **Nessuna terminazione da 120 Ω** a bordo: il bus va terminato agli estremi della linea.
- **Microcontrollore:** modulo ESP32-C6-WROOM-1-N8 (flash 8 MB, antenna su PCB), con l'antenna a filo del bordo superiore della scheda. Rete RC su EN (10 kΩ + 1 µF) e pull-up da 10 kΩ su GPIO8, come raccomanda Espressif.
- **Ingressi pulsante:** per ciascuno pull-up da 3,3 kΩ a 3,3 V (circa 1 mA nel contatto chiuso, per tenere puliti i contatti in argento dei pulsanti da rete), resistenza in serie da 1 kΩ e condensatore da 100 nF verso GND (τ ≈ 100 µs). Il pulsante chiude verso GND (logica attiva bassa). Componenti 0402 in tre colonne per lato: pulsanti 1–3 a sinistra del modulo, 4–6 a destra.

## Pinout

| Funzione | GPIO | Pin modulo WROOM |
|---|---|---|
| CAN TXD | GPIO23 | 21 |
| CAN RXD | GPIO22 | 20 |
| Pulsante 1 | GPIO7 | 7 |
| Pulsante 2 | GPIO0 | 8 |
| Pulsante 3 | GPIO1 | 9 |
| Pulsante 4 | GPIO20 | 18 |
| Pulsante 5 | GPIO19 | 17 |
| Pulsante 6 | GPIO18 | 16 |
| Qwiic SDA | GPIO3 | 26 |
| Qwiic SCL | GPIO2 | 27 |
| USB D− / D+ (programmazione) | GPIO12 / GPIO13 | 13 / 14 |
| BOOT (pin 5 di J4) | GPIO9 | 15 |
| Pull-up di boot | GPIO8 | 10 |
| Liberi | GPIO4, 5, 6, 10, 11, 15, 16, 17, 21 | – |

Rispetto alla versione 48 × 44 mm i GPIO di pulsanti, Qwiic e CAN sono cambiati: i pulsanti 1–3 usano i pin del lato sinistro del modulo, i pulsanti 4–6 quelli del lato destro, così le piste non si incrociano. GPIO4, GPIO5, GPIO8, GPIO9 e GPIO15 sono pin di strapping: se in futuro ne usi uno, tieni conto del livello che deve avere all'avvio.

## Connettori

- **J1 BUS:** morsetto estraibile ad angolo a 4 poli, passo 3,5 mm, sul bordo destro. Sulla scheda c'è la presa (Kefa KF2EDGR-3.5-4P), a filo del bordo; i fili vanno nella spina a vite (KF2EDGK-3.5-4P), che si innesta di lato da destra, quindi i fili escono paralleli alla scheda come prima. La spina sporge di circa 1 cm oltre il bordo: lascia lo spazio nel case. Dall'alto in basso: 24V – GND – CAN-H – CAN-L.
- **Catena del bus:** il morsetto del bus è uno solo, quindi il cavo che arriva e quello che riparte verso il nodo successivo vanno nello stesso polo della spina (due fili per polo, meglio con un puntale doppio; la spina accetta fino a 1,5 mm² in tutto). Il collegamento tra i due cavi lo fa la spina stessa: sfilandola stacchi la scheda senza interrompere il bus e l'alimentazione degli altri nodi.
- **J2 e J5 PULSANTI:** due connettori JST PH a 4 poli (passo 2 mm, B4B-PH-K-S verticale) sul bordo inferiore, sotto il modulo. **J2** (a sinistra): pulsanti 1, 2, 3, GND. **J5** (a destra): pulsanti 4, 5, 6, GND. Nella maggior parte dei casi basta J2; J5 serve solo per i nodi con più di 3 pulsanti. Il cavo si innesta dall'alto (fili perpendicolari alla scheda) e si sfila per staccare la scheda. Alto 6 mm, 8 mm con il cavo innestato: il componente più alto della scheda resta il K7805.
- **Cavi dei pulsanti:** un cavo a 4 fili per gruppo, con il connettore JST PHR-4 e i contatti SPH-002T-P0.5S (filo da AWG 30 a AWG 24, cioè fino a 0,2 mm²). Il modo più semplice è comprare cavetti PH 2,0 a 4 poli già crimpati, con fili **AWG 24** lunghi 10–15 cm. Il connettore non si salda: si ordina a parte, come prima la spina. La corrente è di circa 1 mA, quindi la sezione conta solo per la meccanica.
- **Collegamento ai frutti:** i pulsanti Vimar Linea hanno morsetti a vite pensati per fili da rete. Metti un **puntale da 0,25 mm²** su ogni filo (oppure ripiega il filo spelato) perché la vite stringa bene. Il GND di ogni cavo va al comune dei 3 frutti del suo gruppo.
- **Montaggio nella scatola:** il JST PH resta innestato per attrito, senza dente di blocco. Lascia un po' di lasco ai cavi quando spingi i frutti nella 503, ed etichetta i due cavi (1–3 e 4–6): hanno lo stesso connettore e si possono scambiare. Nelle scatole dei pulsanti non ci sono conduttori a 230 V; se un giorno ci fossero, i fili sottili dei cavetti PH (isolamento da 300 V) non andrebbero bene così.
- **J3 Qwiic:** JST SH a 4 pin, passo 1 mm, sul bordo superiore a destra con l'imbocco verso l'alto. GND, 3,3 V, SDA, SCL. **Nessun pull-up I²C sulla scheda:** li forniscono il QwiicBus e le schede dei sensori.
- **J4 PROG:** pettine 1×6 a passo 2,54 mm, orizzontale sul bordo inferiore a destra, da non montare (fori passanti). Pin da sinistra: 5V, D−, D+, GND, BOOT, GND (serigrafati sopra i fori). I pin 1–4 vanno al cavo USB (USB nativo del C6). Un ponticello sui pin 5–6 porta GPIO9 a massa e fa partire il modulo in modalità download.

Nessuna terminazione da 120 Ω sulla scheda: il bus va terminato agli estremi della linea.

## Prima programmazione

1. Collega un cavo USB al pettine J4: rosso al 5V, bianco a D−, verde a D+, nero a GND. Puoi saldare un pettine maschio 1×6, oppure infilarne uno nei fori e tenerlo premuto mentre programmi.
2. Con il flash vuoto il modulo di solito entra da solo in modalità download. Se non succede, o se un firmware difettoso ha bloccato l'USB:
   - metti un ponticello sui pin 5–6 di J4 (BOOT–GND);
   - collega l'USB, oppure accendi la scheda;
   - programma, poi **togli il ponticello**. Se lo lasci, il modulo resta in modalità download a ogni riavvio e il firmware non parte.
3. Programma con ESPHome (o esptool) via USB. Dal flash successivo puoi usare l'OTA via Wi-Fi.

## Da verificare prima dell'ordine

1. **Codici LCSC e magazzino.** Tutti i componenti montati hanno un codice LCSC. Al caricamento della BOM controlla la disponibilità, soprattutto di J3 (vedi sotto).
2. **Rotazioni nel file CPL.** Controllale nell'anteprima di assemblaggio JLCPCB, soprattutto per il modulo U3 (l'antenna deve stare a filo del bordo superiore, sopra l'area senza rame), U2, U4 (ruotato di 180°), J3 (ruotato di 180°, imbocco verso l'alto), J1 (ruotato di 90°, imbocco della spina verso il bordo destro), J2 e J5 (la tacca del connettore deve coincidere con quella del footprint), i diodi e C1.
3. **Via nel pad di massa del modulo.** Il pad di massa sotto il WROOM è una griglia 3×3 con 5 via verso la massa sul retro. Su JLCPCB conviene chiedere che le via siano tappate ("via-in-pad" o "epoxy filled"), così lo stagno non cola nei fori. Se non lo fai, di solito funziona comunque.
4. **Piste sotto il modulo.** La pista +3V3 tra i due lati del modulo e le piste USB verso il pettine di programmazione passano sotto il modulo, lontano dall'antenna (sullo strato superiore e sul retro). È ammesso, ma lascia meno piano di massa sotto il modulo.
5. **Fori di J1.** Il footprint Phoenix MC ha fori da 1,2 mm. Il datasheet Kefa non è consultabile da qui: confronta il diametro con il footprint EasyEDA di C441173 (pagina del componente su LCSC o JLCPCB) prima di ordinare. J2 e J5 usano il footprint KiCad del JST PH originale.

## Montaggio

- **Montaggio completo:** carica `BOM.csv` e `CPL_JLCPCB.csv`. JLCPCB monta anche i THT (K7805-500R3, J1, J2 e J5) a onda o a mano. Non resta nulla da saldare, J4 resta senza componente. La spina KF2EDGK-3.5-4P (J1) e i cavi PH per J2/J5 si ordinano a parte.
- **Solo SMD:** carica `BOM_SMD.csv` e `CPL_SMD.csv`. Il K7805, J1, J2 e J5 restano da saldare a mano.

## Esempio ESPHome (indicativo)

```yaml
esp32:
  board: esp32-c6-devkitc-1
  variant: esp32c6
  framework:
    type: esp-idf

canbus:
  - platform: esp32_can
    tx_pin: GPIO23
    rx_pin: GPIO22
    can_id: 0x101
    bit_rate: 125kbps

i2c:
  sda: GPIO3
  scl: GPIO2
  scan: true

binary_sensor:
  - platform: gpio
    name: "Pulsante 1"
    pin:
      number: GPIO7
      inverted: true
      mode: { input: true, pullup: false }   # pull-up esterno da 3,3k
    filters:
      - delayed_on_off: 20ms
  # Pulsanti 2–6: GPIO0, GPIO1, GPIO20, GPIO19, GPIO18
```

## BOM e librerie JLCPCB (aggiornata il 2026-10-14)

Tutti i componenti hanno un codice LCSC e sono pensati per il montaggio completo da JLCPCB, compresi i THT (J1, J2, J5 e K7805 U1, saldati da JLCPCB a onda o a mano). La colonna **Libreria JLCPCB** della BOM indica Basic / Preferred / Extended; l'elenco usato è in `hardware/jlc_library.json`.

- **Non montati:** solo **J4** (pettine di programmazione, DNP). Per programmare si usa un pettine inserito al momento o saldato.
- **C2** è passato da 2,2 µF a **10 µF 50 V 1206** (C13585, Basic): più capacità in ingresso al K7805 e un componente Extended in meno.
- **C1:** Honor Elec RVT1H100M0505 (C86603, Extended), 10 µF 50 V, 5 × 5,4 mm, 105 °C. Dalla ricerca risultavano circa 6 000 pezzi su LCSC: verificalo al caricamento della BOM.
- **D1:** B5819W (C8598, Basic), lo stesso diodo di D3 e D5: al posto dello SS34 in SMA.
- **J1:** presa Kefa KF2EDGR-3.5-4P (C441173, Extended, ad angolo, 10 A 300 V, saldatura a onda, PCBA Economic e Standard), footprint Phoenix MC 1,5/4-G-3,5 orizzontale, fronte della presa a filo del bordo destro. A magazzino LCSC 7 295 pezzi il 2026-10-18. Prima dell'ordine verifica nell'anteprima JLCPCB che l'imbocco della spina sia verso il bordo.
- **Spina per J1 da ordinare a parte:** Kefa KF2EDGK-3.5-4P (LCSC C440849, 12 196 pezzi il 2026-10-18), vite M2, filo fino a 1,5 mm².
- **J2 e J5:** JST B4B-PH-K-S(LF)(SN) originale (C131334, Extended, saldatura a onda), lo stesso codice per i due connettori. Dalla ricerca del 2026-10-19 risultavano circa 95 000 pezzi su LCSC: verificalo al caricamento della BOM.
- **Cavi per J2/J5 da ordinare a parte:** cavetti PH 2,0 a 4 poli già crimpati (fili AWG 24), oppure connettori JST PHR-4 con contatti SPH-002T-P0.5S da crimpare. Non sono nella BOM di montaggio perché non si saldano.
- **CPL:** per i THT la posizione è il centro dei pin (non il pin 1). Controlla nell'anteprima di assemblaggio le rotazioni dei morsetti e del K7805.
- **J3 (C160404) ha pochissimi pezzi a magazzino.** Alternative compatibili Qwiic (Extended, da confrontare con il footprint): ZX-SH1.0-4PWT C7430446, HC-1.0-4PWT C2845363, BX-SH1.0-4PWT C18077910.
- Le pagine JLCPCB dei componenti Preferred mostrano solo "Extended": al caricamento della BOM verifica che abbiano il badge "Preferred".

## Storia e decisioni

Esiste anche una variante con un unico morsetto estraibile Kefa a 7 poli per i pulsanti (scheda 55 × 37 mm, spina a vite e cordina da 0,5 mm²): è nel branch `variante/kefa`, con i suoi file di produzione.

La storia del progetto (rev A con XIAO, rev B con MINI-1, revisione di un esperto, passaggio a 56 × 41 mm e poi a 55 × 33,5 mm, scelta dei connettori) e il motivo di ogni scelta sono in [docs/decisioni.md](docs/decisioni.md).
