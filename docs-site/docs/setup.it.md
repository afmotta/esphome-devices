# Per iniziare

Questa pagina accompagna un computer nuovo, senza nulla installato, fino a poter compilare ("compile") e installare ("flash") il firmware di questa casa, e leggerne i log. Raccoglie in un unico posto passaggi che altrimenti sono sparsi in diversi file del repository del progetto (la cartella dove è conservato il codice sorgente, gestita da uno strumento chiamato git).

Se non sai ancora cosa significhi "repository," "compilare" o "flashare," continua a leggere — ogni termine è spiegato la prima volta che viene usato. Se hai già un ambiente funzionante e vuoi solo i comandi quotidiani, salta al [Passo 5](#passo-5-comandi-quotidiani).

!!! note "A chi è rivolta questa pagina"
    Questa pagina presuppone che tu sia a tuo agio a digitare comandi in un terminale (una finestra di comandi testuale), ma niente di più avanzato. Se sei davanti a hardware guasto in questo momento e non ti serve configurare un computer di sviluppo, vai invece a [Guasto hardware](hardware/index.md).

## Passo 1: installa i prerequisiti

Ti servono quattro cose sul tuo computer prima di iniziare:

1. **git** — lo strumento che scarica e tiene traccia delle modifiche al codice del progetto. Su macOS, installare git avviene automaticamente la prima volta che esegui `git` in un terminale (te lo chiederà). Su Linux, installalo tramite il gestore pacchetti (es. `sudo apt install git`).
2. **Python, versione 3.12 o successiva** — il linguaggio in cui sono scritti alcuni degli strumenti di supporto del progetto. Controlla la tua versione con `python3 --version`.
3. **Una toolchain di compilazione C++ (in particolare, `g++`)** — necessaria per eseguire i "test nativi" di questo progetto, piccoli programmi autonomi che verificano la logica principale senza bisogno di alcun strumento ESPHome installato. Su macOS si ottiene installando gli Xcode Command Line Tools di Apple (`xcode-select --install`); su Linux, installa `build-essential` (Debian/Ubuntu) o l'equivalente della tua distribuzione.
4. **Un editor di testo** — per modificare i file di configurazione, che sono testo semplice (formato YAML). Va bene qualsiasi editor; VS Code è una scelta comune per questo tipo di progetto.

## Passo 2: clona il repository e configura il tuo file dei segreti

"Clonare" significa scaricare una copia di lavoro completa del progetto, inclusa la sua cronologia.

1. Clona il repository:

    ```
    git clone git@github.com:afmotta/esphome-devices.git
    ```

    (Se non hai configurato una chiave SSH con GitHub, usa invece la forma HTTPS: `git clone https://github.com/afmotta/esphome-devices.git`.)

2. Copia il modello dei segreti per creare il tuo file dei segreti reale:

    ```
    cp devices/secrets.yaml.example devices/secrets.yaml
    ```

    `devices/secrets.yaml` è **deliberatamente escluso da git** ("gitignored") — contiene password e chiavi reali, e non deve mai essere committato o pushato. Solo il modello `.example`, con valori segnaposto, è tracciato.

3. Apri `devices/secrets.yaml` nel tuo editor di testo e compila ogni valore. Ecco cosa significa ciascuno:

    | Chiave | Cos'è | Come ottenere un valore |
    |---|---|---|
    | `wifi_ssid` / `wifi_password` | Il nome e la password della rete WiFi di casa. Ogni dispositivo ne ha bisogno, anche quelli che usano principalmente una connessione Ethernet cablata — viene usato come ripiego. | Le tue credenziali WiFi reali. |
    | `api_encryption_key` | Una chiave segreta che cifra la comunicazione tra il **controller dell'illuminazione** e Home Assistant (il software di domotica con cui questo progetto si integra). Non è una password che scegli tu — è una chiave casuale. | Generane una con `openssl rand -base64 32` in un terminale. |
    | `health_monitor_encryption_key` | Lo stesso tipo di chiave, ma specifica per il dispositivo **monitor di salute del bus CAN**. Deve essere un valore casuale *diverso* da `api_encryption_key` — ogni dispositivo ha la propria chiave. | Di nuovo `openssl rand -base64 32` — eseguilo una seconda volta per un nuovo valore. |
    | `encryption_key` | Ancora lo stesso tipo di chiave, ma condivisa dal **controller climatico** e dai dispositivi sensore ambiente/parete autonomi. | `openssl rand -base64 32` — un terzo valore distinto. |
    | `ota_password` | Una password che protegge gli aggiornamenti firmware "OTA" (over-the-air, cioè via rete) dall'essere inviati a un dispositivo da chiunque non sia autorizzato. | `openssl rand -base64 32`, oppure qualsiasi password robusta. |
    | `github_username` / `github_pat` | Necessari solo se userai il metodo di distribuzione in produzione basato su GitHub (`devices/remotes/`, spiegato al Passo 5) — un nome utente GitHub e un "personal access token" (una specie di password limitata a ciò che serve) che permette a un dispositivo di scaricare la propria configurazione direttamente da GitHub. | Crea un token nelle impostazioni del tuo account GitHub, sotto Developer Settings → Personal Access Tokens. |

    Ogni dispositivo ESPHome dovrebbe avere una propria chiave di cifratura distinta — non riusare mai la stessa chiave tra più dispositivi. Ogni comando `openssl rand -base64 32` stampa un nuovo valore casuale di 32 byte codificato come testo; eseguilo una volta per ogni chiave da compilare.

## Passo 3: installa ESPHome, alla versione esatta

ESPHome è il framework che trasforma i file di configurazione YAML del progetto in firmware reale per i microcontrollori ESP32 usati in tutta la casa. Installa la versione esatta su cui questo repository è costruito e testato:

```
pip install "esphome==2026.7.0"
```

Alcune note sul perché questa versione specifica è importante:

- Il progetto fissa deliberatamente `esphome==2026.7.0` in `climate/tests/pyproject.toml`. 🟢 Questa è l'unica versione verificata end-to-end per i percorsi di compilazione dei controller principali (il controller climatico e il firmware dei nodi del bus CAN).
- Le singole definizioni hardware ("board") nel repository dichiarano una propria versione minima di ESPHome, che varia da 2026.3.0 fino a 2026.7.0 a seconda della board. 🟢 Ma 2026.7.0 è la versione da installare effettivamente — soddisfa il minimo di ogni board ed è quella su cui girano i test stessi del progetto.

!!! warning "Attenzione su Mac Intel"
    🟢 Se sei su un **Mac basato su Intel (x86_64)** in particolare, installare `esphome==2026.7.0` può entrare in conflitto con `esptool` (uno strumento da cui ESPHome dipende per il flashing): ESPHome 2026.7.0 fissa una libreria di sicurezza (`cryptography==49.0.0`) che `esptool 5.3.1` rifiuta su quella piattaforma. Questo è un conflitto reale e confermato — non ipotetico — ma specifico di macOS Intel. Se sei su un **Mac Apple Silicon (serie M/arm64)** o su **Linux**, questo non ti riguarda; sono i due ambienti su cui questo progetto effettivamente sviluppa e testa. Se sei bloccato su un Mac Intel, chiedi a chi mantiene questo repository la soluzione attuale prima di perderci tempo da solo.

## Passo 4: verifica rapida dell'ambiente

Prima di toccare hardware reale, conferma che la tua configurazione funzioni davvero usando lo script di verifica integrato del progetto.

1. Prima, esegui il sottoinsieme "solo nativo." Funziona anche *prima* che ESPHome sia installato, perché esercita solo i programmi di test in Python e C++ puro (non serve alcuno strumento di build ESPHome):

    ```
    bash scripts/verification-battery.sh --native-only
    ```

2. Una volta installato ESPHome (Passo 3), esegui la batteria completa, che convalida e compila anche configurazioni di dispositivi reali:

    ```
    bash scripts/verification-battery.sh
    ```

Entrambi i comandi stampano una riga di riepilogo PASS/FAIL per ogni controllo, e in caso di fallimento mostrano le ultime 50 righe del log rilevante. 🟢 Se uno dei due comandi fallisce su un checkout appena clonato senza modifiche locali, il problema è nella tua configurazione dell'ambiente, non nel progetto — ricontrolla i Passi 1–3 prima di andare oltre.

!!! note
    La batteria completa include un controllo che rigenera alcuni file auto-generati e si aspetta una corrispondenza byte per byte con quanto già committato. Richiede che la tua copia di lavoro non abbia modifiche non committate sotto `canbus/`, `climate/` o `registry/` prima di eseguirla — committa o metti in stash prima, se hai fatto modifiche.

## Passo 5: comandi quotidiani

Una volta configurato l'ambiente, ecco i comandi che userai di routine. Vanno tutti eseguiti dalla radice del repository.

| Comando | Cosa fa |
|---|---|
| `esphome config devices/locals/climate-control.yaml` | **Solo convalida** — controlla la configurazione per errori senza costruire il firmware. Veloce; usalo per primo dopo aver cambiato qualcosa. |
| `esphome compile devices/locals/climate-control.yaml` | **Costruisce** il firmware in un file binario, senza installarlo da nessuna parte. Utile per confermare che qualcosa compili prima di flasharlo. |
| `esphome run devices/locals/climate-control.yaml --device /dev/ttyUSB0` | Costruisce **e installa** ("flasha") il firmware su un dispositivo collegato via cavo USB. Il percorso `--device` indica quale porta USB usare (varia da computer a computer e da cavo a cavo — `/dev/ttyUSB0` è un esempio tipico su Linux; su macOS assomiglia più a `/dev/cu.usbserial-XXXX`). **Questo passaggio via USB serve solo una volta per ogni dispositivo fisico** — dopo il primo flash, gli aggiornamenti successivi possono avvenire via rete ("OTA," over-the-air). |
| `esphome logs devices/locals/climate-control.yaml` | Si connette a un dispositivo in funzione e trasmette in tempo reale il suo log al tuo terminale — il modo principale per osservare cosa sta facendo un dispositivo in tempo reale. |

### `devices/locals/` contro `devices/remotes/`

Noterai due cartelle diverse con file dal nome simile:

- **`devices/locals/*.yaml`** — configurazioni che costruisci tu stesso, sul tuo computer, con i comandi sopra. È ciò che usi per sviluppo, test, e qualsiasi flash via cavo USB.
- **`devices/remotes/*.yaml`** — configurazioni di produzione che non contengono direttamente la definizione del firmware; invece dicono a ESPHome di scaricarla direttamente da GitHub (`github://...`). Vengono distribuite in modo diverso: tramite l'add-on ESPHome di Home Assistant, cliccando **"Install"** sulla scheda del dispositivo. Non serve un computer né un terminale per questa via, una volta che un dispositivo è già stato configurato in questo modo — il che la rende la scelta giusta per gli aggiornamenti di routine di un dispositivo già installato in una parete.

!!! note "Non tutti i dispositivi hanno ancora entrambe le varianti"
    A oggi, **solo il controller climatico** ha sia un `devices/locals/climate-control.yaml` sia un `devices/remotes/climate-control.yaml`. Il controller dell'illuminazione no — non esiste un `devices/locals/light-controller.yaml` né un `devices/remotes/light-controller.yaml`. Se stai lavorando sul controller dell'illuminazione, compila direttamente il suo file punto d'ingresso: `devices/light-controller.yaml`. Non dare per scontato che ogni dispositivo segua lo schema a due varianti del controller climatico; controlla prima cosa esiste davvero nella cartella `devices/`.

## Un'insidia da conoscere

!!! warning "Ri-configurare un dispositivo dopo un cambio di schema di autenticazione"
    🟢 La versione 2026.1.0 di ESPHome ha rimosso un vecchio modo con cui i dispositivi si autenticano a Home Assistant (`api: password:`) a favore di uno schema più nuovo e cifrato (`api: encryption:`, quello usato da questo progetto — vedi `api_encryption_key` ecc. al Passo 2). Se stai ri-flashando un dispositivo originariamente configurato in Home Assistant con il vecchio schema a password, Home Assistant **non accetterà** la nuova chiave di cifratura su quella vecchia registrazione. Devi prima **eliminare il dispositivo da Home Assistant** (Impostazioni → Dispositivi e Servizi → ESPHome) e poi **riaggiungerlo** usando la nuova chiave di cifratura. Limitarsi a ri-flashare il dispositivo lasciando la vecchia voce Home Assistant al suo posto non funzionerà.

## Dove andare adesso

- Pronto a verificare se il sistema si comporta normalmente giorno per giorno? Vedi [Controlli quotidiani](monitoring.md).
- Stai configurando un dispositivo fisico nuovo per la prima volta, o sostituendone uno guasto? Vedi [Guasto hardware](hardware/index.md) per la procedura specifica del dispositivo.
- Ti serve cercare un termine sconosciuto? Vedi il [Glossario](reference/glossary.md).
