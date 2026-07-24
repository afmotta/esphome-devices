# Nodo CAN Guasto (Pulsante a Muro / Sensore Ambiente)

Un "nodo CAN" è una delle piccole schede dietro un pulsante a muro o integrata in un
sensore ambiente. Eseguono un firmware fisso (senza WiFi), comunicano con il resto
della casa tramite il bus CAN, e ognuna ha un `node_id` univoco registrato in
`registry/nodes.csv`.

!!! danger "Fai il push prima di riflashare"
    Se hai modificato `registry/nodes.csv` (o usato lo strumento di commissioning qui
    sotto), esegui `python3 canbus/tools/check_registry_pushed.py` e conferma che vada
    a buon fine **prima** di flashare qualsiasi cosa. Vedi
    [Guasto Hardware: panoramica](index.md) per il perché.

Ci sono due percorsi, a seconda che la scheda stessa sia ancora funzionante.

## Percorso A — Riflash USB sul posto (usalo per primo)

Usalo quando la scheda è fisicamente a posto e devi solo cambiare cosa esegue (es. un
aggiornamento firmware, o la voce nel registro è cambiata ma la scheda no). La scheda
resta montata e cablata — devi solo raggiungere la sua porta USB. La sua identità
(`node_id`) viene preservata automaticamente; non serve ri-registrare nulla.

1. Conferma che la riga per questa scheda in `registry/nodes.csv` sia corretta e
   pushata.
2. Rigenera le configurazioni firmware dei nodi:
   `python3 canbus/tools/generate_nodes.py` (controlla la mappa CAN-ID stampata).
3. Compila: `esphome compile canbus/nodes/node<id>.yaml` (il nome file è l'id del
   nodo, con zeri iniziali fino a 3 cifre — es. `node007.yaml`).
4. Raggiungi la porta USB della scheda (ogni nodo installato dovrebbe avere una porta
   raggiungibile senza ricablare — 🔵 previsto per progetto, verificato al momento
   dell'installazione).
5. Flasha: `esphome upload canbus/nodes/node<id>.yaml`.
6. Conferma che rientri sul bus — verifica che il suo heartbeat sia di nuovo visibile
   (vedi [Controlli quotidiani](../monitoring.md) per cosa guardare).

## Percorso B — Sostituzione scheda (quando la scheda è danneggiata)

Usalo quando la scheda fisica stessa deve essere sostituita.

1. Al banco, assegna un **nuovo** `node_id` alla sostituzione:
   `python3 canbus/tools/allocate_node.py`. Questo crea solo la riga nel registro — la
   configurazione firmware del nodo non esiste ancora.
2. Rigenera e compila la sostituzione: `python3 canbus/tools/generate_nodes.py`, poi
   `esphome compile canbus/nodes/node<newid>.yaml`, poi
   `esphome upload canbus/nodes/node<newid>.yaml` (via USB, al banco, prima di
   installarla a muro).
3. **Ritira prima la vecchia riga del registro della scheda guasta** — imposta la sua
   stanza/scheda al placeholder vuoto, oppure elimina la riga del tutto. I `node_id`
   non vengono mai riutilizzati, quindi se salti questo passaggio la vecchia riga
   entrerà in conflitto con la nuova.
4. Sostituisci fisicamente la scheda nuova al posto di quella guasta.
5. Assegna alla nuova scheda la sua stanza/posizione con lo strumento di
   commissioning: `python3 canbus/tools/commission.py` (supporta un flusso "premi un
   pulsante per identificarti", oppure la forma diretta `commission.py assign
   --node-id N --room R --board B`).
6. Conferma che la nuova scheda riporti correttamente dati end-to-end (i suoi
   eventi/letture sensore attesi compaiono).

## Stime di tempo

!!! warning "Non validate — non pianificare in base a questi numeri"
    Queste sono le stime del progetto fatte *in fase di progettazione*, esplicitamente
    segnate come non misurate nel runbook di origine. Trattale solo come un ordine di
    grandezza approssimativo, e se ne misuri una reale, aggiorna questa pagina.

| Attività | Stima | Stato |
|---|---|---|
| Riflash sul posto per scheda (incluso raggiungerla) | ~5–10 minuti | 🔵 solo stima |
| Sostituzione scheda per nodo (banco + installazione + commissioning) | "minuti per nodo" | 🔵 solo stima |
| Campagna su tutta la casa (~100 nodi) | ~2–3 giorni lavorativi | 🔵 solo stima |

## Prima di iniziare una campagna su larga scala

- Ogni nodo installato dovrebbe avere accesso USB senza ricablare — se ne trovi uno
  senza, vale la pena sistemarlo indipendentemente da qualsiasi guasto specifico.
- Ricostruire un'immagine firmware storica *esatta* anni dopo dipende da build
  archiviate per ogni release e dal conoscere la versione esatta di ESPHome usata
  all'epoca — se non sono archiviate, potresti riuscire a costruire solo il firmware
  *attuale*, non riprodurre esattamente quello vecchio.

## Correlati

- [Risoluzione problemi bus CAN](../troubleshooting/canbus.md) — se non sei sicuro che
  la scheda sia davvero guasta rispetto a un problema sull'intero bus.
- [Configurazione ambiente](../setup.md) — se questo è un computer nuovo e non hai
  ancora gli strumenti installati.
