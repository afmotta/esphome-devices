# Climatizzazione — Diagnosi e soluzione: problemi comuni

Il sistema di climatizzazione controlla riscaldamento/raffrescamento a
pavimento/soffitto radiante più unità fancoil sui tre piani della casa,
usando un controller che legge i sensori di stanza via bus CAN (con un
ripiego su Home Assistant) e comanda relè e uscite 0-10V tramite il proprio
bus RS485/Modbus. Questa pagina copre la confusione sui livelli di ripiego
dei sensori (failover), i problemi di taratura del ciclo di controllo PID,
i problemi di ventilazione (MEV) e la selezione manuale della modalità
stagionale. Per problemi di cablaggio e comunicazione sul bus RS485 stesso,
vedi [RS485 / Modbus](rs485-modbus.md). Per una spiegazione delle entità
sensore citate sotto, vedi
[Controlli quotidiani](../monitoring.md).

!!! note "Come leggere le etichette di affidabilità in questa pagina"
    Questo impianto non è ancora stato installato fisicamente. 🟢 VERIFICATO
    = confermato su banco di prova o sul campo. 🔵 PROGETTATO = costruito e
    pensato per funzionare così, ma non ancora provato contro un guasto
    reale. ⚠️ LACUNA NOTA = genuinamente irrisolto.

---

## La temperatura di una stanza sembra sbagliata, bloccata o mancante

**Sintomo:** La temperatura mostrata per una stanza smette di aggiornarsi,
salta a un valore strano, oppure un'entità diagnostica di "livello sensore"
mostra qualcosa di diverso dalla sorgente normale.

**Contesto — come viene scelta la lettura del sensore di stanza:** Ogni
temperatura (e umidità) di stanza ha fino a tre livelli, provati in ordine:

1. **Primario** — la lettura del sensore via bus CAN, ricevuta direttamente
   dal controller. Usato ogni volta che ha un valore reale.
2. **Secondario** — un sensore di Home Assistant, usato solo quando il
   primario non è disponibile.
3. **Emergenza** — usato quando *entrambi* i precedenti non sono
   disponibili. Il sistema non pubblica alcun numero utilizzabile
   (internamente, "non un numero" / NaN) per la temperatura di quella
   stanza.

Un'entità diagnostica associata (l'entità chiamata `..._sensor_tier`)
indica quale livello è attualmente attivo, così non devi indovinare — vedi
[Controlli quotidiani](../monitoring.md) per il pattern esatto di nomenclatura
delle entità.

**Importante — cosa significa davvero "bloccato in Emergenza":** Il livello
Emergenza scatta **immediatamente**, nel momento in cui sia la lettura
primaria che quella secondaria diventano non valide — non c'è alcun periodo
di attesa incorporato nella logica del sensore stesso. 🟢 VERIFICATO (letto
direttamente dal codice del componente di failover,
`climate/packages/components/failover_sensor.yaml`). Potresti trovare in
altri documenti del progetto un riferimento a un ritardo di "5 minuti" prima
di uno spegnimento di sicurezza — quella cifra descrive un'ipotesi su come
ci si aspetta che si comporti il ciclo di controllo della temperatura a
valle quando riceve per un po' una lettura non utilizzabile, non un timer
che esiste in questo codice di failover del sensore. Tratta un simile
ritardo come 🔵 PROGETTATO/non verificato, e non fare affidamento
sull'esistenza di un periodo di grazia a livello del sensore: se entrambi i
livelli del sensore diventano non validi, il ciclo di controllo della
stanza vede subito una lettura mancante.

**Cause probabili:**

- Livello Primario (CAN) fuori uso: un problema del bus CAN — vedi
  [Diagnosi bus CAN](canbus.md), in particolare le sezioni "un nodo non
  risponde" e "un segmento del bridge sembra fuori servizio".
- Anche il livello Secondario (HA) fuori uso: Home Assistant stesso
  irraggiungibile, oppure l'entità sensore HA sottostante non disponibile —
  vedi [Rete / Home Assistant](network.md).
- Entrambi fuori uso insieme: di solito significa che il percorso CAN si è
  guastato *e* Home Assistant era anch'esso offline/irraggiungibile nello
  stesso momento — controlla entrambi indipendentemente invece di supporre
  che uno abbia causato l'altro.

**Passi diagnostici:**

1. Controlla l'entità diagnostica `..._sensor_tier` di quella stanza per
   vedere quale livello è attualmente attivo.
2. Se è su Secondario, segui la checklist del bus CAN in
   [Diagnosi bus CAN](canbus.md).
