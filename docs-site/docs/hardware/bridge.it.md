# Bridge CAN Guasto

Il bridge è una piccola scheda che unisce due sezioni del bus CAN — un segmento
"backbone" e un segmento "di zona" — così un guasto o molto traffico su una sezione non
si propaga necessariamente all'altra. È volutamente semplice: niente WiFi, nessuna
connessione a Home Assistant, nessun aggiornamento via rete. Lo si flasha e se ne
leggono i log solo collegando un cavo USB direttamente ad esso.

È la **stessa scheda CANBed RP2040 di un nodo CAN normale**, con un secondo controller
CAN (un modulo MCP2515) aggiunto sul connettore SPI della scheda. È voluto: una sola
scatola di schede di scorta copre sia i nodi sia i bridge. 🔵 Il bridge non è ancora
stato costruito né flashato su hardware reale.

## Come capire se è il bridge e non qualcos'altro

Se un'intera sezione della casa smette di ricevere traffico CAN mentre il resto del
bus funziona bene, il bridge che unisce quella sezione è il primo sospettato. Il
bridge è progettato per **guastarsi in sicurezza**: se il suo firmware si blocca, un
timer di controllo (watchdog) lo forza a riavviarsi invece di continuare a
malfunzionare, e se non riesce a stare al passo o qualcosa va storto, smette
semplicemente di inoltrare traffico ("si degrada in silenzio") — è costruito per non
bloccare mai il bus né tenerlo occupato. Quindi un bridge guasto/bloccato si presenta
come "quella intera sezione è diventata silenziosa", non come caos generale sul bus.
🔵 Questo comportamento è stato costruito e revisionato nel codice, ma non ancora
messo alla prova con un guasto hardware reale.

Esiste anche un segnale di auto-diagnosi: se il bridge ha mai scartato frame perché il
suo buffer interno si è riempito, blocca un flag di errore
(`ERR_BRIDGE_QUEUE_OVERFLOW`) nel proprio heartbeat che resta impostato finché il
bridge non viene spento e riacceso — quindi un bridge in difficoltà ma non
completamente guasto dovrebbe essere visibile nella sua diagnostica invece di
degradarsi silenziosamente. Poiché un bridge è una normale riga del registro, compare
anche nelle entità di salute per-nodo di Home Assistant esattamente come un nodo: se
smette di inviare l'heartbeat, ricevi lo stesso segnale "nodo offline" che riceveresti
per un interruttore a muro.

!!! danger "Fai il push prima di riflashare"
    Stessa regola di ogni dispositivo derivato dal registro — vedi
    [Guasto Hardware: panoramica](index.md).

## Percorso A — Riflash USB sul posto

La configurazione del bridge è **generata dal registro**, come quella di qualsiasi nodo
— la sua riga del registro porta semplicemente il profilo `bridge` invece di `buttons`.

1. Rigenera: `python3 canbus/tools/generate_nodes.py`.
2. Compila la sua configurazione generata: `esphome compile canbus/nodes/bridge<id>.yaml`
   (nota il prefisso `bridge` — è così che si riconoscono i bridge in `canbus/nodes/`).
3. Flashala via USB-seriale (il bridge non ha OTA/WiFi per progetto — la scheda non ha
   proprio alcuna radio).
4. Conferma che riprenda l'inoltro e l'heartbeat (verifica che il monitor di salute veda
   di nuovo il suo heartbeat).

## Percorso B — Sostituzione scheda (il bridge stesso è danneggiato)

1. Al banco, assegna al bridge sostitutivo un nuovo `node_id` con
   `python3 canbus/tools/allocate_node.py` (i bridge condividono lo spazio piatto dei
   node_id con i nodi CAN normali).
2. In `registry/nodes.csv`, imposta la colonna `profile` di quella nuova riga a `bridge`
   e dai al suo `location` un nome identificabile, es. "bridge - piano 1". L'allocatore
   crea le righe nuove come `buttons`, quindi è questo passaggio che ne fa un bridge.
3. Ritira la vecchia riga del registro del bridge (stesso ragionamento dei nodi CAN —
   i `node_id` non vengono mai riutilizzati).
4. Rigenera, compila e flasha la sostituzione via USB, come nel Percorso A.
5. Installala fisicamente al posto di quella guasta e conferma che riprenda l'inoltro
   e l'heartbeat.

!!! note "Il modulo di ricambio deve essere a 3,3 V"
    Il secondo controller CAN è un modulo MCP2515 aggiuntivo. Deve essere un modello a
    3,3 V (abbinato a un transceiver SN65HVD230, MCP2562FD o TJA1042T,3). Il diffusissimo
    modulo rosso "MCP2515 + TJA1050" è a 5 V e **distruggerà** la scheda — l'RP2040 non
    tollera i 5 V. Verificalo prima di comprare una scorta.

## Correlati

- [Risoluzione problemi bus CAN](../troubleshooting/canbus.md)
- [Nodo CAN](can-node.md) — il caso più comune; un guasto al bridge è più raro di un
  guasto a un nodo normale. Stessa scheda, quindi la scorta è intercambiabile.
