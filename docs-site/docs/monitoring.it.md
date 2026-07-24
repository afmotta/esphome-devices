# Controlli quotidiani

Questa pagina spiega com'è "sano" giorno per giorno l'impiantistica elettronica di questa casa, così puoi individuare un problema in sviluppo prima che diventi un dispositivo morto. Copre anche le basi per leggere i log di un dispositivo quando qualcosa sembra strano.

Se non conosci un termine qui sotto, controlla il [Glossario](reference/glossary.md). Se qualcosa qui ti indirizza verso un problema hardware, la pagina rilevante è [Guasto hardware](hardware/index.md); per qualcosa che si comporta male ma non è chiaramente hardware rotto, vedi [Risoluzione problemi](troubleshooting/canbus.md).

!!! note "Etichette di affidabilità"
    Questa pagina usa le etichette 🟢 VERIFICATO / 🔵 PROGETTATO / ⚠️ LACUNA NOTA, spiegate nella pagina [Home](index.md). Quasi tutto qui sotto è 🔵 — progettato e implementato, ma questo sistema è pre-live, quindi nulla di questo è ancora stato osservato in funzione durante un vero periodo pluriennale di vita in casa.

## Salute del bus CAN

Il bus CAN è la coppia di fili condivisi che interruttori a muro e sensori ambiente usano per comunicare con il resto della casa. Un dispositivo dedicato (il **monitor di salute del bus CAN**) sorveglia ogni dispositivo sul bus e segnala quando uno rimane silenzioso.

🔵 **Come viene definito "perso":** ogni dispositivo sul bus invia un heartbeat (un piccolo segnale "sono ancora qui") ogni 30 secondi. Se il monitor di salute manca **3 heartbeat consecutivi** dallo stesso dispositivo — 90 secondi di silenzio — dichiara quel dispositivo **perso** (lost).

Quando lo stato di un dispositivo cambia, il monitor di salute invia un evento a Home Assistant (il software di domotica). Gli eventi da conoscere:

| Evento | Significato |
|---|---|
| `esphome.canbus_node_lost` | Un dispositivo è appena diventato silenzioso (3 heartbeat mancati). |
| `esphome.canbus_node_recovered` | Un dispositivo precedentemente perso è tornato e invia di nuovo heartbeat. |
| `esphome.canbus_node_error` | Un dispositivo ha segnalato un cambiamento nel proprio stato di errore interno. |
| `esphome.canbus_node_unknown` | Il monitor di salute ha sentito un dispositivo che non riconosce (non presente nel registro della casa). |

Oltre a questi eventi, il monitor di salute pubblica anche alcune entità diagnostiche sempre attive in Home Assistant, aggiornate ogni 5 secondi in modo da sopravvivere anche a una breve disconnessione da Home Assistant stesso:

- **Nodes Online** — quanti dispositivi vengono attualmente ricevuti.
- **Nodes Total** — quanti dispositivi sono attesi, in base al registro della casa.
- **Nodes Missing** — i nomi dei dispositivi attesi ma non attualmente ricevuti.
- **Fallback Events** — un conteggio delle volte in cui il sistema di illuminazione ha dovuto ricorrere alla propria logica locale perché Home Assistant non era pronto a rispondere in tempo. Un conteggio in crescita in una notte altrimenti tranquilla merita un'occhiata.
- **HA Ready** — se Home Assistant è attualmente considerato pronto a ricevere eventi.

**Cosa fare se "Nodes Missing" non è vuoto:** significa che uno specifico dispositivo fisico — un interruttore a muro, un sensore ambiente o simile — ha smesso di comunicare per almeno 90 secondi. Annota quale dispositivo viene indicato, poi vai a [Nodo CAN](hardware/can-node.md) per i passaggi di risoluzione fisica del problema. Non allarmarti per un singolo, breve intoppo — ma un dispositivo che resta nella lista "Missing" per più di qualche minuto richiede un controllo fisico.

## Livelli di ripiego dei sensori climatici

