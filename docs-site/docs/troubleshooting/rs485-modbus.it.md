# RS485 / Modbus — Diagnosi e soluzione: problemi comuni

RS485 è il bus cablato che porta i comandi tra un controller e le schede
I/O "senza intelligenza propria" che comanda — banchi relè, schede di
uscita analogica e l'unità di ventilazione (MEV). Modbus RTU è il formato
dei messaggi usato su quel cavo. Questo bus è **infrastruttura condivisa
usata da entrambi i sistemi applicativi della casa**:

- Il sistema di **climatizzazione** ha un proprio bus RS485, sul controller
  climatizzazione, che parla con una scheda uscite analogiche, una scheda
  relè e l'unità MEV.
- Il sistema di **illuminazione** ha un bus RS485 separato e indipendente,
  sul controller illuminazione, che parla con una propria scheda relè.

Si tratta di due bus fisicamente separati (non lo stesso cavo condiviso),
ma seguono regole di cablaggio identiche, e l'indirizzo Modbus della scheda
relè (`0x2`) è deliberatamente identico su entrambi — così una singola
scheda relè di scorta funziona come sostituzione diretta su entrambi i bus,
senza bisogno di riconfigurare l'indirizzo. Entrambi i bus puntano a
**38400 baud, 8 bit dati, parità pari, 1 bit di stop ("38400 8E1")**. 🔵
PROGETTATO — questa è la configurazione obiettivo; l'accordo su
parità/velocità tra tutte le schede di ciascun bus deve ancora essere
verificato fisicamente in fase di avvio.

Se il problema riguarda specificamente i sensori di temperatura/comfort di
una stanza, questi **non** passano affatto per questo bus (arrivano via bus
CAN con un ripiego su Home Assistant) — vedi invece
[Climatizzazione](climate.md). Se il problema è una luce che non risponde a
un interruttore, inizia da [Illuminazione](lighting.md), che ti rimanda
qui se il sospetto è il bus stesso.

!!! note "Come leggere le etichette di affidabilità in questa pagina"
    Questo impianto non è ancora stato installato fisicamente. 🟢 VERIFICATO
    = confermato su banco di prova o sul campo. 🔵 PROGETTATO = costruito e
    pensato per funzionare così, ma non ancora provato contro un guasto
    reale. ⚠️ LACUNA NOTA = genuinamente irrisolto.

---

## Nessuna comunicazione

**Sintomo:** I log del controller mostrano che ogni dispositivo sul bus non
risponde (errori "nessuna risposta", timeout su ogni interrogazione), non
solo uno.

**Cause probabili:**

- Uno o più dispositivi non sono accesi.
- Il cablaggio A/B è interrotto, invertito o scollegato da qualche parte sul
  bus.
- Disallineamento di velocità (baud rate) o parità tra il controller e le
  schede I/O.
- Resistenze di terminazione mancanti, che causano riflessioni del segnale
  abbastanza gravi da bloccare completamente la comunicazione.

**Passi diagnostici:**

1. **Controlla l'alimentazione** su ogni dispositivo del bus — LED di
   alimentazione accesi, tensione corretta per ciascun dispositivo.
2. **Controlla la continuità del cablaggio**: a tutto spento, usa un
   multimetro per confermare che la continuità A-A e B-B corra per tutto il
   percorso dal controller fino all'ultimo dispositivo, e che non ci sia
   corto A-B.
3. **Controlla la configurazione**: tutti i dispositivi sul bus concordano
   su 38400 8E1? Le schede Waveshare escono di fabbrica configurate a 9600
   8N1 e devono essere riconfigurate ai parametri obiettivo del bus prima
   del primo utilizzo — una scheda non riconfigurata è una causa classica
   di "nessuna comunicazione". L'unità MEV è il membro del bus meno
   flessibile (il suo stesso default di fabbrica è 9600 8N1): se non può
   essere portata a 38400 8E1, potrebbe essere necessario riconciliare
   l'intero bus su ciò che la MEV riesce effettivamente a fare, invece di
   forzare la MEV ad adeguarsi alle altre schede. 🔵 PROGETTATO
