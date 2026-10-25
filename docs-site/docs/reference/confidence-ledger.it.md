# Registro di affidabilità

Quasi nulla in questa casa è stato ancora testato sul campo — il sistema è "pre-live"
(progettato e in gran parte costruito, ma non installato fisicamente). Ogni pagina di
questo sito etichetta le proprie affermazioni non banali come 🟢 **VERIFICATO**,
🔵 **PROGETTATO**, oppure ⚠️ **LACUNA NOTA** (vedi il [Glossario](glossary.md) per le
definizioni complete). Questa pagina è l'elenco principale di quelle etichette in un
unico posto: ogni affermazione 🔵 PROGETTATO che dovrebbe diventare 🟢 VERIFICATO una
volta confermata su hardware reale, e ogni ⚠️ LACUNA NOTA a cui manca ancora una
risposta.

!!! note "Questo è un documento vivo"
    Se verifichi sul campo qualcosa in questo elenco, aggiorna la sua riga qui (e
    nella pagina che riporta l'affermazione originale) invece di lasciare entrambe
    non aggiornate. Se trovi un'affermazione 🔵 PROGETTATO su un'altra pagina che non
    è ancora elencata qui, aggiungila — è proprio lo scopo di questa pagina.

## Discrepanze (priorità più alta di una semplice lacuna)

Queste non sono solo non verificate — la documentazione e il codice effettivo sono in
disaccordo tra loro, il che è peggio di una semplice lacuna perché può fuorviare chi
si fida della fonte sbagliata. **Al momento non ce n'è nessuna aperta**; quelle risolte
restano elencate perché la vecchia affermazione non venga reintrodotta.

| Affermazione | La discrepanza | Stato |
|---|---|---|
| Tempistica dello "spegnimento sicuro" del failover di emergenza dei sensori | Il `CLAUDE.md` alla radice affermava che il livello di emergenza "attiva lo spegnimento sicuro **dopo 5 minuti**." Cosa fa davvero il codice: (1) il failover (`climate/packages/components/failover_sensor.yaml`) restituisce `NAN` (not-a-number) **immediatamente** non appena sia il livello primario (CAN) sia quello secondario (Home Assistant) non sono disponibili — nessun timer; (2) il controller PID di ESPHome porta le proprie uscite a **0 immediatamente** quando l'ingresso di temperatura è NaN (`pid_climate.cpp`); (3) gli unici "5 minuti" della catena sono il **periodo di grazia del livello Home Assistant**: quel livello vale NaN quando HA segnala l'entità come `unavailable`/`unknown`, oppure quando da 5 minuti non esiste alcuna connessione a Home Assistant con sottoscrizione agli stati (abbastanza da coprire un riavvio di HA; `climate/protocol/ha_tier.h`). Prima di questo fix il livello HA non diventava mai NaN — manteneva l'ultimo valore per sempre, quindi una zona poteva essere controllata su una lettura congelata. | ✅ **Risolta** (review del repository R-04, 2026-10-25) — documentazione corretta per riflettere il codice. Il comportamento è coperto da test nativi e da test end-to-end su piattaforma host, non ancora da una prova su banco sul controller reale (vedi la riga 🔵 sotto). Ancora aperto: l'override del boost radiante può scavalcare lo zero imposto dal NaN (review R-05). Suggerimento: una sessione `esphome logs` dimenticata aperta conta anch'essa come sottoscrizione agli stati e mantiene vivo il livello HA durante un'interruzione di HA — usa `esphome logs --no-states`. |

## Affermazioni 🔵 PROGETTATO in attesa di verifica sul campo

| Affermazione | Dove viene usata | Fonte |
|---|---|---|
| Stime di tempo per il riflash in loco (~5–10 min), la sostituzione della scheda ("minuti per nodo") e una campagna sull'intera casa (~2–3 giorni lavorativi) per i nodi CAN | [Sostituzione nodo CAN](../hardware/can-node.md) | `canbus/docs/reflash-campaign-runbook.md`, che segnala esplicitamente la propria tabella dei tempi come **"STUB — in attesa di misurazione su banco"** e dichiara che i numeri sono stime non validate che devono essere misurate su banco prima di poterle usare per pianificare. |
| Un nodo CAN viene dichiarato "perso" dopo 3 heartbeat mancati consecutivi (90 secondi di silenzio) | [Risoluzione problemi bus CAN](../troubleshooting/canbus.md) | Implementato e coperto da test automatici della logica, ma non ancora messo alla prova con un guasto reale su banco o sul campo. |
| Il bridge CAN fallisce in modo sicuro (diventa silenzioso invece di intasare il bus) e si riprende da solo dai blocchi tramite un watchdog hardware | [Risoluzione problemi bus CAN](../troubleshooting/canbus.md) | Costruito e pensato per funzionare così; non ancora dimostrato con un guasto reale del bridge. |
| La logica di prontezza a tre condizioni della porta `ha_ready` (connessione API, heartbeat recente, hash del manifesto dei binding corrispondente) | [Risoluzione problemi bus CAN](../troubleshooting/canbus.md) | Implementata; non ancora messa alla prova con un'interruzione reale di Home Assistant sul campo. |
| Ogni nodo CAN installato ha accesso USB senza bisogno di essere smontato o ricablato | [Sostituzione nodo CAN](../hardware/can-node.md) | Un requisito di progetto (ADR-0008 §3), verificato per singolo nodo solo al momento dell'installazione — non ancora vero per nessun nodo, dato che nessuno è installato. |
| Accordo di parità del bus RS485: sia il bus climatizzazione sia il bus illuminazione possono far funzionare tutti i loro dispositivi all'impostazione target 38400 8E1 | [Tabella hardware e indirizzi](hardware-table.md), [Risoluzione problemi RS485/Modbus](../troubleshooting/rs485-modbus.md) | Configurazione target secondo ADR-0014 §4; in attesa di una verifica fisica in fase di avviamento, poiché l'unità di ventilazione (VMC) è il membro meno flessibile del bus ed è il vincolo determinante se non riesce a raggiungere quell'impostazione. |
| Pulsare manualmente ogni canale relè/analogico confermerà che la mappa cablaggio/attuatore corrisponde alla [tabella di assegnazione relè](hardware-table.md) | `docs/climate-deployment-runbook.md` Fase 0.1 | La mappatura è progettata e documentata; non è mai stata verificata contro il cablaggio fisico perché il cablaggio fisico non esiste ancora. |
| La cascata di domanda di ventilazione VMC (Solo ventola → Deumidificazione → Integrazione) e il blocco di sicurezza "qualsiasi allarme forza la ventola a zero" | `docs/climate-deployment-runbook.md` Fase 0.2 | Implementata in `climate/mev_demand.yaml`/`mev_modbus.yaml`; non ancora eseguita contro un'unità VMC reale. |
| Anti-ciclo del boost fancoil e passaggio pulito di ritorno a "Solo radiante" | `docs/climate-deployment-runbook.md` Fase A-C4 | Implementato nel coordinatore di boost; non ancora eseguito su hardware reale. |
| La logica del guardiano finestre si autoattiva quando mappata e resta un no-op sicuro quando non mappata o quando Home Assistant è offline | `climate/packages/components/window_guard.yaml`, `docs/climate-deployment-runbook.md` Fase C | Progettata per degradare in modo sicuro; non ancora messa alla prova con un sensore finestra reale o un'interruzione reale di Home Assistant. |
| Il bridge I²C-a-1-Wire DS2484 (indirizzo `0x18`) non entra in collisione con il controller touch integrato sul bus I²C condiviso | ADR-0014 §5 | Segnalato come punto aperto nello stesso ADR, da confermare all'avviamento dell'hardware. |
| La scheda Waveshare disponibile è realmente la variante RS485-CAN con un transceiver CAN cablato su GPIO15/16, e il secondo tap CAN che aggiunge sul backbone non richiede una modifica alla terminazione | ADR-0015, punti aperti 1–3 | Ipotizzato dal cablaggio noto del precedente gateway (pre-separazione); non ancora confermato su banco sulla scheda reale. |
| Il livello Home Assistant del sensore di stanza vale NaN dopo 5 minuti senza Home Assistant (o quando l'entità è `unavailable`), dopodiché le uscite PID della zona scendono a 0 | [Controlli quotidiani](../monitoring.md), [Risoluzione problemi climatizzazione](../troubleshooting/climate.md) | Implementato (R-04) con test nativo della regola e test end-to-end su piattaforma host; non ancora provato sul controller reale. Prova su banco: scollega Home Assistant e verifica che il text sensor del livello lasci "HA" dopo ~5 minuti e che l'uscita di valvola/fancoil della zona vada a 0. |

## ⚠️ LACUNE NOTE nominate (nessuna risposta ancora, dichiarate apertamente)

| Lacuna | Dettaglio | Dove emerge |
|---|---|---|
| Politica delle scorte di riserva | Quante schede CAN pre-flashate di riserva tenere sullo scaffale per il percorso di sostituzione scheda, e con quale disciplina di allocazione del `node_id`. Registrato come punto aperto dell'ADR-0008 (`docs/adr/0008-post-live-firmware-evolution-no-can-bootloader.md`): *"Spare-stock policy (ADR-0008 open item 4) [ops / commissioning] — how many pre-flashed spare boards sit on the shelf for the board-swap path, and at what `node_id` allocation discipline (ADR-0007 id space). Supports `docs/reflash-campaign-runbook.md` Path B."* (Politica delle scorte di riserva — quante schede pre-flashate tenere di scorta per il percorso di sostituzione, e con quale disciplina di allocazione del `node_id`. Supporta il Percorso B del runbook di riflash.) Nessuna risposta è stata registrata da nessuna parte finora. | Sostituzione scheda nodo CAN |
| Nessuna procedura di sostituzione hardware per l'unità VMC | Non esiste alcuna procedura documentata nel repository per sostituire fisicamente l'unità di ventilazione (VMC) in sé — solo per il lato cablaggio/comunicazione Modbus. | [Unità VMC](../hardware/mev.md) |
| Nessuna procedura di sostituzione hardware per le schede sensore ambiente | Non esiste alcuna procedura documentata per sostituire fisicamente una scheda S1 Pro Multi-Sense o una scheda sensore a muro (quelle dietro [Scheda sensore ambiente](../hardware/room-sensor.md)) — solo per il percorso software di failover dei dati del sensore. | [Scheda sensore ambiente](../hardware/room-sensor.md) |
| Lunghezze reali dei cavi RS485 per questa casa | Le indicazioni sulla lunghezza dei cavi nella [pagina di risoluzione problemi RS485/Modbus](../troubleshooting/rs485-modbus.md) si basano sui limiti generali dello standard RS485, non su una misurazione delle tratte di cablaggio reali di questa casa, perché l'installazione fisica non è ancora avvenuta. | Risoluzione problemi RS485/Modbus |

## Correlati

- [Glossario](glossary.md) — definisce il sistema di etichette 🟢/🔵/⚠️ usato in
  tutto questo sito.
- [Mappa dei documenti](doc-map.md) — per trovare il documento sorgente sottostante
  di qualsiasi affermazione elencata qui.
- [Tabella hardware e indirizzi](hardware-table.md) — diverse righe sopra fanno
  riferimento alle sue affermazioni su parametri del bus e assegnazione relè.
