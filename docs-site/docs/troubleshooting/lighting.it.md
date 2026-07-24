# Illuminazione — Diagnosi e soluzione: problemi comuni

Il sistema di illuminazione trasforma la pressione dei pulsanti a muro in
azioni sulle luci. Le pressioni dei pulsanti arrivano tramite il bus CAN
(infrastruttura condivisa — vedi [Diagnosi bus CAN](canbus.md) per problemi
di cablaggio/nodi) e vengono decodificate dal **controller illuminazione**,
che o passa la pressione a Home Assistant (per un comportamento ricco come
dimmerazione e scene) oppure, se Home Assistant non è raggiungibile, agisce
direttamente usando il proprio banco relè via RS485 (vedi
[RS485 / Modbus](rs485-modbus.md) per quel bus). Questa pagina copre
problemi specifici di quella logica decisionale e della mappatura
pulsante→luce.

!!! warning "Questa pagina è nuova"
    A differenza delle altre pagine di diagnosi, non esiste alcuna
    documentazione di diagnosi preesistente da nessuna parte nel progetto a
    cui attingere per il sistema di illuminazione — il sistema è reale ma
    non ancora installato fisicamente, e non si è ancora verificato alcun
    guasto sul campo. Tutto quanto segue è ragionato a partire dai documenti
    di progettazione del sistema, non dall'esperienza di riparare un guasto
    reale. Trattalo di conseguenza. 🔵 PROGETTATO in tutta la pagina salvo
    diversa indicazione.

!!! note "Come leggere le etichette di affidabilità in questa pagina"
    🟢 VERIFICATO = confermato su banco di prova o sul campo. 🔵 PROGETTATO
    = costruito e pensato per funzionare così, ma non ancora provato contro
    un guasto reale. ⚠️ LACUNA NOTA = genuinamente irrisolto.

---

## Un relè non risponde a un comando da Home Assistant o a una pressione di pulsante

**Sintomo:** Attivare una luce da Home Assistant non fa nulla, oppure
premere il suo pulsante a muro non fa nulla (o fa la cosa sbagliata).

**Passi diagnostici, in ordine (ognuno esclude un livello prima di passare
al successivo):**