4. **Controlla la terminazione**: spegni il bus, scollega la coppia A/B dal
   controller e misura la resistenza tra A e B con un multimetro. Vedi
   [Verifica delle resistenze di terminazione](#verifica-delle-resistenze-di-terminazione)
   più sotto.
5. **Isola**: scollega ogni dispositivo tranne il controller. Il controller
   dovrebbe segnalare "nessuna risposta" per tutto (atteso — nessuno slave è
   collegato). Ricollega i dispositivi uno alla volta finché la
   comunicazione non riprende; il dispositivo appena aggiunto quando torna a
   rompersi è il sospetto principale, oppure il tratto di cablaggio che
   porta ad esso.

**Soluzione:**

- Accendi qualsiasi dispositivo spento.
- Ripara cablaggio interrotto/invertito; reinserisci e stringi tutte le viti
  delle morsettiere.
- Riconfigura una scheda ancora sul default di fabbrica 9600 8N1 portandola
  all'obiettivo del bus, 38400 8E1 (consulta il manuale di quella scheda per
  la procedura).
- Installa le resistenze di terminazione mancanti (vedi sotto).

**Quando rivolgersi a un tecnico:** Se cablaggio, alimentazione e
configurazione risultano tutti a posto e il bus continua a non mostrare
alcuna comunicazione, il trasmettitore RS485 del controller stesso potrebbe
essere il problema — vedi
[Sostituzione controller](../hardware/controller.md).

---

## Comunicazione intermittente (funziona, poi si interrompe, poi riprende)

**Sintomo:** La comunicazione funziona per lo più ma si interrompe in modo
imprevedibile. I log mostrano occasionali errori CRC (checksum), circa
l'1-10% delle interrogazioni fallisce.

**Cause probabili:**

- Resistenze di terminazione mancanti o mal inserite, che causano
  riflessioni che corrompono alcuni messaggi ma non tutti.
- Connessioni delle morsettiere allentate (contatto intermittente).
- Interferenze elettromagnetiche (EMI) da cavi di potenza vicini, plafoniere
  fluorescenti o inverter/variatori di frequenza.
- Un tratto di cavo vicino alla lunghezza massima per la velocità in uso.

**Passi diagnostici:**

1. Verifica la resistenza di terminazione (vedi sotto) — un terminatore
   mancante causa spesso esattamente questo pattern di "funziona quasi
   sempre", piuttosto che silenzio totale.
2. Reinserisci e stringi ogni connessione a morsettiera sul bus; una vite
   allentata può causare un contatto che va e viene con vibrazioni o
   variazioni di temperatura.
3. Se il cavo RS485 corre parallelo a cablaggio di potenza da qualche parte,
   o passa vicino a note fonti di EMI, prova a spostarlo (la regola generale
   è almeno 30 cm di distanza dai cavi di potenza) e osserva se il tasso di
   errore cambia.
