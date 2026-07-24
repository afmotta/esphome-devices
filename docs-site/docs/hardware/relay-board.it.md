# Scheda Relè Guasta

La scheda relè (una Waveshare Modbus RTU Relay 32CH) comanda pompe, valvole
miscelatrici, circuiti radianti a pavimento e circuiti di illuminazione — 32 canali su
una scheda. È indirizzata a `0x2` sul bus RS485, e questo indirizzo è volutamente
**duplicato identico sia sul bus climatico che su quello di illuminazione**, quindi
una scheda di ricambio pre-indirizzata a `0x2` funziona in entrambi i sistemi senza
alcuna configurazione aggiuntiva.

## Commissionare una scheda nuova/di ricambio

Una scheda nuova di fabbrica viene fornita con l'indirizzo predefinito `0x1`. Devi
cambiarlo in `0x2` prima di cablarla in uno dei due sistemi.

!!! danger "Solo una scheda sul bus durante questa operazione"
    La procedura di commissioning scrive all'indirizzo di *broadcast*, che ogni
    dispositivo Modbus in ascolto accetta. Se durante questa operazione è collegata
    più di una scheda, le ri-indirizzerai tutte contemporaneamente. Scollega tutto
    tranne la scheda che stai commissionando.

1. Collega la scheda target **da sola** al terminale RS485 di un T-Connect Pro di
   ricambio (A→A, B→B).
2. Prendi lo strumento di commissioning già pronto in
   `docs/change_waveshare_relay_address.yaml` in questo repository, modifica i
   placeholder WiFi, e flashalo sul T-Connect Pro di ricambio:
   `esphome run docs/change_waveshare_relay_address.yaml`.
3. Nella sua interfaccia web (o in Home Assistant, una volta connesso), osserva il
   sensore "Address Register" — dovrebbe leggere `1` (il valore di fabbrica),
   confermando che la scheda risponde.
4. Premi il pulsante "Write Address". Questo invia il cambio di indirizzo.
5. Spegni e riaccendi la scheda relè (il cambio di indirizzo ha effetto solo dopo un
   riavvio).
6. Per verificare, modifica la sostituzione `current_address` dello strumento in
   `0x02` e riflasha — il sensore Address Register dovrebbe ora leggere `2`.
7. Cabla la scheda in posizione. I controller della casa si aspettano già una scheda
   relè a `0x2`, quindi una volta cablata e alimentata dovrebbe essere riconosciuta
   automaticamente — nessuna modifica di configurazione lato controller necessaria.

⚠️ **Attenzione sui parametri seriali**: questo strumento di commissioning comunica ai
valori di fabbrica della scheda (9600 8N1). I bus attivi di questa casa hanno come
obiettivo **38400 8E1** — un baud rate e una parità diversi. Cambiare baud/parità di
una scheda rispetto al valore di fabbrica è una scrittura di registro *separata* che
questo strumento non automatizza (al momento della stesura, questa procedura non è
stata confermata/testata in fase di bring-up). Se il tuo bus attivo funziona davvero a
38400 8E1, una scheda di ricambio appena indirizzata potrebbe aver bisogno di una
riconfigurazione separata dei parametri seriali prima di comunicare correttamente —
non dare per scontato che il solo indirizzamento sia sufficiente; verifica sul manuale
della scheda o testando la comunicazione dopo averla cablata.

## Se la scheda necessita solo di una sostituzione diretta (già correttamente indirizzata)

Se hai una scheda di ricambio già pre-indirizzata (già impostata a `0x2` e, idealmente,
già testata al banco ai parametri seriali attivi), puoi saltare i passaggi di
commissioning sopra — basta spegnere, sostituire la scheda fisica, ricablare e
riaccendere. Non serve alcuna modifica di configurazione lato controller; interroga
l'indirizzo `0x2` indipendentemente da quale scheda fisica risponda.

## Correlati

- [Tabella assegnazione relè](../reference/hardware-table.md) — quale numero di relè
  controlla quale circuito.
- [Risoluzione problemi RS485/Modbus](../troubleshooting/rs485-modbus.md) — se non sei
  sicuro che la scheda sia davvero guasta rispetto a un problema di cablaggio/bus.
- [Scheda Uscite Analogiche](analog-board.md) — l'*altra* scheda I/O Modbus; la sua
  procedura di commissioning è meno documentata, non dare per scontato che sia
  identica.
