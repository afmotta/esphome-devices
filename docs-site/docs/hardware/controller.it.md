# Controller Guasto (T-Connect Pro)

Lo stesso modello di scheda — un LilyGO T-Connect Pro (ESP32-S3 con Ethernet, RS485 e
CAN integrati) — viene usato per **due ruoli diversi** in questa casa: il controller
climatico e il controller di illuminazione. Eseguono firmware completamente diversi,
ma una scheda di ricambio autentica di questo modello funziona per entrambi i ruoli —
questo è il senso di standardizzare su un'unica famiglia di controller.

Prima di fare qualsiasi cosa, capisci quale ruolo è guasto:

- **Controller climatico** guasto: nessuna stanza si riscalda/raffredda/ventila, le
  entità PID in Home Assistant non sono raggiungibili, o l'intero dispositivo
  climatico è offline.
- **Controller di illuminazione** guasto: nessuna luce risponde a Home Assistant *né*
  ai pulsanti a muro (una singola luce che non risponde è più probabilmente un
  problema di [scheda relè](relay-board.md) o [nodo CAN](can-node.md) — questa pagina
  riguarda "l'intero sistema di illuminazione è fuori uso").

## Controller climatico

1. Procurati una scheda T-Connect Pro di ricambio (variante Ethernet).
2. Copia i secret di cui ha bisogno. I secret della build di sviluppo locale si
   trovano in `devices/locals/secrets.yaml`; quelli della build di
   produzione/OTA si trovano in `devices/remotes/secrets.yaml` — sono file separati
   con (probabilmente) chiavi di cifratura diverse, quindi usa quello che corrisponde
   a come questo specifico controller è stato provisionato. In caso di dubbio, parti
   da `devices/secrets.yaml.example` e vedi
   [Configurazione ambiente](../setup.md) per cosa significa ogni chiave.
3. Flashalo:
   - Per una build locale/da banco: `esphome run devices/locals/climate-control.yaml
     --device /dev/ttyUSB0` (il primo flash richiede USB; in seguito `esphome run`
     può passare per la rete).
   - Per lo schema di deployment di produzione basato su GitHub:
     `devices/remotes/climate-control.yaml` recupera la definizione del firmware da
     GitHub e viene normalmente installato cliccando "Installa" sulla scheda del
     dispositivo nell'add-on ESPHome di Home Assistant — vedi
     [Configurazione ambiente](../setup.md) per la differenza tra questi due schemi.
4. **Prima di alimentare qualsiasi cosa**, conferma che il controller si avvii nel suo
   stato di riposo sicuro (🔵 previsto per progetto, descritto nel runbook di
   deployment del progetto, non ancora messo alla prova dopo una vera sostituzione
   hardware):

   | Controllo | Atteso dopo un flash pulito | Perché conta |
   |---|---|---|
   | `hp_mode_manual_hold` | ON | `hp_mode` non si muove da solo |
   | `hp_mode` | SANITARY_ONLY | Nessun riscaldamento/raffrescamento ambienti da nessuna parte |
   | Ogni entità `climate` di zona | OFF | Nessuna attuazione radiante/fancoil |
   | Pendenza curva termica di ogni piano | 0 | Curva piatta, mandata fissa, nessuna sorpresa da compensazione climatica |
   | Interruttori boost abilitati | OFF | Nessun boost ibrido radiante+fancoil |
   | VMC (ventilazione) abilitata | OFF | La ventola resta spenta finché non la accendi deliberatamente |

   Se qualcosa sta attuando che non dovrebbe, spegni l'entità `climate` di quella
   specifica zona come argine immediato, poi indaga.
5. Una volta confermato che è sicuro, riporta le zone online deliberatamente e osserva
   il comportamento per un giorno o due invece di ripristinare tutto in una volta —
   vedi la guida sul [cambio stagionale](../maintenance-tasks.md) per la stessa
   disciplina applicata in modo ordinario.

## Controller di illuminazione

1. Procurati una scheda T-Connect Pro di ricambio (variante Ethernet).
2. Questo controller viene compilato direttamente — al momento non esiste una
   variante `devices/locals/` o `devices/remotes/` per esso (⚠️ a differenza del
   clima, esiste un solo file di configurazione: `devices/light-controller.yaml`).
   Flashalo con `esphome run devices/light-controller.yaml --device /dev/ttyUSB0` per
   il primo flash.
3. Questo dispositivo porta anche il banco relè e la logica di fallback dei pulsanti —
   dopo il flash, conferma che i relè rispondano ai comandi di Home Assistant, e che
   la diagnostica `ha_ready` sembri corretta (vedi
   [Controlli quotidiani](../monitoring.md) e
   [Risoluzione problemi illuminazione](../troubleshooting/lighting.md) se qualcosa
   sembra sbagliato).
4. ⚠️ A differenza del controller climatico, non esiste una checklist documentata di
   "stato di riposo sicuro dopo il flash" per il controller di illuminazione in questo
   repository. Finché non ne esiste una, l'approccio più sicuro dopo una sostituzione
   è verificare manualmente ogni relè prima di fidarsi del sistema incustodito.

## Correlati

- [Configurazione ambiente](../setup.md) — installare gli strumenti e i secret
  necessari per compilare/flashare.
- [Scheda Relè](relay-board.md) / [Scheda Uscite Analogiche](analog-board.md) — se in
  realtà è una delle schede I/O, non il controller stesso, ad essere fuori uso.
