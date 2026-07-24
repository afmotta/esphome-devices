# Manutenzione ordinaria e attività di configurazione

Questa pagina illustra le attività di manutenzione e configurazione di cui avrai più
probabilmente bisogno nel corso della vita della casa: aggiungere una stanza,
registrare un nuovo pulsante a muro, ricablare cosa controlla un pulsante, tarare il
controllo della temperatura, passare il sistema tra stagione di riscaldamento e di
raffrescamento, aggiornare la toolchain e ruotare le credenziali.

Ogni sezione è una procedura numerata autonoma. Se un termine non ti è familiare,
controlla il [Glossario](reference/glossary.md).

!!! note "Come leggere le etichette di affidabilità in questa pagina"
    🟢 **VERIFICATO** — confermato su banco o sul campo.
    🔵 **PROGETTATO** — costruito e pensato per funzionare così, ma non ancora
    provato con un'installazione reale (vero per la maggior parte di questa casa
    pre-live).
    ⚠️ **LACUNA NOTA** — questione realmente irrisolta.

---

## Aggiungere o spostare una stanza di climatizzazione

Usa questa procedura quando una stanza viene aggiunta alla casa, una stanza viene
divisa/unita, oppure una zona deve essere spostata su un relè/canale diverso.

1. **Crea il file di configurazione della stanza.** Aggiungi un nuovo file in
   `climate/rooms/[piano]/[nome_stanza].yaml` (piano è `ground_floor`,
   `first_floor`, o `second_floor`; nome stanza in snake_case, es.
   `camera_est.yaml`).
2. **Includi i pacchetti standard con valori specifici della stanza.** Il file deve
   includere i pacchetti componente per sensore, radiante e fancoil, ciascuno
   parametrizzato con i valori di questa stanza (slug, nome visualizzato, entità
   sensore, numero relè). Copia la struttura di un file di stanza esistente nella
   stessa cartella del piano come punto di partenza — qui la coerenza conta più che
   memorizzare i campi esatti.
3. **Registra la stanza presso il suo piano.** Aggiungi l'include del pacchetto della
   nuova stanza al file aggregatore di quel piano (`[piano]-floor.yaml` nella stessa
   cartella). Un file di stanza non incluso dall'aggregatore del suo piano è invisibile
   al resto del sistema.