3. Se è in Emergenza, controlla sia il percorso CAN che la connettività
   Home Assistant/rete — vedi [Rete / Home Assistant](network.md).

**Soluzione:** Ripristina qualunque percorso a monte (CAN o Home Assistant)
sia fuori uso; il livello del sensore recupera automaticamente e registra
il ripristino non appena una lettura valida torna disponibile — non serve
alcun reset manuale.

**Quando rivolgersi a un tecnico:** Se Primario e Secondario risultano
entrambi strutturalmente a posto (bus sano, HA raggiungibile) e la lettura
è comunque sbagliata, potrebbe essere un guasto hardware del sensore — vedi
[Sostituzione scheda sensore di stanza](../hardware/room-sensor.md).

---

## La temperatura di una zona oscilla, supera il target o non si stabilizza (taratura PID)

**Sintomo:** Una zona radiante o fancoil oscilla sopra e sotto la
temperatura target invece di stabilizzarsi, oppure risponde troppo
lentamente/troppo aggressivamente ai cambi di setpoint.

**Contesto:** Ogni zona usa un controllore PID (un algoritmo standard di
controllo a tre termini) con **impostazioni di guadagno separate per la
modalità riscaldamento e per la modalità raffrescamento** — ritarare una
modalità non influisce sull'altra. I sistemi a pavimento radiante sono
lenti (hanno bisogno di guadagni delicati e pazienti); i fancoil sono
veloci (possono usare guadagni più aggressivi). 🔵 PROGETTATO

**Cause probabili:**

- Guadagni troppo aggressivi per quel tipo di terminale (causa più comune
  di oscillazione).
- Guadagni troppo prudenti (causa più comune di risposta lenta/superamento
  del target per correzione troppo debole).
- Guadagni di modalità riscaldamento e raffrescamento confusi tra loro
  (taratura di una modalità quando il problema è in realtà nell'altra).

**Passi diagnostici:**

1. Conferma in quale modalità (riscaldamento o raffrescamento) si trova
   davvero la zona quando si presenta il problema — `hp_mode` (vedi la
   sezione sulla modalità stagionale sotto) governa questo, e ogni modalità
   ha i propri guadagni indipendenti.
2. Osserva il comportamento della zona per un ciclo completo di
   riscaldamento/raffrescamento, non solo per pochi minuti — i pavimenti
   radianti rispondono nell'arco di ore, quindi "oscillazioni" di breve
   periodo potrebbero essere solo un normale assestamento lento.

**Soluzione:**

1. **Usa prima l'auto-taratura.** Il componente di auto-taratura
   (`climate/packages/components/pid_autotune.yaml`) esiste apposta per
   evitare di indovinare i guadagni a mano — eseguilo prima di modificare i
   numeri manualmente.
2. **Se tarifichi a mano, parti prudente**: guadagno proporzionale (Kp)
   basso, guadagni integrale/derivativo (Ki/Kd) molto bassi, poi aumenta
   gradualmente osservando la stabilità. È molto più facile spingere verso
   l'alto un ciclo lento che calmare uno che oscilla.
3. Regola solo il set di guadagni della modalità in cui si presenta
   realmente il problema (riscaldamento e raffrescamento sono indipendenti).

**Quando rivolgersi a un tecnico:** Un'oscillazione persistente nonostante
guadagni prudenti e auto-tarati suggerisce un problema meccanico (es. una
valvola bloccata, una pompa che non gira, un relè che non commuta) piuttosto
che un problema di taratura — controlla l'attuatore interessato tramite
[RS485 / Modbus](rs485-modbus.md) o la pagina hardware corrispondente prima
di continuare a modificare i numeri del PID.

---

## La ventilazione (MEV) non si comporta come previsto

!!! warning "Lacuna nota"
    Oltre alla mappa dei registri usata per parlare con l'unità MEV via
    Modbus (`climate/mev_modbus.yaml`), questo progetto non ha ancora una
    documentazione di diagnosi dedicata alla MEV. L'elenco sotto è la base
    realmente nota, non una guida diagnostica completa — tratta qualsiasi
    cosa non elencata qui come non verificata. ⚠️ LACUNA NOTA

**Cosa si sa:**

- L'unità MEV (ventilazione meccanica controllata / ventilazione centralizzata
  della casa) si trova sul bus RS485 della climatizzazione all'indirizzo
  Modbus `0x10`.
- L'unità MEV è il membro del bus meno flessibile — le sue impostazioni di
  comunicazione predefinite di fabbrica sono meno regolabili rispetto alle
  altre schede sul bus, cosa che conta se stai diagnosticando un problema
  di comunicazione a livello dell'intero bus (vedi
  [RS485 / Modbus](rs485-modbus.md)) piuttosto che un problema specifico
  della ventilazione.
