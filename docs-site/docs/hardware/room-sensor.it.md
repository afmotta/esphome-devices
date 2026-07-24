# Scheda Sensore Ambiente Guasta

!!! warning "Pagina speculativa — nessuna procedura confermata"
    Nulla in questo progetto documenta una procedura di sostituzione per una scheda
    sensore ambiente. Questa pagina abbozza un approccio plausibile **per analogia**
    con la procedura del nodo CAN, perché i sensori ambiente sembrano registrarsi
    tramite lo stesso registro dell'intera casa (`registry/nodes.csv` registra un
    flag `sensors` e uno `room_slug` per nodo — il sensore del soggiorno è registrato
    lì come nodo 101). Ma questo non è stato confermato end-to-end, e il processo
    fisico di rimozione/sostituzione di una scheda sensore che potrebbe essere
    integrata in una scatola a muro non è documentato da nessuna parte. Tratta tutto
    quanto segue come un punto di partenza, non come una procedura affidabile — e per
    favore aggiorna questa pagina (e il
    [Registro di Affidabilità](../reference/confidence-ledger.md)) una volta che
    qualcuno lo fa davvero.

## Cos'è questo dispositivo

Esistono due diverse famiglie di schede sensore ambiente in questa casa:

- **S1-Pro Multi-Sense** (`boards/s1-pro-multi-sense.yaml`) — la maggior parte delle
  stanze; include un radar di presenza LD2450, rilevamento qualità dell'aria e altro.
- **wall-sensor** (`devices/wall-sensor.yaml`) — una scheda più semplice
  (temperatura/umidità + qualità dell'aria di base, senza radar), usata in un numero
  minore di stanze.

Ogni stanza ha il proprio piccolo file di configurazione (es.
`devices/room-sensor-soggiorno.yaml`) che imposta lo slug/nome della stanza e include
il modello di scheda condiviso.

## Bozza di una procedura per analogia

1. Conferma di quale famiglia di schede è il sensore guasto (S1-Pro Multi-Sense o
   wall-sensor) — controlla il file di configurazione esistente di quella stanza sotto
   `devices/` o `devices/locals/`.
2. Se la scheda stessa è a posto e devi solo riflasharla, trattala come il
   [Percorso A per un nodo CAN](can-node.md#percorso-a-riflash-usb-sul-posto-usalo-per-primo):
   compila e flasha via USB la configurazione esistente della stanza.
3. Se la scheda fisica deve essere sostituita, trattala come il
   [Percorso B per un nodo CAN](can-node.md#percorso-b-sostituzione-scheda-quando-la-scheda-e-danneggiata):
   questo probabilmente significa ritirare la vecchia riga del registro per quella
   stanza e ri-commissionare la sostituzione — ma conferma che sia davvero così che
   queste schede ottengono la loro identità prima di fare affidamento su questo; non è
   stato verificato contro il vero firmware/strumentario di questa specifica famiglia
   di schede.
4. Segui la stessa [regola d'oro](index.md) di ovunque altro: fai il push del registro
   prima di riflashare qualsiasi cosa.

## Correlati

- [Nodo CAN](can-node.md) — la procedura su cui questa pagina è modellata.
- [Controlli quotidiani](../monitoring.md) — come capire che i dati del sensore di una
  stanza sono diventati obsoleti.