4. **Scegli un relè non allocato.** Ogni zona radiante ha bisogno del proprio canale
   relè sulla scheda relè della climatizzazione. Controlla la tabella di assegnazione
   **in vigore** in
   [Tabella hardware e indirizzi](reference/hardware-table.md#tabella-di-assegnazione-rele-bus-climatizzazione-indirizzo-0x2)
   per un canale libero (attualmente `relay_5` o `relay_22`–`relay_32`), e aggiorna
   quella tabella nella stessa modifica così da non farla andare alla deriva rispetto
   alla configurazione reale. I fancoil non hanno un proprio relè — condividono il
   relè della pompa del loro piano e vengono modulati separatamente tramite la scheda
   uscite analogiche.
5. **Testa la configurazione prima di toccare qualsiasi hardware.**
   ```bash
   esphome config devices/locals/climate-control.yaml
   ```
   Questo controlla che lo YAML sia valido e che ogni riferimento si risolva
   correttamente — non richiede un dispositivo fisico collegato. Correggi ogni
   errore segnalato prima di proseguire.
6. **Distribuisci.** Segui il tuo normale percorso di distribuzione (flash locale via
   USB/rete per lo sviluppo, oppure la distribuzione remota basata su GitHub per la
   produzione — vedi `climate/CLAUDE.md` nel progetto se ti serve la meccanica
   completa della distribuzione). Osserva i log della nuova zona per i primi minuti
   dopo la distribuzione, come faresti per qualsiasi modifica che tocca l'attuazione.

!!! warning "Le nuove stanze entrano in una sequenza di messa in servizio pre-live"
    Le zone di climatizzazione in questa casa vengono messe in servizio
    gradualmente e deliberatamente, non tutte insieme — vedi il runbook di
    distribuzione richiamato dalla [Mappa dei documenti](reference/doc-map.md) se
    questa è una prima messa in servizio piuttosto che un'aggiunta ordinaria a una
    casa già in funzione.

---

## Aggiungere o ri-registrare un nodo CAN

Usa questa procedura quando una nuova scheda pulsante a muro o scheda sensore si
unisce al bus CAN, oppure quando una esistente viene ri-registrata (spostata in
un'altra stanza, o sostituita con una scheda di ricambio).

!!! danger "Leggi questo prima di iniziare"
    Il file di registro modificato da questa attività (`registry/nodes.csv`) è
    l'**unica** registrazione di quale scheda fisica corrisponde a quale nodo. Non è
    memorizzato sulla scheda stessa — una scheda diventa qualunque `node_id` con cui
    è stata flashata più di recente. Git è l'unico backup di quell'identità. L'ordine
    dei passaggi seguenti esiste appositamente per garantire che la tua modifica sia
    salvata in modo sicuro **prima** di riflashare qualsiasi cosa, così che un errore
    ti costi un nuovo tentativo, non un'identità persa o duplicata.

1. **Effettua la modifica al registro.** Modifica direttamente `registry/nodes.csv`,
   oppure usa gli strumenti forniti: `canbus/tools/allocate_node.py` per riservare
   un `node_id` nuovo per una scheda del tutto nuova, oppure
   `canbus/tools/commission.py` per assegnare una stanza/posizione a una scheda
   (supporta un flusso "premi un pulsante per identificarti").
2. **Rigenera i file generati.**
   ```bash
   python3 canbus/tools/generate_nodes.py
   ```
   Questo ricostruisce le configurazioni firmware per singolo nodo e gli altri
   artefatti generati collegati a partire dal registro. Non modificare mai a mano i
   file generati direttamente — la rigenerazione successiva sovrascriverebbe
   silenziosamente la tua modifica.
3. **Esegui il controllo proprio del generatore.** Il progetto ha un controllo di
   idempotenza/coerenza che conferma che il registro e i file generati siano
   allineati:
   ```bash
   git diff --exit-code canbus climate registry
   ```
   eseguito subito dopo il passo 2 con un albero di lavoro pulito, questo non
   dovrebbe mostrare differenze inattese. Se lo fa, qualcosa nella modifica al
   registro o nella rigenerazione merita un ulteriore controllo prima di
   proseguire.
4. **Fai il commit del file di registro e dei file generati insieme, nello stesso
   commit.** Non vanno mai committati separatamente — un file generato che non
   corrisponde alla sua fonte nel registro è peggio di nessun file generato, perché
   sembra corretto finché qualcosa non legge effettivamente la parte disallineata.
5. **Fai il push verso il remoto.** Questo è il passaggio che crea effettivamente un
   backup. Finché questo push non è completato, l'unica copia della tua modifica è
   sul disco su cui è stata digitata.
6. **Esegui il gate di push prima di riflashare qualsiasi cosa.**
   ```bash
   python3 canbus/tools/check_registry_pushed.py
   ```
   Deve terminare con codice 0 ("successo"). Verifica che i file di
   registro/generati siano puliti (nulla non committato) e che il tuo ultimo commit
   sia effettivamente raggiungibile dal repository remoto — cioè realmente
   salvato, non solo committato in locale.
7. **Solo ora, riflasha le schede interessate.** Vedi
   [Sostituzione nodo CAN](hardware/can-node.md) per i passaggi di flashing veri e
   propri.

**Perché questo ordine è importante:** se riflashi una scheda *prima* di fare il
push, e qualcosa poi va storto sul tuo computer (guasto del disco, un `git reset`
sbagliato, una sovrascrittura accidentale) prima che tu riesca a fare il push, la
scheda nel muro ora ha un'identità che non esiste da nessun'altra parte — non sul
remoto, non in nessun altro backup. Ricostruire quell'identità in seguito significa
ri-identificare fisicamente ogni scheda interessata a mano. Fare il push prima, e
confermarlo con lo script di gate, significa che il caso peggiore è "rifare una
modifica al registro di cinque minuti", mai "perdere la corrispondenza tra una
scheda e la sua stanza."

---

## Cambiare un binding dell'illuminazione

Un "binding" è la mappatura da un gesto specifico di un pulsante a muro (click,
doppio click, pressione prolungata) a ciò che controlla (quale relè, quale azione).
Usa questa procedura quando stai ricablando cosa fa un pulsante — nessuna modifica
fisica necessaria, solo logica.

1. **Modifica `registry/bindings.yaml`** per cambiare, aggiungere o rimuovere un
   binding.
2. **Rigenera i file generati**, esattamente come nell'attività del nodo CAN sopra:
   ```bash
   python3 canbus/tools/generate_nodes.py
   ```
3. **Esegui lo stesso controllo di coerenza:**
   ```bash
   git diff --exit-code canbus climate registry
   ```
4. **Fai il commit del file di registro e dei file generati insieme**, fai il push,
   ed esegui lo stesso gate di push prima di riflashare:
   ```bash
   python3 canbus/tools/check_registry_pushed.py
   ```
5. **Riflasha il controller dell'illuminazione** (non il nodo pulsante a muro — i
   binding vengono interpretati dal controller dell'illuminazione e da Home
   Assistant, non dalla scheda del pulsante stessa, che riporta solo i gesti grezzi).

Questa è esattamente la stessa disciplina "push prima di riflashare" dell'attività
sul nodo CAN sopra, e per lo stesso motivo: `registry/bindings.yaml` è un dato di
casa non ricostruibile, e git è l'unico suo backup. Vedi quell'attività sopra se
vuoi la spiegazione più completa del perché l'ordine conta.

---

## Tarare i guadagni PID per una zona radiante o fancoil

Il controllo PID (proporzionale-integrale-derivativo) è ciò che porta gradualmente
la temperatura di ogni zona verso il suo obiettivo. Ogni zona ha guadagni separati
per riscaldamento e raffrescamento, e i sistemi radianti e fancoil hanno bisogno di
punti di partenza molto diversi perché si comportano in modo molto diverso — i
pavimenti radianti sono lenti a rispondere, i fancoil sono veloci.

**Dove vivono i valori:** i guadagni PID (`kp`, `ki`, `kd`) vengono impostati nel
punto in cui il pacchetto componente PID viene incluso per quella zona/circuito —
sono parametri passati al momento dell'inclusione, non nascosti nella logica
condivisa del componente. Cerca il blocco `vars:` che accompagna l'inclusione del
pacchetto PID di quella zona.

**Intervalli di partenza:**

| Sistema | Kp | Ki | Kd |
|---|---|---|---|
| Pavimento radiante (sistema lento) | 0,5–1,0 (parti da 0,8) | 0,001–0,01 (parti da 0,005) | 0,01–0,1 (parti da 0,05) |
| Fancoil (sistema veloce) | 1,0–2,0 (parti da 1,2) | 0,005–0,02 (parti da 0,008) | 0,05–0,2 (parti da 0,08) |

La modalità raffrescamento tipicamente richiede guadagni più alti rispetto al
riscaldamento (aumenta tutti e tre di circa il 20–50%) perché il raffrescamento
risponde più velocemente una volta coinvolta la circolazione d'aria a ventilazione
forzata.

**Prova prima l'auto-taratura.** Prima di tarare a mano, usa il componente
`pid_autotune.yaml` — è costruito esattamente per questo e di solito ti avvicinerà
di più, più rapidamente, rispetto a indovinare dagli intervalli sopra. Tara a mano
solo se il risultato non traccia ancora bene.

**Processo di taratura, una volta ottenuto un punto di partenza:**

1. Inizia in modo conservativo — `kp` basso, `ki`/`kd` molto bassi.
2. Aumenta gradualmente osservando eventuali oscillazioni (la temperatura che
   supera il target e oscilla ripetutamente è un segno che sei andato troppo oltre).
3. Tara le modalità riscaldamento e raffrescamento separatamente — sono problemi di
   controllo genuinamente diversi sullo stesso hardware.
4. Dai a una zona radiante tempo reale per mostrare il suo comportamento — poiché è
   un sistema lento, una modifica fatta ora non mostrerà il suo pieno effetto per
   ore, non minuti. Non correggere eccessivamente basandoti sui primi 20 minuti di
   dati.

---

## Cambio di stagione

**Questa è un'attività ricorrente, circa due volte l'anno — non un passaggio di
configurazione una tantum.**

La pompa di calore produce acqua calda oppure acqua refrigerata per tutta la casa
alla volta, e il cambio fisico tra le due avviene alla pompa di calore stessa —
non esiste un relè di commutazione, e nulla in questo sistema software rileva quale
delle due la pompa di calore sta effettivamente producendo. `hp_mode` (e il suo
compagno, `hp_mode_manual_hold`) sono controlli software che l'operatore imposta
**manualmente** per dire al sistema quale delle due sta effettivamente accadendo, in
modo che i controller PID di zona scelgano il comportamento di riscaldamento o
raffrescamento corrispondente.

1. **Sappi quando l'installatore della tua pompa di calore commuta la fonte** —
   questo è un cambio meccanico/idraulico dal loro lato, e in genere avviene vicino
   al cambio di stagione.
2. **Dopo che la fonte è cambiata, aggiorna `hp_mode`** in Home Assistant per
   rispecchiare cosa viene effettivamente prodotto ora (es. da `HEAT` a `COOL`).
   Fallo solo *dopo* che la fonte è effettivamente cambiata — impostare `hp_mode`
   in anticipo rispetto al cambio reale farà sì che le zone provino a condizionare
   usando acqua che non viene ancora effettivamente prodotta.
3. **Lascia `hp_mode_manual_hold` su ON** a meno che la tua installazione non abbia
   già completato la fase di automazione cross-stagione descritta nel runbook di
   distribuzione (vedi [Mappa dei documenti](reference/doc-map.md)) — con
   l'attesa (hold) attiva, `hp_mode` si muove solo quando lo muovi tu, che è
   l'impostazione predefinita più sicura.

!!! warning "Questo continuerà ad accadere"
    Ogni cambio di stagione — da riscaldamento a raffrescamento, e viceversa —
    richiede questo stesso passaggio manuale. Non c'è alcun promemoria integrato nel
    sistema; imposta un promemoria ricorrente legato a quando l'installatore della
    tua pompa di calore commuta effettivamente la fonte, non a una data fissa del
    calendario, poiché la data reale del cambio può spostarsi di anno in anno.

---

## Aggiornamenti di ESPHome/toolchain

Il progetto blocca una versione **esatta** di ESPHome invece di "ultima disponibile"
— attualmente tracciata in `climate/tests/pyproject.toml`. Questo è deliberato: una
nuova versione di ESPHome non testata potrebbe cambiare silenziosamente il
comportamento in un sistema che gestisce attuazione climatica/illuminazione senza
supervisione, quindi gli aggiornamenti sono un evento controllato, non un
`pip install --upgrade` in sottofondo.

1. **Aggiorna il blocco di versione** in `climate/tests/pyproject.toml` alla nuova
   versione target di ESPHome.
2. **Esegui l'intera batteria di verifica** — non saltarla, e non considerare un
   `pip install` riuscito come sufficiente di per sé:
   ```bash
   bash scripts/verification-battery.sh
   ```
   (usa `--native-only` solo se genuinamente non hai ESPHome installato in questo
   ambiente — questo salta i controlli di compilazione/configurazione specifici di
   ESPHome, il che non è il quadro completo per un aggiornamento di versione).
3. **Fidati della nuova versione solo una volta che la batteria passa pulita.** Se
   non passa, non distribuire la nuova versione — o l'aggiornamento ha introdotto
   un'incompatibilità reale che va corretta, oppure il blocco di versione deve
   tornare indietro finché l'incompatibilità non viene risolta a monte.
4. **Fai il commit della modifica al blocco di versione insieme a qualsiasi cosa la
   batteria ti abbia richiesto di correggere** — non separare "aggiorna la
   versione" da "correggi cosa si è rotto a causa di essa" in due commit che
   potrebbero essere distribuiti indipendentemente.

---

## Rotazione di credenziali/segreti

I segreti del sistema vivono in `devices/secrets.yaml` (escluso da git — mai
committato). Il modello in `devices/secrets.yaml.example` documenta quali esistono:

| Segreto | Ambito |
|---|---|
| `wifi_ssid` / `wifi_password` | Credenziali WiFi condivise, usate da ogni dispositivo (anche quelli normalmente su Ethernet — hanno comunque bisogno del WiFi configurato come ripiego). |
| `api_encryption_key` | La chiave di cifratura API Home Assistant del controller dell'illuminazione. |
| `health_monitor_encryption_key` | La chiave di cifratura API propria del monitor di salute del bus CAN — separata da quella del controller dell'illuminazione. |
| `encryption_key` | Condivisa dal controller di climatizzazione e dai dispositivi sensore autonomi (sensore stanza, sensore a muro). |
| `ota_password` | Autentica gli aggiornamenti firmware via rete (OTA), in tutta la casa. |
| `github_username` / `github_pat` | Usati solo dal percorso di distribuzione remota basato su GitHub, per scaricare la configurazione di questo repository durante un aggiornamento OTA tramite l'add-on ESPHome di Home Assistant. |

**Ruota una credenziale alla volta, in questo ordine, in modo da non rimanere
tagliato fuori:**

1. **Genera prima il nuovo valore**, senza toccare ancora nulla di attivo (per le
   chiavi di cifratura: `openssl rand -base64 32`).
2. **Aggiorna `devices/secrets.yaml` in locale** con il nuovo valore solo per la
   credenziale che stai ruotando.
3. **Riflasha il dispositivo interessato mentre la vecchia credenziale funziona
   ancora, oppure tramite una connessione USB diretta.** Per una chiave di
   cifratura API o una password OTA, questo di solito significa flashare via rete
   un'ultima volta usando la credenziale *vecchia* (prima di finalizzare la
   modifica dal lato Home Assistant), oppure collegarsi via USB se non sei sicuro
   che il percorso di rete si autenticherà ancora dopo. In entrambi i casi, il
   punto è: non metterti in una posizione in cui l'unico modo per raggiungere il
   dispositivo richiede una credenziale che hai già cambiato ovunque tranne che sul
   dispositivo stesso.