Il controllo climatico di ogni stanza non legge direttamente un singolo sensore — legge un valore "astratto" (combinato, il migliore disponibile) di temperatura e umidità che può ricadere silenziosamente su fino a tre fonti di dati. È deliberato: un sensore CAN guasto non deve poter fermare del tutto il riscaldamento o raffrescamento di una stanza.

I tre livelli, in ordine di priorità:

1. **Primario (etichettato "CAN")** — il sensore CAN proprio della stanza, letto direttamente dal controller climatico.
2. **Secondario (etichettato "HA")** — una lettura di ripiego presa invece da Home Assistant, usata solo quando la lettura CAN non è disponibile.
3. **Emergenza** — nessuna lettura valida da nessuna delle due fonti. Il valore astratto diventa non valido (matematicamente "NaN," not-a-number) nel momento stesso in cui entrambe le fonti falliscono — 🔵 non c'è alcun ritardo integrato in questo componente prima che ciò accada.

    !!! warning "Lacuna nota: il numero '5 minuti'"
        Potresti trovare in altra documentazione del progetto una descrizione del livello Emergenza come innesco di "uno spegnimento di sicurezza dopo 5 minuti." ⚠️ Quel numero specifico non compare nel codice di questo componente di ripiego — restituisce una lettura non valida immediatamente, senza alcun ritardo qui codificato. Se un periodo di grazia di 5 minuti esiste da qualche parte prima che scatti un'azione di sicurezza più ampia, deve vivere in un'altra parte del sistema; considera quel numero non verificato finché non viene confermato. Non dare per scontato che ti protegga.

Ogni stanza espone un'entità diagnostica di testo **"Active Sensor Tier"** (livello sensore attivo) in Home Assistant, che riporta quale livello sta attualmente fornendo i suoi dati, seguendo lo schema `{stanza}_temp_abstracted_sensor_tier` (per esempio, `soggiorno_temp_abstracted_sensor_tier` per il soggiorno). Ne esiste una corrispondente per l'umidità.

**Cosa fare in base a cosa vedi:**

- **Bloccato su "HA" per molto tempo** — il sensore CAN della stanza ha probabilmente smesso di comunicare. La stanza è comunque controllata (usando la lettura di ripiego di Home Assistant), quindi non è un'emergenza, ma va controllato presto. Vedi [Risoluzione problemi climatizzazione](troubleshooting/climate.md) e, se risulta essere il sensore fisico, [Nodo CAN](hardware/can-node.md).
- **Mostra "Emergency"** — nessuna delle due fonti dati funziona per quella stanza. Segnala immediatamente; il controllo climatico di quella stanza non ha dati di temperatura validi su cui agire. Inizia da [Risoluzione problemi climatizzazione](troubleshooting/climate.md).

## Illuminazione: l'hash del manifesto dei binding

La mappatura di "quale pressione di pulsante fa cosa" (quale relè/luce controlla) vive nel registro della casa, in git, e viene compilata nel firmware del controller dell'illuminazione come "manifesto dei binding." Esistono due valori diagnostici correlati per verificare rapidamente che il firmware compilato corrisponda effettivamente a ciò che è attualmente committato:

- **Binding Manifest Hash** — un'impronta breve delle regole di binding incorporate nel firmware in esecuzione.
- **Node Map Version** — un indicatore di versione per la mappa dispositivi/stanze incorporata nel firmware in esecuzione.

🔵 Se uno di questi due non corrisponde a quanto attualmente committato nel registro (`registry/map.json` / `registry/bindings.yaml`), significa: **"la mappatura è stata modificata e committata, ma quel dispositivo non è ancora stato ri-flashato con il nuovo firmware."** Questo è uno stato completamente normale e atteso durante lo sviluppo attivo — non è, di per sé, un guasto. Diventa un problema solo se persiste dopo che credevi fosse già avvenuto un reflash, nel qual caso vale la pena ricontrollare il reflash stesso.

## Cadenza dei controlli di routine

Un ritmo semplice per tenere d'occhio le cose senza ossessionarsi:

- **Settimanale** — dai un'occhiata veloce alle entità diagnostiche di Home Assistant descritte sopra per qualsiasi cosa sembri insolita: "Nodes Missing" diverso da zero, un conteggio "Fallback Events" in crescita, o qualsiasi stanza bloccata fuori dal livello "CAN"/"Primary".
- **Mensile** — controlla che ogni stanza sia tornata sul proprio livello Primario ("CAN"). Una stanza che vive silenziosamente sul suo livello Secondario per un mese è facile da non notare se guardi solo se è "Emergency o no."
- **Trimestrale / a ogni cambio di stagione** — verifica che `hp_mode` (il selettore di modalità pompa di calore/stagione) e le impostazioni di ventilazione (VMC/MEV) corrispondano effettivamente alla stagione in cui ti trovi ora. La fonte di riscaldamento/raffrescamento di questo sistema produce acqua calda o fredda per tutta la casa senza cambio automatico, quindi un'impostazione stagionale rimasta indietro dopo che la stagione è effettivamente cambiata è un modo realistico per ritrovarsi a riscaldare quando si intendeva raffrescare, o viceversa.

## Leggere i log

Per la risoluzione dei problemi in tempo reale, lo strumento principale è trasmettere i log di un dispositivo al tuo terminale:

```
esphome logs <file-punto-d-ingresso.yaml>
```

Per esempio, `esphome logs devices/locals/climate-control.yaml` per il controller climatico, o `esphome logs devices/light-controller.yaml` per il controller dell'illuminazione. (Vedi [Per iniziare](setup.md) se non hai ancora un'installazione ESPHome funzionante per eseguire questo comando.)

### Attivare il log dettagliato Modbus

Modbus è il protocollo cablato che il controller climatico usa per comunicare con le schede relè e uscite analogiche. Se sospetti un problema di comunicazione Modbus (vedi [Risoluzione problemi RS485 / Modbus](troubleshooting/rs485-modbus.md)), puoi ottenere log molto più dettagliati aggiungendo questo alla configurazione del dispositivo prima di compilare e flashare:

```yaml
logger:
  level: DEBUG
  logs:
    modbus_controller: DEBUG
    modbus: DEBUG
```

Questa è un'impostazione diagnostica temporanea — disattivala di nuovo (o non committarla) una volta finito, poiché il log dettagliato è più rumoroso e non pensato per l'uso quotidiano in produzione.

### Leggere le righe di log del failover (ripiego)

🟢 Il testo esatto qui sotto è tratto direttamente dal codice sorgente del componente di ripiego (`climate/packages/components/failover_sensor.yaml`), non indovinato:

- La caduta dal livello Primario al livello Secondario viene registrata a livello **INFO**: `Failover: <livello di partenza> → <livello di arrivo> (primary sensor unavailable)`.
- La caduta al livello Emergenza — da Primario o da Secondario — viene registrata a livello **ERROR**: `Failover: <livello di partenza> → <livello di arrivo> (all sensors unavailable)`.
- Il recupero verso un livello superiore (Secondario → Primario, Emergenza → Primario, o Emergenza → Secondario) viene registrato a livello **INFO**, con la parola `Recovery` al posto di `Failover`.

Quindi, in questo componente specificamente, solo la caduta in Emergenza viene registrata come errore; la caduta da Primario a Secondario è informativa, non un avviso (warning). Se stai cercando nei log con grep, cerca `"failover"` (il tag di log usato) e guarda la parola subito dopo il nome della stanza — `Failover` contro `Recovery` ti dice subito la direzione.

## Dove andare adesso

- Stanza bloccata su un livello di ripiego o in Emergency? [Risoluzione problemi climatizzazione](troubleshooting/climate.md)
- Un dispositivo manca dal bus CAN? [Nodo CAN](hardware/can-node.md)
- Qualcosa è effettivamente morto? [Guasto hardware](hardware/index.md)
- Controllo programmato invece di reagire a un allarme? [Manutenzione ordinaria](maintenance-tasks.md)
