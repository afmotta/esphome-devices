# Bus CAN — Diagnosi e soluzione: problemi comuni

Il bus CAN è il cablaggio che porta le pressioni dei pulsanti a muro (i
"nodi") ai due dispositivi controller che ascoltano il bus: il
**controller illuminazione**, che trasforma la pressione di un pulsante in
un'azione sulle luci, e il **monitor di salute del bus** (health monitor),
che verifica che tutti i nodi siano ancora vivi. Questa pagina copre i
problemi relativi a questo cablaggio e ai nodi/monitor stessi — non a cosa
*fa* la pressione di un pulsante (per quello vedi
[Illuminazione](lighting.md)) e non al cablaggio RS485/Modbus separato
usato per relè e I/O della climatizzazione (vedi
[RS485 / Modbus](rs485-modbus.md)).

!!! note "Come leggere le etichette di affidabilità in questa pagina"
    Questo impianto non è ancora stato installato fisicamente in casa (è
    "pre-live"), quindi quasi nulla qui è stato testato contro un guasto
    reale sul campo. Ogni affermazione tecnica non banale è etichettata:

    - 🟢 **VERIFICATO** — confermato su banco di prova o sul campo.
    - 🔵 **PROGETTATO** — costruito e pensato per funzionare così, ma non
      ancora provato contro un guasto reale.
    - ⚠️ **LACUNA NOTA** — genuinamente irrisolto; dichiarato apertamente
      invece di essere indovinato.

---

## Un nodo non risponde / Home Assistant lo mostra come "perso"

**Sintomo:** Una scheda pulsanti a muro smette di reagire alle pressioni,
oppure una notifica/entità di Home Assistant segnala che un nodo è mancante
o perso.

**Cause probabili:**

- Il nodo ha perso l'alimentazione (fusibile saltato, filo scollegato,
  alimentatore guasto).
- Il cablaggio CAN del nodo, nel punto di derivazione (tap), si è allentato
  o rotto.
- Il segmento locale del nodo ha perso il percorso verso il controller (vedi
  la sezione sul bridge più sotto).
- Il nodo stesso si è guastato (raro, ma possibile).

**Passi diagnostici:**

1. In Home Assistant, controlla le entità diagnostiche del monitor di
   salute: **Nodi Online**, **Nodi Totali** e **Nodi Mancanti** (quest'ultima
   indica il nome dei nodi mancanti). Queste sono entità aggregate
   pubblicate dal monitor di salute, quindi sopravvivono a riavvii e
   riconnessioni di Home Assistant. 🔵 PROGETTATO
2. Ogni nodo e ogni bridge invia un heartbeat (segnale di vita) ogni 30
   secondi. Un nodo viene dichiarato "perso" dopo **3 heartbeat mancati di
   fila — 90 secondi totali** di silenzio. Un singolo heartbeat mancato non
   è quindi ancora un guasto: aspetta i 90 secondi completi prima di
   presumere un problema reale. 🔵 PROGETTATO (questa regola di
   temporizzazione è implementata ed è coperta da test automatici della
   logica, ma non è ancora stata verificata contro un guasto reale su banco
   o sul campo)
3. Se Home Assistant conferma che il nodo è perso, vai a controllare
   fisicamente quel nodo: è alimentato? Il connettore del cavo CAN nel suo
   punto di derivazione è ben inserito e integro?
4. Se alimentazione e cablaggio in quel punto sembrano a posto, controlla se
   anche *altri* nodi sullo stesso tratto fisico risultano mancanti. Più
   nodi che spariscono insieme indicano una causa comune — un'interruzione
   del cablaggio a monte di tutti loro, o un bridge morto (vedi sotto) —
   piuttosto che un singolo nodo guasto.

**Soluzione:**

- Connettore CAN allentato o danneggiato: reinseriscilo o riparalo.
- Nodo senza alimentazione: risali fino alla sorgente di alimentazione di
  quel punto.
- Nodo effettivamente morto (alimentato, cablato correttamente, ancora
  silenzioso): serve la sostituzione fisica — vedi
  [Sostituzione nodo CAN](../hardware/can-node.md).

**Quando rivolgersi a un tecnico:** Se i controlli 3-4 escludono
alimentazione e cablaggio, o se non ti senti sicuro ad aprire hardware
installato a muro, tratta il problema come una questione hardware e vai a
[Sostituzione nodo CAN](../hardware/can-node.md) invece di continuare a
tentare.

---

## Un click, una pressione prolungata o un rilascio di un pulsante non vengono registrati correttamente