4. **Verifica la connettività** — conferma che il dispositivo si riconnette a Home
   Assistant / alla rete con la nuova credenziale prima di passare al dispositivo
   successivo.
5. **Solo allora considera completata la rotazione di quella credenziale.** Se stai
   ruotando una credenziale condivisa tra più dispositivi (come `wifi_password` o
   `ota_password`), ripeti i passi 3–4 per ogni dispositivo interessato prima di
   poter dire in sicurezza che la rotazione è finita — un segreto condiviso non è
   "ruotato" finché ogni dispositivo che usava il vecchio valore non è stato
   aggiornato.

!!! danger "Non aggiornare il file dei segreti e fermarti lì"
    Modificare solo `devices/secrets.yaml` non fa nulla a un dispositivo già in
    funzione — ha effetto solo la prossima volta che quello specifico dispositivo
    viene riflashato. Una rotazione a metà (file aggiornato, alcuni dispositivi non
    ancora riflashati) è uno stato da cui uscire rapidamente: significa che
    dispositivi diversi in casa si fidano attualmente di valori diversi per lo
    stesso segreto nominale.

## Correlati

- [Tabella hardware e indirizzi](reference/hardware-table.md) — le tabelle di
  assegnazione relè/canale in vigore richiamate sopra.
- [Glossario](reference/glossary.md) — definizioni per ogni termine non familiare in
  questa pagina.
- [Registro di affidabilità](reference/confidence-ledger.md) — diversi
  comportamenti richiamati sopra (gate di messa in servizio, cascata VMC,
  coordinamento boost) sono ancora 🔵 PROGETTATO, non ancora verificati sul campo.
- [Quale dispositivo è guasto?](hardware/index.md) — se sei qui perché qualcosa si
  è rotto, non perché stai facendo una modifica pianificata.
