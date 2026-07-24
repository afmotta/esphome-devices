# Unità VMC Guasta

!!! danger "Lacuna nota — non esiste una procedura di sostituzione"
    Non esiste alcuna procedura documentata di sostituzione hardware per l'unità VMC
    (Ventilazione Meccanica Controllata / Mechanical Extract Ventilation) in nessuna
    parte di questo progetto. Questa pagina riporta ciò che *è* noto così da non
    partire da zero, ma non ti guida attraverso una sostituzione come fanno le altre
    pagine hardware — perché nessuno ha ancora scritto quella procedura.

## Cos'è questo dispositivo

L'unità VMC (una Cappellotto Air Fresh I) gestisce la ventilazione e la
deumidificazione dell'intera casa. Comunica in Modbus all'indirizzo `0x10` sul bus
RS485 climatico. È descritta altrove nella documentazione di questo progetto come
**"il membro del bus meno flessibile"** — significa che se le impostazioni seriali del
bus RS485 dovessero mai dover essere riconciliate (baud rate, parità), le impostazioni
supportate da questa unità sono il vincolo attorno a cui deve adattarsi il resto del
bus, più delle schede relè o analogica.

La sua mappa registri completa — controlli modalità/on-off/deumidifica, cinque sensori
di temperatura, 39 tipi di allarme distinti, tracciamento ore filtro — si trova in
`climate/mev_modbus.yaml` nel repository. Quel file è la fonte di verità se ti servono
i numeri esatti dei registri per la diagnosi; non è duplicato qui.

## Se non risponde

Prima di supporre che l'unità stessa sia guasta, escludi il bus condiviso:
[Risoluzione problemi RS485/Modbus](../troubleshooting/rs485-modbus.md) copre
cablaggio, terminazione e conflitti di indirizzo che potrebbero far sembrare guasta
un'unità perfettamente funzionante.

## Se è effettivamente guasta

Questo è territorio genuinamente inesplorato per questo progetto. Punti di partenza
ragionevoli, non una procedura convalidata:

- Contatta il produttore o il tuo installatore per la diagnosi/sostituzione hardware —
  questa è un'unità di ventilazione costruita per uno scopo specifico, non una scheda
  I/O Modbus generica con una storia di ricambi come le schede relè/analogica.
- Reintegrare un'unità sostitutiva (cablaggio, conferma che la mappa registri Modbus
  corrisponda ancora, configurazione indirizzo) va trattato come nuovo lavoro di
  integrazione, non come una sostituzione documentata — verifica ogni registro contro
  il manuale dell'unità stessa invece di assumere compatibilità.
- Se affronti questo lavoro, per favore documenta cosa hai fatto — vedi il
  [Registro di Affidabilità](../reference/confidence-ledger.md) per dove annotarlo, così
  la prossima persona non parte da zero.

## Correlati

- [Risoluzione problemi clima](../troubleshooting/climate.md) — per problemi di
  comportamento della ventilazione che potrebbero non essere affatto un guasto
  hardware.