**Sintomo:** Un pulsante sembra non rispondere, scatta due volte, oppure un
gesto di pressione prolungata/rilascio (es. tieni premuto per attenuare la
luce) non si comporta come previsto, pur risultando il nodo online.

**Cause probabili:**

- Guasto di cablaggio sulla connessione di quello specifico pulsante,
  dentro il nodo (contatto allentato, interruttore danneggiato).
- Il nodo esegue una versione firmware più vecchia rispetto al resto della
  flotta — la temporizzazione di click/pressione prolungata (inclusa la
  soglia di 800 ms prima che una pressione venga contata come "hold") è
  incorporata nel firmware al momento della programmazione e non può essere
  cambiata da remoto. 🔵 PROGETTATO
- Molto raramente è un difetto di progettazione del sistema di gesti in sé:
  click, doppio click, triplo click, hold e hold-release sono un insieme di
  comportamenti ben definito e testato. Se un solo pulsante si comporta
  male mentre tutto il resto funziona, considera prima un problema hardware
  o di versione firmware su quel nodo.

**Passi diagnostici:**

1. Conferma che il nodo sia online (vedi la sezione precedente).
2. Prova lo stesso gesto fisico su un pulsante *diverso* dello stesso tipo
   di nodo. Se lì funziona bene, il problema è locale a questo nodo o a
   questo specifico pulsante.
3. Controlla quando questo nodo è stato riprogrammato l'ultima volta,
   rispetto al resto della flotta. I nodi pulsante a muro non hanno WiFi né
   aggiornamenti via rete (OTA) — ricevono modifiche firmware solo quando
   qualcuno collega fisicamente un cavo USB e li riprogramma, quindi è
   facile che un nodo resti indietro senza che nessuno se ne accorga.
4. Se possibile, apri il nodo e controlla il cablaggio/interruttore di
   quello specifico pulsante, cercando un contatto allentato o usurato.

**Soluzione:**

- Disallineamento firmware: riprogramma il nodo via USB con il firmware
  corrente.
- Guasto di cablaggio/interruttore: ripara la connessione, oppure sostituisci
  il nodo se l'interruttore stesso è guasto — vedi
  [Sostituzione nodo CAN](../hardware/can-node.md).

**Quando rivolgersi a un tecnico:** Se il pulsante continua a comportarsi
male dopo aver confermato che il firmware è aggiornato e il cablaggio sembra
integro, passa a [Sostituzione nodo CAN](../hardware/can-node.md).

---

## `ha_ready` risulta falso, oppure il sistema passa al controllo relè locale quando non dovrebbe

**Sintomo:** Le luci iniziano a comportarsi come se Home Assistant fosse
offline — solo accensione/spegnimento semplice, niente dimmerazione, niente
scene — anche se Home Assistant ti sembra funzionare normalmente. Oppure
un'entità diagnostica chiamata `ha_ready` mostra `false`.

**Cosa significa realmente:** `ha_ready` non è una proprietà di un singolo
nodo pulsante — i nodi non sanno né si preoccupano se Home Assistant è
raggiungibile. È un "cancello di prontezza" (readiness gate) calcolato dal
**controller illuminazione**, il dispositivo che decide se passare la
pressione di un pulsante a Home Assistant (il percorso ricco: dimmerazione,
scene, colore) oppure agire immediatamente usando la propria logica relè
locale (il percorso di riserva resiliente, così le luci continuano a
funzionare se Home Assistant è irraggiungibile). Questo meccanismo esiste
apposta perché la casa continui a funzionare quando Home Assistant non è
raggiungibile. 🔵 PROGETTATO

Il controller illuminazione considera Home Assistant "pronto" solo quando
**tutte** le condizioni seguenti sono vere:

1. La sua connessione API verso Home Assistant è attiva.
2. Home Assistant ha inviato di recente un heartbeat di prontezza aggiornato
   (entro un tempo limite configurato).
3. L'hash del manifesto dei binding riportato da Home Assistant coincide con
   quello compilato nel controller — cioè Home Assistant e il controller
   sono d'accordo su cosa deve fare ciascun pulsante.

**Cause probabili (in ordine approssimativo di probabilità):**

- Home Assistant stesso è offline, in fase di riavvio o irraggiungibile
  in rete.
- Il controller illuminazione ha perso la connettività di rete (cavo
  Ethernet, porta dello switch, problema DHCP/IP) — vedi
  [Rete / Home Assistant](network.md).
