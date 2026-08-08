# Unità VMC Guasta

!!! danger "Lacuna nota — non esiste una procedura di sostituzione"
    Non esiste alcuna procedura documentata di sostituzione hardware per l'unità VMC
    (Ventilazione Meccanica Controllata / Mechanical Extract Ventilation) in nessuna
    parte di questo progetto. Questa pagina riporta ciò che *è* noto così da non
    partire da zero, ma non ti guida attraverso una sostituzione come fanno le altre
    pagine hardware — perché nessuno ha ancora scritto quella procedura.

## Cosa sono questi dispositivi

Ci sono **due** unità VMC, di **modelli diversi**, una per ciascun piano ventilato:

- **Primo piano — Cappellotto Air Fresh I**, indirizzo Modbus `0x10`. Gestisce la
  ventilazione *e* la deumidificazione. È descritta altrove nella documentazione di questo
  progetto come **"il membro del bus meno flessibile"** — significa che se le impostazioni
  seriali del bus RS485 dovessero mai dover essere riconciliate (baud rate, parità), le
  impostazioni supportate da questa unità sono il vincolo attorno a cui deve adattarsi il
  resto del bus, più delle schede relè o analogica. La sua mappa registri completa —
  controlli modalità/on-off/deumidifica, cinque sensori di temperatura, 39 tipi di allarme
  distinti, tracciamento ore filtro — si trova in `climate/mev_modbus.yaml`.
- **Piano terra — Innova HRP DOMO 60 H**, indirizzo Modbus `0x11`. Un'unità passiva a
  recupero di calore che rinnova solo l'aria e risponde alla **qualità dell'aria** — **non**
  gestisce l'umidità (al piano terra l'umidità è gestita dai fancoil). Il suo driver si trova
  in `climate/mev_innova_modbus.yaml`.

Entrambe pilotano la velocità del ventilatore tramite un'uscita analogica 0-10V (primo piano
`analog_output_7`, piano terra `analog_output_8`) e usano Modbus per tutto il resto. Quei due
file sono la fonte di verità per i numeri esatti dei registri se ti servono per la diagnosi;
non sono duplicati qui.

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
