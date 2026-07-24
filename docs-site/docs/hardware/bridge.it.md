# Bridge CAN Guasto

Il bridge è una piccola scheda (LilyGO T-2CAN) che unisce due sezioni del bus CAN —
un segmento "backbone" e un segmento "di zona" — così un guasto o molto traffico su
una sezione non si propaga necessariamente all'altra. È volutamente semplice: niente
WiFi, nessuna connessione a Home Assistant, nessun aggiornamento via rete. Lo si
flasha e se ne leggono i log solo collegando un cavo USB direttamente ad esso.

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
degradarsi silenziosamente.

!!! danger "Fai il push prima di riflashare"
    Stessa regola di ogni dispositivo derivato dal registro — vedi
    [Guasto Hardware: panoramica](index.md).

## Percorso A — Riflash USB sul posto

A differenza di un nodo normale, la configurazione del bridge (`devices/bridge.yaml`)
è **scritta a mano**, non generata dal registro — salta il passaggio di rigenerazione
del registro.

1. Compilala direttamente: `esphome compile devices/bridge.yaml`.
2. Flashala via USB-seriale (il bridge non ha OTA/WiFi per progetto — le radio sono
   volutamente disattivate su questo dispositivo).
3. Conferma che riprenda l'inoltro e l'heartbeat (verifica che il controller veda di
   nuovo il suo heartbeat).

!!! warning "Ignora il file esca"
    Il generatore del registro (`canbus/tools/generate_nodes.py`) emette comunque un
    file `canbus/nodes/node<id>.yaml` per la riga del registro del bridge, perché il
    bridge condivide lo stesso spazio di numerazione `node_id` dei nodi normali.
    **Non flashare mai quel file sul bridge** — è una configurazione generica di nodo,
    non il vero firmware del bridge. Flasha sempre `devices/bridge.yaml` direttamente.

## Percorso B — Sostituzione scheda (il bridge stesso è danneggiato)

1. Al banco, assegna al bridge sostitutivo un nuovo `node_id` con
   `python3 canbus/tools/allocate_node.py` (i bridge condividono lo spazio piatto dei
   node_id con i nodi CAN normali — dai alla riga del registro un nome identificabile,
   es. "bridge - piano 1").
2. In `devices/bridge.yaml`, imposta la sostituzione `node_id` al nuovo id assegnato
   (il file viene fornito con un valore placeholder — controlla il file attuale, non
   dovrebbe più dire `"200"` quando flashi un bridge reale con esso).
3. Ritira la vecchia riga del registro del bridge (stesso ragionamento dei nodi CAN —
   i `node_id` non vengono mai riutilizzati).
4. Compila e flasha la sostituzione via USB, come nel Percorso A.
5. Installala fisicamente al posto di quella guasta e conferma che riprenda l'inoltro
   e l'heartbeat.

## Correlati

- [Risoluzione problemi bus CAN](../troubleshooting/canbus.md)
- [Nodo CAN](can-node.md) — il caso più comune; un guasto al bridge è più raro di un
  guasto a un nodo normale.
