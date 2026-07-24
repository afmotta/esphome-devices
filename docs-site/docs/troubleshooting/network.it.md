# Rete / Home Assistant — Diagnosi e soluzione: problemi comuni

Questa pagina copre i problemi generali di connettività che non sono
specifici di un singolo sottosistema: un controller che risulta offline in
Home Assistant, aggiornamenti firmware via rete (OTA) che falliscono, e
Home Assistant che non riesce a rilevare o accettare un dispositivo. Se il
dispositivo in questione funziona bene e solo un sottosistema specifico
(climatizzazione, illuminazione, bus CAN) si comporta male, inizia invece
dalla pagina di quel sottosistema — questa pagina serve per quando il
dispositivo stesso non è raggiungibile affatto.

!!! note "Come leggere le etichette di affidabilità in questa pagina"
    Questo impianto non è ancora stato installato fisicamente. 🟢 VERIFICATO
    = confermato su banco di prova o sul campo. 🔵 PROGETTATO = costruito e
    pensato per funzionare così, ma non ancora provato contro un guasto
    reale. ⚠️ LACUNA NOTA = genuinamente irrisolto.

---

## Un dispositivo risulta offline / non disponibile in Home Assistant

**Sintomo:** Un controller o dispositivo che normalmente comunica con Home
Assistant risulta non disponibile, in grigio, oppure semplicemente smette
di aggiornarsi.

**Cause probabili:**

- Il collegamento di rete del dispositivo è caduto (cavo Ethernet
  scollegato, porta dello switch morta, WiFi fuori portata o credenziali
  errate).
- L'indirizzo IP del dispositivo è cambiato (se usa DHCP invece di un
  indirizzo fisso, un riavvio del router o la scadenza del lease può
  assegnargli un nuovo indirizzo, rompendo tutto ciò che puntava al vecchio).
- Il dispositivo si è bloccato o è intrappolato in un ciclo di riavvio.
- Home Assistant stesso ha un problema, non il dispositivo.

**Passi diagnostici:**

1. Verifica prima che Home Assistant stesso sia in buono stato — se *tutti*
   i dispositivi risultano offline insieme, il problema è Home Assistant o
   la rete nel suo complesso, non un singolo controller.
2. Controlla il collegamento di rete fisico sul dispositivo specifico: cavo
   Ethernet ben inserito, spia di link attiva sullo switch/sulla porta;
   oppure, per dispositivi WiFi, intensità del segnale e credenziali.
3. Se il dispositivo usa normalmente un indirizzo IP fisso/statico, conferma
   che risponda ancora a quell'indirizzo. Se usa DHCP, controlla l'elenco
   client del router per l'indirizzo attualmente assegnato — potrebbe essere
   cambiato.
4. Se la rete sembra a posto ma il dispositivo continua a non rispondere,
   potrebbe essersi bloccato; un ciclo di spegnimento/accensione è un passo
   successivo ragionevole.

**Soluzione:**

- Ripara o reinserisci la connessione di rete fisica.
- Se l'indirizzo IP è cambiato, aggiorna qualsiasi riferimento al vecchio
  indirizzo (oppure assegna al dispositivo un IP fisso/statico così non
  accade più — vedi [Per iniziare](../setup.md) per indicazioni sulla
  configurazione di rete iniziale).
- Spegni e riaccendi il dispositivo come ultima risorsa se sembra bloccato
  e una semplice correzione di rete non lo riporta online.

**Quando rivolgersi a un tecnico:** Se il dispositivo non torna online dopo
un ciclo di spegnimento/accensione e con una rete confermata funzionante, e
puoi accedervi fisicamente, controlla se risponde su una connessione
USB/seriale diretta — se non risponde nemmeno lì, potrebbe essere un guasto
hardware; vedi la pagina corrispondente sotto Guasto hardware (inizia da
[Quale dispositivo è guasto?](../hardware/index.md)).

---

## Un aggiornamento firmware via rete (OTA) fallisce

**Sintomo:** L'invio di un aggiornamento firmware a un dispositivo
dall'integrazione ESPHome di Home Assistant fallisce a metà, va in timeout,
oppure il dispositivo non torna online dopo.

**Cause probabili:**

