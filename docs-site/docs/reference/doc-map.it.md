# Mappa dei documenti

Questo sito non è l'unica documentazione presente nel repository di codice del
progetto. Se tu (o chi ti aiuta) apre mai il repository direttamente invece di
navigare questo sito, è utile sapere quali file sono l'autorità attuale su cosa, e
quali invece sono vecchi e vanno ignorati. Questa pagina è quella mappa.

## I tre livelli della documentazione

Nel repository ci sono tre tipi diversi di documenti, scritti per tre scopi diversi:

1. **Questo sito (`docs-site/`) — la guida pratica, quotidiana.**
   Scritta per chi sta effettivamente facendo il lavoro: un tecnico, un familiare, o
   il proprietario tra qualche anno che cerca di ricordare come funziona qualcosa. Se
   vuoi sapere *come fare* qualcosa — sostituire una scheda, aggiungere una stanza,
   diagnosticare un problema — inizia da qui.

2. **File `CLAUDE.md`** (uno alla radice del repository, e uno dentro ogni cartella
   di sottosistema: `canbus/CLAUDE.md`, `lighting/CLAUDE.md`, `climate/CLAUDE.md`) —
   **riferimenti tecnici/architetturali più approfonditi.**
   Sono stati scritti principalmente per istruire un assistente AI di programmazione
   che lavora sul codice, ma fungono anche da riferimento tecnico più dettagliato nel
   repository: convenzioni di nomenclatura delle entità, mappe complete dei registri
   Modbus, intervalli di taratura del PID, regole di organizzazione dei file. Se
   questo sito fa riferimento a un valore o a una convenzione specifica e vuoi il
   dettaglio completo sottostante, di solito è nel `CLAUDE.md` pertinente che si
   trova. Il file alla radice è una mappa dell'intero repository; il file di ogni
   sottosistema è il vero regolamento di quel sottosistema.

3. **ADR (Architecture Decision Record)**, sotto
   `_bmad-output/planning-artifacts/adrs/` e
   `canbus/_bmad-output/planning-artifacts/adrs/` — **la registrazione del *perché*.**
   Ogni ADR documenta una decisione significativa (es. "su quale hardware controller
   standardizzare"), le alternative considerate, e i compromessi accettati. Leggi un
   ADR quando vuoi capire *perché* qualcosa è stato costruito in un certo modo, non
   solo cosa fa attualmente. Questo sito e i file `CLAUDE.md` descrivono lo stato
   attuale; gli ADR spiegano il ragionamento dietro di esso e non vengono tenuti
   sincronizzati con le modifiche successive come invece accade per gli altri due — una
   decisione può essere modificata da un ADR *successivo* senza che il file originale
   venga riscritto.

Se questi tre sembrano mai in disaccordo, considera questo ordine: questo sito e il
`CLAUDE.md` pertinente descrivono il sistema *attuale*; un ADR spiega *perché* è
arrivato a essere così e potrebbe descrivere una versione precedente o poi modificata
della decisione.

## Documenti storici — ignorali per le procedure attuali

La cartella `docs/` del repository (non la `docs-site/` di questo sito) contiene
alcuni documenti che descrivono una generazione precedente e ritirata dell'hardware
(schede Kincony KC868-A6 / A16, una topologia di controller master/slave, e sensori
ambiente basati su Modbus). Quella generazione è stata completamente sostituita
dall'attuale hardware LilyGO T-Connect Pro e dal design a master unico. Questi file
sono conservati solo come documentazione storica — **non seguirli per il lavoro
attuale**:

| File | Cosa copre | Sostituito da |
|---|---|---|
| `docs/deployment-guide.md` | Distribuzione della vecchia topologia master/slave A6/A16 | `docs/climate-deployment-runbook.md` |
| `docs/sensor-technology-selection.md` | La decisione originale (poi ribaltata) di usare sensori ambiente Modbus | Rilevamento ambiente via bus CAN / Home Assistant, `climate/room_sensors.yaml` |
| `docs/0-10v-adapter-setup-guide.md` | Configurazione di un generico adattatore Modbus 0–10V da AliExpress | La scheda Waveshare Modbus RTU Analog Output 8CH (B) — vedi [Tabella hardware e indirizzi](hardware-table.md) |
| `docs/modbus-register-map.md` | La mappa completa dei registri del vecchio sistema master/slave basato su KC868-A6 | L'attuale impronta Modbus, molto più piccola, descritta in [Tabella hardware e indirizzi](hardware-table.md) |

La maggior parte di questi file riporta un proprio avviso "documento storico" in cima
se li apri direttamente — quell'avviso è accurato e va creduto. Gli altri file sotto
`docs/` (runbook di distribuzione, note sulla compensazione climatica, guide di
cablaggio, mappatura dei sensori finestra, e così via) sono attuali e non fanno parte
di questo elenco.

## Una nota a margine: file scheda orfani

La cartella `boards/` del repository contiene le definizioni hardware per ogni scheda
mai usata dal progetto. Alcune di esse sono residui della generazione hardware
ritirata sopra descritta e non sono più referenziate da nulla: file chiamati
`a6*.yaml`, `a16*.yaml`, `base.yaml` e `wifi.yaml`, più una serie di varianti
Waveshare-S3 inutilizzate (`waveshare-s3.yaml`, `waveshare-s3-ethernet.yaml`,
`waveshare-s3-wifi.yaml` — a differenza di `waveshare-s3-rs485-can.yaml`, che **è**
quella effettivamente usata, dal monitor di salute del bus CAN). Se stai sfogliando
quella cartella e ti chiedi perché esista un file che nulla sembra usare, è per
questo — non è un errore da correggere, solo vecchio codice mai eliminato.

## Correlati

- [Registro di affidabilità](confidence-ledger.md) — tiene traccia di quali
  affermazioni in tutto il sito sono ancora non verificate, separatamente da quali
  *documenti* sono attuali o storici (l'argomento di questa pagina).
- [Tabella hardware e indirizzi](hardware-table.md) — il riferimento hardware attuale
  verso cui rimanda la sezione "documenti storici" di questa pagina.
- [Glossario](glossary.md) — se un termine (italiano o tecnico) in uno di questi
  documenti non ti è familiare.