- La MEV espone un ampio insieme di indicatori di allarme e sensori di
  stato dei componenti (ventole, compressore, serrande, valvole, ore filtro
  rimanenti) via Modbus — se l'unità si comporta male, controlla prima
  quelle entità diagnostiche in Home Assistant, poiché l'unità segnala da
  sola le proprie condizioni di guasto in dettaglio.
- La velocità delle ventole è determinata dalla domanda (segnali di CO2,
  qualità dell'aria e umidità) piuttosto che fissa, quindi un cambio di
  velocità spontaneo in risposta a quelle letture è un comportamento
  atteso, non un guasto.

**Passi diagnostici:**

1. Controlla prima le entità di allarme/diagnostica della MEV in Home
   Assistant — un allarme attivo lì è l'unità che segnala da sola una
   condizione reale (inclusa la forzatura della velocità ventole a zero
   come risposta di sicurezza), non un problema di comunicazione.
2. Se non c'è alcun allarme attivo ma l'unità sembra non rispondere,
   trattalo come un problema di comunicazione RS485/Modbus — vedi
   [RS485 / Modbus](rs485-modbus.md), in particolare la sezione "alcuni
   dispositivi funzionano, altri no", poiché la MEV è spesso il dispositivo
   anomalo su un bus altrimenti sano.

**Quando rivolgersi a un tecnico:** Per qualsiasi cosa oltre le basi sopra
elencate, questa pagina non può ancora darti una risposta affidabile — vai
a [Sostituzione/assistenza unità MEV](../hardware/mev.md) oppure trattalo
come un problema di comunicazione del bus tramite
[RS485 / Modbus](rs485-modbus.md).

---

## Una zona non riscalda o non raffresca (controlla prima `hp_mode`)

**Sintomo:** Una zona che dovrebbe riscaldare (o raffrescare) non fa nulla,
oppure si comporta come se fosse nella modalità sbagliata.

**Contesto:** La casa ha **una sola pompa di calore che produce, per tutta
la casa e in un dato momento, o acqua calda o acqua refrigerata** — non
esiste un relè di commutazione né un rilevamento automatico di quale delle
due stia producendo. Un'impostazione software chiamata `hp_mode` (un'entità
di selezione, non un comando fisico) dice al controllore PID di ogni zona
in quale modalità operare — riscaldamento o raffrescamento — e deve essere
**mantenuta sincronizzata manualmente** con ciò che la pompa di calore sta
realmente producendo alla fonte. 🔵 PROGETTATO

Questo significa che `hp_mode` non *comanda* la pompa di calore — si limita
a rispecchiare ciò che l'installatore/tecnico ha impostato sulla pompa di
calore stessa. Se `hp_mode` dice "riscaldamento" mentre la pompa di calore
sta in realtà producendo acqua refrigerata (o viceversa), le zone si
comporteranno in modo scorretto anche se ogni componente hardware sta
funzionando esattamente come istruito.

**Cause probabili:**

- `hp_mode` è in disaccordo con ciò che la pompa di calore sta realmente
  producendo in questo momento (di gran lunga la causa più comune di
  segnalazioni "non succede nulla" o "comportamento sbagliato").
- `hp_mode_manual_hold` è attivo (il suo stato predefinito) e nessuno ha
  ancora impostato `hp_mode` in base alla stagione — questo è atteso su un
  sistema appena messo in servizio, non un guasto.

**Passi diagnostici:**

1. **Controlla `hp_mode` prima di ogni altra cosa.** Conferma che
   corrisponda a ciò che la pompa di calore sta realmente producendo alla
   fonte in questo momento — chiedi a chi gestisce la pompa di calore se
   non sei sicuro.
2. Solo una volta confermato che `hp_mode` è corretto, tratta il problema
   come un vero guasto di zona/attuatore e passa alle sezioni RS485/Modbus
   o PID sopra.

**Soluzione:** Imposta `hp_mode` in base alla stagione che la pompa di
calore sta realmente producendo. Questo è un passo manuale per progetto —
non esiste un rilevamento automatico della commutazione su cui fare
affidamento.

**Quando rivolgersi a un tecnico:** Solo dopo aver confermato che `hp_mode`
è corretto e la zona continua a non riscaldare/raffrescare, trattalo come
un guasto hardware — controlla il relè/valvola/pompa interessati tramite
[RS485 / Modbus](rs485-modbus.md) o la pagina hardware corrispondente.
