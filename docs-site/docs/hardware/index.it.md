# Guasto Hardware: Quale Dispositivo?

Se hai scansionato un codice QR attaccato a un dispositivo specifico, probabilmente
vuoi andare direttamente alla sua pagina — usa il menu a sinistra, oppure l'elenco qui
sotto.

## Prima di tutto, due cose da controllare

1. **È davvero guasto, o è qualcosa a monte che non è raggiungibile?** Una scheda relè
   che "non risponde" potrebbe essere perfettamente funzionante — il problema reale
   potrebbe essere il bus RS485 condiviso, un connettore allentato o un problema di
   alimentazione. Prima di sostituire qualsiasi scheda, fai una verifica rapida: il
   dispositivo è alimentato (LED acceso, se presente)? I cavi sono ben inseriti? È
   *solo* questo dispositivo ad essere colpito, o tutto ciò che è sullo stesso bus si
   comporta in modo anomalo (nel qual caso vedi prima
   [Risoluzione problemi](../troubleshooting/rs485-modbus.md) o
   [Risoluzione problemi bus CAN](../troubleshooting/canbus.md) — potresti non dover
   sostituire nulla)?
2. **La regola d'oro, prima di usare qualsiasi strumento di riflash**: diversi
   dispositivi in questa casa ottengono la propria identità (quale stanza, quale
   numero di nodo) da un file in questo repository, `registry/nodes.csv`. Git è
   l'**unico** backup di quei dati. Se hai appena modificato il registro (aggiunto una
   stanza, ri-registrato un nodo sostituito), **fai il push del commit e conferma con
   `python3 canbus/tools/check_registry_pushed.py` prima di riflashare qualsiasi
   cosa** — quel comando deve stampare un successo (codice di uscita 0). Una modifica
   al registro presente solo sul tuo computer, riflashata su un dispositivo, viene
   descritta altrove in questo progetto come "una casa senza backup." 🟢 Questa
   disciplina è documentata e fondamentale, non opzionale.

## Quale pagina ti serve?

| Sintomo | Vai a |
|---|---|
| Un pulsante a muro o un sensore ambiente non risponde più | [Nodo CAN](can-node.md) |
| Un'intera sezione della casa (un piano, un'ala) non riceve più traffico CAN | [Bridge CAN](bridge.md) |
| Il conteggio "Nodi Mancanti" resta alto ma tutto il resto funziona, oppure il dispositivo monitor di salute sembra offline in Home Assistant | [Monitor di Salute](health-monitor.md) |
| Il controllo climatico non aziona nulla, oppure l'illuminazione non risponde affatto | [Controller (T-Connect Pro)](controller.md) |
| I relè non commutano (pompe, valvole, circuiti di illuminazione) ma il controller sembra a posto | [Scheda Relè](relay-board.md) |
| Fancoil/valvole miscelatrici bloccati, uscite 0-10V che non rispondono | [Scheda Uscite Analogiche](analog-board.md) |
| La ventilazione (VMC) non risponde | [Unità VMC](mev.md) |
| La lettura di temperatura/umidità/qualità dell'aria di una stanza sembra ferma o chiaramente sbagliata | [Scheda Sensore Ambiente](room-sensor.md) |

Non sei ancora sicuro? Inizia da [Controlli quotidiani](../monitoring.md) per
verificare le entità diagnostiche del sistema — di solito indicano il dispositivo
giusto.

!!! note "Etichette di affidabilità usate in questa sezione"
    🟢 **VERIFICATO** — confermato con test su hardware reale.
    🔵 **PROGETTATO** — costruito e pensato per funzionare così, ma non ancora messo
    alla prova con un guasto reale (vero per la maggior parte di questa casa non
    ancora in funzione).
    ⚠️ **LACUNA NOTA** — non esiste una procedura documentata; lo diciamo chiaramente
    invece di improvvisare.