- Il manifesto dei binding (`registry/bindings.yaml`, che definisce cosa fa
  ogni pulsante) è stato modificato e inviato a Home Assistant, ma il
  controller illuminazione non è mai stato riprogrammato con
  l'aggiornamento corrispondente — quindi i due lati hanno hash diversi.
  Questa è una lacuna nel processo di manutenzione, non un guasto.
- L'automazione di heartbeat di prontezza in Home Assistant non è in
  esecuzione (es. l'automazione è stata disabilitata o cancellata).

**Passi diagnostici:**

1. Verifica se Home Assistant stesso è raggiungibile e in buono stato —
   questa è la causa più comune, e *non* è un guasto di nodo o di bus.
2. Controlla la connettività di rete del controller illuminazione.
3. Se entrambi sembrano a posto, sospetta un disallineamento dell'hash del
   manifesto: `registry/bindings.yaml` è stato modificato di recente senza
   riprogrammare il controller illuminazione?

**Soluzione:**

- Ripristina la connettività a Home Assistant/rete — `ha_ready` dovrebbe
  recuperare automaticamente non appena la condizione sottostante si
  risolve.
- Disallineamento del manifesto: rigenera e invia gli artefatti dei binding
  aggiornati, poi riprogramma il controller illuminazione così i due lati
  tornano d'accordo.

**Quando rivolgersi a un tecnico:** Questo non è quasi mai un motivo per
sostituire hardware CAN — è un problema di connettività o configurazione a
monte del bus. Se sia Home Assistant che la rete risultano a posto e
`ha_ready` non si riprende comunque, vale la pena trattarlo come
un'indagine software/configurazione, non hardware.

---

## Un segmento del bridge CAN sembra fuori servizio

**Contesto:** Il bus CAN della casa è diviso in segmenti collegati da
piccoli dispositivi bridge (`devices/bridge.yaml`), invece di un unico
cavo continuo. Un bridge si limita a inoltrare il traffico tra il segmento
su cui si trova e il resto del bus.

**Sintomo:** Tutti i nodi su un particolare segmento risultano mancanti/
persi contemporaneamente, mentre i nodi altrove funzionano normalmente.

**Cosa significa realmente:** Il bridge è progettato deliberatamente per
guastarsi in modo sicuro. Ha un watchdog hardware e un rilevatore di
brownout, quindi se si blocca si riavvia da solo invece di restare bloccato
in uno stato problematico. E se si guasta, è progettato per diventare
**silenzioso** — smette semplicemente di inoltrare traffico — piuttosto che
bloccare il bus o inondarlo di dati spuri. 🔵 PROGETTATO Per questo un
bridge morto si manifesta come "un intero segmento è diventato silenzioso
tutto insieme", non come caos su tutta la casa.

Se il bridge è mai costretto a scartare frame perché la sua coda interna si
è riempita, imposta un indicatore `ERR_BRIDGE_QUEUE_OVERFLOW` nel proprio
heartbeat, che resta impostato finché il bridge non viene spento e
riacceso — così un sovraccarico temporaneo lascia una traccia visibile
invece di scomparire silenziosamente. 🔵 PROGETTATO

**Cause probabili:**

- Il bridge ha perso alimentazione.
- Il bridge stesso ha bisogno di un riavvio (il watchdog dovrebbe già
  gestire i blocchi, ma un ciclo di spegnimento/accensione completo è il
  reset manuale più semplice).
- Un guasto di cablaggio tra il bridge e quel segmento.

**Passi diagnostici:**

1. Conferma che si tratti davvero di "un intero segmento in blocco" e non
   di nodi singoli sparsi — quel pattern è la firma tipica di un problema
   di bridge, non di un problema per singolo nodo.
2. Controlla lo stato/heartbeat del bridge stesso, se visibile in Home
   Assistant, incluso se l'indicatore di overflow sopra descritto è
   impostato.
3. Controlla fisicamente che il bridge sia alimentato e che le sue
   connessioni CAN (sia lato segmento che lato dorsale) siano integre.

**Soluzione:**

- Spegni e riaccendi il bridge — questo azzera anche un indicatore di
  overflow rimasto impostato.
- Ripara cablaggio allentato o danneggiato sui connettori del bridge.

**Quando rivolgersi a un tecnico:** Se il bridge è alimentato, il cablaggio
sembra a posto e un ciclo di spegnimento/accensione non riporta il segmento
online, trattalo come hardware guasto — vedi
[Sostituzione bridge CAN](../hardware/bridge.md). Se invece sono nodi
singoli sparsi su *più* segmenti a risultare mancanti (non un unico
segmento pulito), rivolgiti invece alle pagine
[nodo](../hardware/can-node.md) o
[monitor di salute](../hardware/health-monitor.md).