4. Controlla la lunghezza totale del cavo rispetto al limite per 38400 baud
   (500 m) — vedi
   [Indicazioni sulla lunghezza del cavo](#indicazioni-sulla-lunghezza-del-cavo)
   più sotto.

**Soluzione:**

- Installa/reinserisci le resistenze di terminazione.
- Stringi tutte le connessioni delle morsettiere.
- Sposta il cavo lontano da fonti EMI o cablaggio di potenza.
- Se la lunghezza è al limite, considera una velocità inferiore come passo
  *solo diagnostico* temporaneo (non una soluzione permanente — vedi
  "Tasso di errore elevato" sotto), oppure un ripetitore se il tratto è
  davvero troppo lungo.

**Quando rivolgersi a un tecnico:** Se gli errori intermittenti persistono
dopo aver confermato terminazione, connessioni e instradamento del cavo,
trattalo come possibile problema di qualità del cavo o dei connettori e
valuta la sostituzione del tratto di cavo interessato.

---

## Alcuni dispositivi funzionano, altri no

**Sintomo:** Il controller comunica bene con alcuni dispositivi sul bus
(es. la scheda relè) ma non con altri (es. la scheda uscite analogiche o
la MEV), anche se sono tutti sullo stesso tratto fisico.

**Cause probabili:**

- Indirizzo Modbus duplicato o errato sul dispositivo che non risponde.
- Un'interruzione del cablaggio specificamente tra l'ultimo dispositivo
  funzionante e il primo non funzionante.
- Il dispositivo che non risponde si è guastato o ha perso alimentazione.

**Passi diagnostici:**

1. **Controlla gli indirizzi.** Ogni dispositivo su un bus deve avere un
   indirizzo Modbus univoco. Sul bus climatizzazione: scheda uscite
   analogiche = `0x1`, scheda relè = `0x2`, MEV = `0x10`. Sul bus
   illuminazione: scheda relè = `0x2`. Un indirizzo duplicato o
   configurato male rende un dispositivo silenziosamente irraggiungibile
   (oppure lo fa rispondere alle interrogazioni destinate a un altro
   dispositivo).
2. **Controlla il cablaggio verso il/i dispositivo/i non funzionante/i**:
   A/B non invertiti, continuità intatta dal dispositivo precedente nella
   catena.
3. **Isola con un test di bypass**: scollega temporaneamente il dispositivo
   sospetto e ponticella i fili A/B direttamente verso ciò che viene dopo
   nel bus. Se i dispositivi più a valle nella catena ricominciano a
   funzionare, il dispositivo scollegato (o il cablaggio immediatamente
   verso di esso) era il problema.

   ```
   Prima:
   Controller ─── Dispositivo 1 ─── Dispositivo 2 ─── Dispositivo 3
                                    (dispositivo 3 irraggiungibile)

   Test di bypass (salta il cablaggio del Dispositivo 2, ponticella diretta):
   Controller ─── Dispositivo 1 ──┐         ┌── Dispositivo 3
                                   └─────────┘

   Se ora il Dispositivo 3 risponde, il Dispositivo 2 (o il suo cablaggio)
   è il guasto.
   ```

4. Controlla l'alimentazione propria del dispositivo guasto.

**Soluzione:**

- Correggi un indirizzo duplicato/errato.
- Ripara il tratto di cablaggio individuato dal test di bypass.
- Sostituisci un dispositivo confermato guasto dal test di bypass — vedi
  [Sostituzione scheda relè](../hardware/relay-board.md),
  [Sostituzione scheda uscite analogiche](../hardware/analog-board.md), o
  [Sostituzione MEV](../hardware/mev.md) a seconda dei casi.

**Quando rivolgersi a un tecnico:** Una volta che il test di bypass ha
isolato un dispositivo o un tratto di cavo specifico, vai direttamente alla
pagina hardware corrispondente invece di continuare a testare.

---

## Tasso di errore elevato (>5%)

**Sintomo:** Il bus comunica per lo più, ma gli errori CRC sono frequenti e
i dati appaiono a volte corrotti o inaffidabili.

**Cause probabili:**

- Problemi di terminazione o riflessione (stesse cause di base della
  comunicazione intermittente, ma più gravi).
- Cavo di scarsa qualità o non schermato.
- Anelli di massa (ground loop) dovuti a schermatura collegata a terra a
  entrambe le estremità invece che a una sola.
- Forte EMI.

**Passi diagnostici:**

1. Riverifica la resistenza di terminazione (sotto).
2. Conferma che il cavo sia a coppia intrecciata e schermato, e che la
   schermatura sia collegata a terra **solo** lato controller — collegarla
   a terra a entrambe le estremità crea un anello di massa che inietta
   rumore.
3. Come passo *solo diagnostico*, abbassa temporaneamente la velocità
   (es. a 9600) su ogni dispositivo del bus contemporaneamente. Velocità
   più basse tollerano meglio il rumore; se il tasso di errore scende
   nettamente, questo conferma un problema di qualità del segnale piuttosto
   che di configurazione. Riporta poi la velocità a 38400 — è un test, non
   una soluzione, e ogni dispositivo sul bus deve cambiare insieme, altrimenti
   nulla comunicherà più.
4. Se hai accesso a un oscilloscopio, bordi arrotondati sulla forma d'onda
   indicano riflessioni (terminazione), mentre picchi di rumore indicano
   EMI.

**Soluzione:**

- Correggi la terminazione.
- Sostituisci cavo non schermato/di scarsa qualità con doppino schermato
  (un cavo Ethernet Cat5e/Cat6, usando una sola coppia, funziona bene ed è
  facile da reperire).
- Collega la schermatura a terra a una sola estremità.
- Allontana il cavo da cablaggio di potenza e altre fonti di EMI.

**Quando rivolgersi a un tecnico:** Se il tasso di errore resta alto dopo
aver confermato terminazione, cablaggio e messa a terra corretti, vale la
pena trattarlo come un guasto hardware nel trasmettitore RS485 del
controller o in una specifica scheda I/O — vedi
[Sostituzione controller](../hardware/controller.md) o la pagina hardware
della scheda interessata.

---

## Verifica delle resistenze di terminazione

RS485 richiede una resistenza da 120Ω a **ciascuna estremità fisica** del
bus (l'estremità controller e l'ultimo dispositivo della catena) — mai nel
mezzo. A bus spento, scollega la coppia A/B dal controller e misura la
resistenza tra A e B con un multimetro:

| Lettura | Significato |
|---|---|
| >1 kΩ (praticamente aperto) | Nessun terminatore presente — terminatore/i mancante/i |
| ~120Ω | Solo un'estremità terminata |
| **~60Ω** | Entrambe le estremità correttamente terminate — questo è l'obiettivo |
| <20Ω | Corto circuito — un guasto di cablaggio, non un problema di terminazione |

Due resistenze da 120Ω in parallelo misurano 60Ω, motivo per cui ~60Ω (non
~120Ω) è il valore da cercare quando entrambe le estremità sono terminate
correttamente.

## Indicazioni sulla lunghezza del cavo

Alla velocità obiettivo del progetto di 38400 baud, lo standard RS485
supporta fino a **500 m** di lunghezza totale del cavo, con le derivazioni
(stub, rami dal percorso principale) mantenute a 1 m o meno. I tratti di
cablaggio a scala domestica dovrebbero risultare ben al di sotto dei 100 m
per bus — comodamente entro quel limite — ma questo non è ancora stato
misurato perché l'installazione fisica non è ancora avvenuta (⚠️ LACUNA
NOTA: le lunghezze reali dei cavi per questa casa non sono ancora registrate
da nessuna parte). Se un tratto dovesse mai superare circa 1000 m, o ci si
avvicina a 32 dispositivi su un bus, un ripetitore diventa da considerare —
nessuno dei due casi si applica alla scala di questa casa.

**La topologia di cablaggio conta quanto la lunghezza**: RS485 deve essere
cablato come un'unica catena a margherita (controller → dispositivo →
dispositivo → … → ultimo dispositivo), mai come una stella con più rami da
un punto centrale. Una topologia a stella causa riflessioni a ogni punto di
diramazione ed è molto difficile da terminare correttamente — se trovi un
cablaggio a stella, questo da solo può spiegare tassi di errore intermittenti
o elevati anche con valori di terminazione corretti.

**Quando rivolgersi a un tecnico:** Se nessuna delle sezioni sopra risolve
il problema, o sospetti che il guasto sia dentro una scheda specifica
piuttosto che nel bus stesso, passa alla pagina corrispondente sotto Guasto
hardware (a partire da
[Quale dispositivo è guasto?](../hardware/index.md)).
