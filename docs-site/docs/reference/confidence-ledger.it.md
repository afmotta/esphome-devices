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
si fida della fonte sbagliata.

| Affermazione | La discrepanza | Stato |
|---|---|---|
| Tempistica dello "spegnimento sicuro" del failover di emergenza dei sensori | Il `CLAUDE.md` alla radice afferma che il livello di emergenza "attiva lo spegnimento sicuro **dopo 5 minuti**." La logica di failover effettiva (`climate/packages/components/failover_sensor.yaml`) restituisce `NAN` (not-a-number) **immediatamente** non appena sia la fonte primaria sia quella secondaria non sono disponibili — non c'è nessun timer di 5 minuti in quel file, né una costante di timeout altrove in `climate/packages/`. Non è noto se qualche consumatore *a valle* di quel valore NaN (un controller PID, un coordinatore) attenda indipendentemente 5 minuti prima di agire su di esso, oppure se "5 minuti" sia semplicemente una cifra imprecisa nella documentazione. | ⚠️ **Discrepanza irrisolta** — richiede una misurazione su banco di cosa succede realmente end-to-end quando il valore del sensore di una zona diventa NaN, e poi o il codice necessita di un vero timer aggiunto, oppure la documentazione "5 minuti" va corretta per riflettere la realtà. Non fare affidamento sull'esistenza di un periodo di grazia di 5 minuti finché questo non è risolto. |

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

## ⚠️ LACUNE NOTE nominate (nessuna risposta ancora, dichiarate apertamente)

| Lacuna | Dettaglio | Dove emerge |
|---|---|---|
| Politica delle scorte di riserva | Quante schede CAN pre-flashate di riserva tenere sullo scaffale per il percorso di sostituzione scheda, e con quale disciplina di allocazione del `node_id`. Registrato testualmente in `canbus/_bmad-output/implementation-artifacts/deferred-work.md` come punto aperto dell'ADR-0008: *"Spare-stock policy (ADR-0008 open item 4) [ops / commissioning] — how many pre-flashed spare boards sit on the shelf for the board-swap path, and at what `node_id` allocation discipline (ADR-0007 id space). Supports `docs/reflash-campaign-runbook.md` Path B."* (Politica delle scorte di riserva — quante schede pre-flashate tenere di scorta per il percorso di sostituzione, e con quale disciplina di allocazione del `node_id`. Supporta il Percorso B del runbook di riflash.) Nessuna risposta è stata registrata da nessuna parte finora. | Sostituzione scheda nodo CAN |
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
