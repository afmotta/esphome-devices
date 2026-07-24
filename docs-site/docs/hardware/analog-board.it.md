# Scheda Uscite Analogiche Guasta

La scheda uscite analogiche (una Waveshare Modbus RTU Analog Output **8CH (B)** — la
variante in tensione, non la simile variante in corrente 0-20mA) genera i segnali 0-10V
che modulano valvole miscelatrici e ventole dei fancoil. È indirizzata a `0x1` sul bus
RS485 climatico. A differenza della scheda relè, questo indirizzo **non** è duplicato
sul bus di illuminazione — questa scheda è esclusiva del clima.

## Assegnazione canali

| Canale | Circuito |
|---|---|
| `analog_output_1` | Valvola miscelatrice radiante piano terra |
| `analog_output_2` | Valvola miscelatrice radiante primo piano |
| `analog_output_3` | Fancoil Soggiorno |
| `analog_output_4` | Fancoil Cucina |
| `analog_output_5` | Fancoil Locale Tecnico |
| `analog_output_6` | Fancoil Sottotetto |
| `analog_output_7` | Velocità ventola VMC primo piano |
| `analog_output_8` | Non assegnato |

## Se stai sostituendo questa scheda con una di ricambio

!!! warning "Lacuna nota — procedura di indirizzamento non confermata"
    A differenza della scheda relè, il registro di configurazione dell'indirizzo di
    questa scheda non è **mai stato verificato indipendentemente** quando l'hardware
    di questa casa è stato standardizzato — solo il registro indirizzo della scheda
    relè (`0x4000`) è stato confermato funzionante come documentato. Lo strumento di
    commissioning in `docs/change_waveshare_relay_address.yaml` è scritto
    specificamente per la scheda relè; i suoi numeri di registro e valori di scrittura
    potrebbero non applicarsi direttamente a questa scheda. **Prima di tentare di
    ri-indirizzare una scheda analogica di ricambio, controlla la procedura sul
    manuale fisico della scheda** invece di assumere che lo strumento della scheda
    relè funzioni senza modifiche.

Ciò che È confermato su questa scheda: i suoi 8 canali di uscita si trovano sui
registri holding Modbus `0x0000`–`0x0007` (canale 1 = registro 0, ecc.), ognuno con un
valore in millivolt da `0` a `10000` (che rappresenta `0`–`10.00V`), letti/scritti con
i codici funzione Modbus standard `0x03`/`0x06`/`0x10`.

## Se hai una scheda di ricambio già indirizzata

Se la scheda sostitutiva è già correttamente indirizzata a `0x1` (confermato in
qualche altro modo — ad es. è arrivata già configurata, oppure l'hai verificato sul
manuale), una sostituzione fisica diretta funziona come per la scheda relè: spegni,
sostituisci, ricabla, riaccendi. Il controller interroga l'indirizzo `0x1`
indipendentemente da quale scheda fisica risponda.

## Correlati

- [Scheda Relè](relay-board.md) — la scheda I/O gemella, con una procedura di
  commissioning confermata che puoi usare come punto di partenza per adattarla a
  questa scheda.
- [Risoluzione problemi clima](../troubleshooting/climate.md) — per problemi di
  comportamento PID/fancoil che potrebbero non essere in realtà una scheda guasta.