1. **Controlla che il controller e Home Assistant siano d'accordo su cosa
   fa il pulsante.** Il controller illuminazione e Home Assistant lavorano
   entrambi a partire dallo stesso "manifesto dei binding" — il file che
   mappa ogni pulsante a un'azione sui relè — e ciascun lato porta un hash
   (un'impronta) di quel manifesto. Se il manifesto è stato modificato e
   inviato a un lato ma il controller non è stato riprogrammato con
   l'aggiornamento (o viceversa), i due lati sono in disaccordo su cosa
   dovrebbe accadere, e il disallineamento influisce anche sul cancello di
   prontezza descritto nella sezione successiva. Vedi
   [Controlli quotidiani](../monitoring.md) per dove controllare questo.
2. **Controlla il bus relè RS485 condiviso.** Il controller illuminazione
   comanda il proprio banco relè tramite il proprio bus RS485/Modbus — lo
   stesso tipo di bus usato dal sistema di climatizzazione (un bus separato
   e indipendente, non lo stesso cavo, ma cablato e diagnosticato allo
   stesso modo). Vedi [RS485 / Modbus](rs485-modbus.md) per il flusso
   diagnostico completo (nessuna comunicazione / intermittente / alcuni
   dispositivi non rispondono / tasso di errore elevato).
3. **Controlla la scheda relè stessa.** Se il bus risulta a posto (il
   controller riesce a raggiungere altri canali sulla stessa scheda) ma un
   canale relè specifico non risponde mai, la scheda o quel canale
   potrebbero essersi guastati.

**Soluzione:** Dipende da quale livello sopra si è rivelato il problema —
rigenera/invia il manifesto dei binding e riprogramma se è un
disallineamento, segui le soluzioni RS485 se è un problema di bus, oppure
sostituisci la scheda se un canale specifico si è guastato.

**Quando rivolgersi a un tecnico:** Una volta confermato che il bus stesso
è sano e gli hash del manifesto sono d'accordo, ma un canale relè specifico
continua a non rispondere, vai a
[Sostituzione scheda relè](../hardware/relay-board.md).

---

## Il sistema passa al controllo semplice on/off a ogni pressione di pulsante, anche quando Home Assistant sembra funzionare bene

**Sintomo:** Le luci si accendono/spengono solo in modo completo — niente
dimmerazione, niente scene — anche se Home Assistant sembra funzionare
normalmente. Un'entità diagnostica `ha_ready`, se visibile, mostra `false`.

**Contesto:** Questo è lo stesso meccanismo di arbitraggio usato altrove
nella casa (condiviso con la progettazione del monitoraggio di salute del
bus CAN): il controller illuminazione passa una pressione di pulsante a
Home Assistant solo quando è sicuro che Home Assistant sia realmente pronto
— API connessa, un segnale di prontezza recente ricevuto, e gli hash del
manifesto dei binding dei due lati che coincidono. Se anche una sola di
queste condizioni non è vera, il controller ripiega sull'agire da solo sulla
pressione, usando solo la logica semplice "commuta il relè N" incorporata —
questo è intenzionale, così le luci continuano comunque a funzionare quando
Home Assistant non è raggiungibile, ma significa che il comportamento
"ricco" è temporaneamente non disponibile. Vedi
[Diagnosi bus CAN](canbus.md#ha_ready-risulta-falso-oppure-il-sistema-passa-al-controllo-rele-locale-quando-non-dovrebbe)
per la spiegazione completa di questo meccanismo, che si applica
identicamente qui.

**Cause probabili:** Le stesse della sezione `ha_ready` della pagina bus
CAN — quasi sempre Home Assistant stesso, la connettività di rete, o un
manifesto dei binding non aggiornato, e quasi mai il nodo pulsante che si è
appena premuto.

**Passi diagnostici:**

1. Conferma che Home Assistant sia effettivamente raggiungibile e in
   esecuzione.
2. Controlla la connettività di rete del controller illuminazione stesso —
   vedi [Rete / Home Assistant](network.md).
3. Controlla un possibile disallineamento dell'hash del manifesto (modificato
   ma non inviato/riprogrammato su entrambi i lati).

**Soluzione:** Ripristina qualunque condizione a monte stia fallendo; il
cancello di prontezza recupera da solo una volta risolta la causa
sottostante — non è richiesto alcun reset manuale.

**Quando rivolgersi a un tecnico:** Questo è un problema di
connettività/configurazione, non un guasto hardware — non è quasi mai un
motivo per sostituire hardware CAN o relè. Se Home Assistant, la rete e
l'hash del manifesto risultano tutti a posto e il ripiego non si sblocca
comunque, trattalo come un'indagine software.

---

## La pressione di un pulsante non produce l'azione luminosa attesa

**Sintomo:** Il pulsante viene chiaramente registrato (il nodo non è il
problema — vedi [Diagnosi bus CAN](canbus.md) se non ne sei sicuro), ma non
succede nulla, oppure risponde la luce/il relè sbagliato.

**Contesto:** Cosa fa uno specifico pulsante — quale/i relè controlla, e
quale azione (on/off/toggle) — è definito da una voce di binding esplicita
per quella precisa coppia `(nodo, pulsante)`. **Solo il click singolo ha
un'azione di ripiego definita** quando Home Assistant è irraggiungibile;
doppio click, triplo click e i gesti hold/hold-release sono
esclusivamente per Home Assistant per progetto, quindi se Home Assistant è
offline, quei gesti semplicemente non fanno nulla — è atteso, non un
difetto. Anche un pulsante senza alcuna voce di binding non fa nulla, per
progetto (non è uno stato di errore, solo "non ancora configurato").

**Passi diagnostici:**

1. Conferma quale gesto stai testando. Se è diverso dal click singolo, e il
   sistema è attualmente in modalità di ripiego locale (vedi la sezione
   precedente), ci si aspetta che quel gesto non faccia nulla in questo
   momento — controlla prima `ha_ready`.
2. Controlla se quel preciso pulsante ha una voce di binding e se questa
   corrisponde al relè/azione che ti aspetti. Il manifesto dei binding è la
   fonte di verità per questa mappatura.
3. Controlla se un binding aggiunto o modificato di recente è stato
   effettivamente generato e inviato sia a Home Assistant che al
   controller, e se il controller è stato riprogrammato da allora — un
   binding modificato ma non ancora distribuito appare identico a "non è
   successo nulla" dal punto di vista del pulsante. Vedi
   [Manutenzione ordinaria](../maintenance-tasks.md) per la sequenza
   invio/rigenerazione/riprogrammazione.

**Soluzione:** Aggiungi o correggi la voce di binding per quel pulsante,
poi esegui il passo di generazione e invia/riprogramma entrambi i lati così
il controller e Home Assistant tornano d'accordo.

**Quando rivolgersi a un tecnico:** Se il binding è confermato corretto e
distribuito su entrambi i lati, e il pulsante continua a non fare la cosa
giusta, trattalo come un problema di relè/cablaggio — vedi
[RS485 / Modbus](rs485-modbus.md) o
[Sostituzione scheda relè](../hardware/relay-board.md).
