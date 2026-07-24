# Monitor di Salute Guasto

Il monitor di salute è un dispositivo dedicato (una scheda Waveshare
ESP32-S3-RS485-CAN) il cui unico compito è osservare il bus CAN e riportare a Home
Assistant quali nodi sono attivi o mancanti. Non controlla nulla — luci, relè e clima
continuano a funzionare normalmente anche se questo dispositivo è completamente
guasto. Ciò che si perde è la *visibilità*: smetti di ricevere notifiche "nodo perso" /
"nodo recuperato" e i conteggi diagnostici (Nodi Online/Totale/Mancanti) diventano
obsoleti.

Detto ciò, questo dispositivo è il tuo sistema di allarme precoce per ogni *altro*
guasto descritto in questa guida — sistemalo tempestivamente anche se non c'è
nessuna emergenza in corso.

!!! warning "È l'unico dispositivo senza una scorta dello stesso modello per default"
    Ogni altro controller/scheda relè/scheda analogica in casa è stato
    volutamente standardizzato in modo che un solo scaffale di ricambi copra tutti.
    Questo dispositivo è l'unica eccezione documentata — vedi la procedura di
    ripiego qui sotto.

## Se hai una scheda Waveshare ESP32-S3-RS485-CAN di ricambio

Questo è il caso semplice — stesso modello, stessi pin, nessuna modifica necessaria.

1. Flasha la configurazione standard sulla scheda di ricambio:
   `esphome compile devices/health-monitor.yaml` poi
   `esphome upload devices/health-monitor.yaml` (ha WiFi/OTA, quindi una volta che
   l'originale è provisionato puoi normalmente aggiornarla via rete — un primo flash
   richiede USB).
2. Assicurati che `health_monitor_encryption_key` in `devices/secrets.yaml` sia
   disponibile per la build (questo dispositivo ha una propria chiave di cifratura
   distinta, separata da quella del controller di illuminazione).
3. Sostituisci la scheda fisica e conferma che si riconnetta a Home Assistant e
   ricominci a riportare lo stato di salute dei nodi.

## Se non è disponibile una scheda Waveshare di ricambio: ripiego su un T-Connect Pro di ricambio

Poiché la logica di monitoraggio della salute (`canbus/packages/health.yaml`) richiede
solo un transceiver CAN — niente RS485, nessun banco relè — può funzionare su una
scheda controller T-Connect Pro di ricambio, cambiando due sostituzioni di pin.
`devices/health-monitor.yaml` dichiara già i suoi pin CAN come sostituzioni
(`can_tx_pin: GPIO15`, `can_rx_pin: GPIO16` — i pin della scheda Waveshare). Il
transceiver CAN di un T-Connect Pro si trova su pin diversi (`GPIO6`/`GPIO7`, secondo
lo standard hardware di questa casa).

1. Crea una nuova configurazione dispositivo che componga `boards/t-connect-pro.yaml`
   (o la variante Ethernet/WiFi che preferisci) invece di
   `boards/waveshare-s3-rs485-can.yaml`, mantenendo tutto il resto uguale a
   `devices/health-monitor.yaml` (`canbus/packages/health.yaml`, gli stessi include,
   lo stesso schema di sostituzioni identità/OTA).
2. Sovrascrivi le due sostituzioni dei pin CAN con i valori del T-Connect Pro:
   `can_tx_pin: GPIO6`, `can_rx_pin: GPIO7`.
3. Compila, flasha e verifica che inizi a riportare lo stato di salute dei nodi.

⚠️ **Lacuna nota**: al momento della stesura di questa pagina non esiste ancora
questo file di configurazione di ripiego nel repository — dovresti crearlo da zero
partendo dal modello sopra, non modificarne uno esistente. La portabilità dei pin in
sé è documentata e intenzionale (ADR-0015), ma nessuno ha ancora avuto bisogno di
costruire davvero questa configurazione di ripiego, quindi tratta i passaggi sopra
come un buon punto di partenza, non come un file pronto da copiare e incollare.

## Correlati

- [Controller (T-Connect Pro)](controller.md) — se stai improvvisando il ripiego sopra,
  questa pagina copre la scheda controller condivisa più in dettaglio.
- [Controlli quotidiani](../monitoring.md) — come appaiono le entità diagnostiche del
  monitor di salute quando tutto va bene.