- La password OTA configurata nello strumento di aggiornamento non
  corrisponde alla password incorporata nel firmware attuale del
  dispositivo.
- Il dispositivo non è raggiungibile in rete nel momento dell'aggiornamento
  (vedi la sezione precedente).
- Il dispositivo non ha abbastanza spazio di memoria flash libero per la
  nuova immagine firmware.

**Passi diagnostici:**

1. Conferma che la password OTA utilizzata corrisponda a quella nei
   segreti/configurazione del dispositivo — un disallineamento qui è una
   delle cause più comuni di aggiornamento fallito e produce un fallimento
   simile a un errore di autenticazione piuttosto che un errore pulito.
2. Conferma che il dispositivo sia raggiungibile in rete in questo momento
   (vedi la sezione precedente) — un aggiornamento non può completarsi
   contro un dispositivo già offline.
3. Controlla lo spazio flash disponibile se il log dell'aggiornamento
   menziona errori di memoria o di partizione; questo è più probabile su
   schede più vecchie/piccole che sull'hardware controller attuale.

**Soluzione:**

- Correggi la password OTA in modo che entrambi i lati siano d'accordo.
- Risolvi prima il problema di raggiungibilità di rete sottostante, poi
  riprova.
- Se il problema è lo spazio flash, in genere significa che il firmware è
  cresciuto oltre quanto la scheda supporta — serve un'indagine sulla
  dimensione del firmware, non solo un nuovo tentativo.

**Quando rivolgersi a un tecnico:** Se un dispositivo non torna online dopo
un aggiornamento OTA fallito e la normale diagnosi di rete non lo ripristina,
l'accesso fisico con un cavo USB per riprogrammarlo direttamente è la via di
riserva — questa è una situazione di recupero firmware, non di cablaggio.

---

## Home Assistant non riesce a rilevare o aggiungere un dispositivo

**Sintomo:** Un dispositivo che dovrebbe essere visibile all'integrazione
ESPHome di Home Assistant non compare per essere aggiunto, oppure un
dispositivo esistente che funzionava prima ora rifiuta di riconnettersi
dopo una sorta di aggiornamento.

**Cause probabili — la più comune è un cambiamento noto dello schema di
cifratura:**

La versione 2026.1.0 di ESPHome ha cambiato il modo in cui i dispositivi si
autenticano verso Home Assistant, passando da un semplice schema `api:
password:` a uno schema più robusto `api: encryption:` (una chiave di
cifratura invece di una semplice password). Un dispositivo che era stato
originariamente aggiunto a Home Assistant con il **vecchio** schema basato su
password, ma che da allora è stato riprogrammato con firmware che usa il
**nuovo** schema basato su chiave di cifratura, non continuerà a funzionare
silenziosamente — bisogna informare Home Assistant del cambiamento. Il
firmware di questo progetto punta a ESPHome corrente, quindi questo riguarda
in particolare dispositivi aggiunti a Home Assistant molto tempo fa e mai
più riaggiunti da allora.

**Passi diagnostici:**

1. Controlla se il dispositivo in questione è stato aggiunto a Home
   Assistant molto tempo fa (prima che il firmware del dispositivo stesso
   passasse all'autenticazione basata su cifratura) — questo disallineamento
   temporale è la firma tipica di questo specifico problema.
2. Conferma prima la raggiungibilità di rete di base (vedi la prima sezione
   di questa pagina) — il rilevamento non può funzionare affatto se il
   dispositivo non è raggiungibile.

**Soluzione:** Rimuovi completamente la vecchia voce del dispositivo da
Home Assistant e riaggiungilo da zero, così Home Assistant recupera la
chiave di cifratura attuale invece di provare a riutilizzare le vecchie
credenziali basate su password. Vedi [Per iniziare](../setup.md) per la
procedura completa di aggiunta di un dispositivo a Home Assistant, incluso
da dove proviene la chiave di cifratura.

**Quando rivolgersi a un tecnico:** Se una rimozione e riaggiunta pulita non
funziona e la raggiungibilità di rete di base è confermata, ricontrolla che
la chiave di cifratura configurata sul dispositivo corrisponda esattamente a
quella che stai inserendo in Home Assistant — un errore di copia/incolla
qui appare identico a un fallimento di rilevamento.
