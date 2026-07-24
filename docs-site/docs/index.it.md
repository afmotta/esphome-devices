# Home

Se hai scansionato un codice QR attaccato a un componente hardware, quasi certamente cerchi **[Guasto hardware](hardware/index.md)**, non questa pagina. Quella sezione è un albero decisionale: scegli il dispositivo guasto e ti dice cosa fare. Torna qui dopo, se vuoi il quadro d'insieme.

Altrimenti — benvenuto. Questa è la guida di manutenzione e supporto per l'impiantistica elettronica della casa: tre sistemi che condividono cablaggio, hardware e un insieme comune di regole. Leggi questa pagina una volta, in circa cinque minuti, e saprai abbastanza per orientarti nel resto della guida.

## I tre sistemi, in una frase ciascuno

- **`canbus`** — un bus di cablaggio (CAN bus) che permette a interruttori a muro e sensori ambiente di comunicare con il resto della casa attraverso una coppia di fili condivisi, più un dispositivo "monitor di salute" che verifica se qualcosa è rimasto silenzioso.
- **`lighting`** — ascolta le pressioni dei pulsanti che arrivano dal bus CAN e le trasforma in comandi di accensione/spegnimento luci, tramite una scheda relè.
- **`climate`** — gestisce riscaldamento, raffrescamento e ventilazione per 13 stanze su 3 piani: legge temperatura/umidità di ogni stanza (in arrivo dal bus CAN), decide di cosa ha bisogno ciascuna stanza, e comanda pompe, valvole e ventole tramite schede relè e uscite analogiche pilotate via Modbus.

Ogni sistema ha le proprie pagine di guida più dettagliate sotto **Risoluzione problemi** e **Guasto hardware**. Questa pagina è solo la mappa.

!!! note "Questo sistema non è ancora in funzione"
    A oggi, l'impiantistica elettronica di questa casa è **pre-live** (non ancora attiva): la progettazione è completa e il firmware esiste, ma non tutto l'hardware è stato installato fisicamente ed esercitato per anni come avverrebbe in una casa realmente abitata. Questo è rilevante per te come lettore, perché quasi nulla in questa guida è stato dimostrato contro un guasto reale, pluriennale — la maggior parte è "costruito come previsto, mai ancora messo alla prova dal tempo." È proprio per questo che ogni procedura in questa guida è etichettata con un livello di affidabilità. Non dare per scontato che un'etichetta 🔵 significhi "sbagliato" — significa "non ancora dimostrato giusto o sbagliato, quindi verifica prima di fidartene ciecamente."

## Come leggere le etichette di affidabilità

Ogni procedura, tempistica o affermazione tecnica rilevante in questa guida porta una di queste tre etichette:

| Etichetta | Significato |
|---|---|
| 🟢 **VERIFICATO** | Confermato su un banco di prova reale o sul campo. Puoi fidartene. |
| 🔵 **PROGETTATO** | Costruito e pensato per funzionare così, ma non ancora messo alla prova contro un guasto reale o una condizione di campo. Questo è lo stato onesto di quasi tutto in un sistema pre-live — trattalo come "probabilmente corretto, attento a possibili sorprese." |
| ⚠️ **LACUNA NOTA** | Il repository (l'archivio del codice sorgente) da cui è generata questa guida non ha esplicitamente una risposta qui. Lo diciamo apertamente invece di indovinare. Se incontri una di queste lacune, per ora sei da solo — considera di annotare ciò che scopri, così la lacuna potrà essere colmata. |

Vedrai queste etichette in tutto il sito, compreso nel [Registro di affidabilità](reference/confidence-ledger.md), che elenca tutte le lacune note in un unico posto.

## La regola più importante

🟢 **Tutte le mappature pulsante-stanza, sensore-stanza e luce-interruttore di questa casa vivono in un unico posto: una cartella chiamata `registry/` dentro il repository git del progetto (il suo sistema di controllo versione del codice sorgente). Git è l'**unico** backup di quei dati.**

In concreto, prima di ri-flashare (riprogrammare) qualsiasi dispositivo il cui firmware è costruito a partire da quei dati di registro — il controller dell'illuminazione, il monitor di salute del bus CAN, o il controller climatico — chi si occupa dell'aspetto tecnico deve eseguire:

```
python3 canbus/tools/check_registry_pushed.py
```

Questo è un controllo meccanico, non un suggerimento: guarda il repository git e si rifiuta di dare l'ok a meno che ogni modifica non sia sia stata **committata** (registrata) sia **pushata** (inviata) a un server remoto (come GitHub), il che è ciò che la rende un vero backup e non un file che vive solo sul disco di un portatile. Il comando termina con codice `0` se è sicuro procedere, `1` se il controllo ha fallito, o `2` se qualcosa è andato storto nel leggere git stesso.

Perché questo conta così tanto: la documentazione stessa di questo progetto descrive il ri-flash di un dispositivo con modifiche al registro non pushate come **"una casa senza backup."** Se la memoria di quel dispositivo venisse mai cancellata — un flash fallito, una scheda morta, un errore — e l'unica registrazione di quale pulsante controlla quale luce, o quale sensore appartiene a quale stanza, esistesse solo sul disco di un portatile, quell'informazione andrebbe persa. Ogni mappatura di interruttore a muro e sensore ambiente dovrebbe essere riscoperta a mano, stanza per stanza. Eseguire il comando sopra richiede pochi secondi e previene tutto questo.

Se sei un tecnico che di solito non usa git: questa è l'unica cosa su cui insistere prima di lasciare che chiunque ri-flashi un dispositivo dopo una modifica alla mappatura. In caso di dubbio, chiedi a chi gestisce questo repository di confermare che il controllo sia passato prima di procedere.

## Lo scaffale fisico dei ricambi

Questa casa riutilizza deliberatamente lo stesso ristretto insieme di modelli hardware sia per il sistema climatico sia per quello di illuminazione, specificamente affinché la maggior parte dei guasti diventi "sostituisci la scheda con un ricambio identico e ri-flashala," non "riprogetta qualcosa." Tenere uno scaffale rifornito con questi elementi copre quasi tutta la casa.

| Dispositivo | Modello | Usato per | Storia del ricambio |
|---|---|---|---|
| Controller | LilyGO T-Connect Pro (ESP32-S3, con Ethernet, RS485 e CAN bus integrati) | **Entrambi** il controller climatico (`devices/climate-control.yaml`) e il controller dell'illuminazione (`devices/light-controller.yaml`) | 🔵 Una scheda di ricambio copre entrambi i ruoli — è il firmware che ci carichi a decidere quale compito svolge. |
| Scheda relè | Waveshare Modbus RTU Relay 32CH (indirizzo `0x2`) | Comando di pompe/valvole di zona (climatizzazione) e circuiti luce (illuminazione) | 🔵 L'indirizzo è deliberatamente specchiato su entrambi i cablaggi RS485 dei due sistemi, quindi una scheda relè di ricambio funziona in entrambi i sistemi, senza modifiche. |
| Scheda uscite analogiche | Waveshare Modbus RTU Analog Output 8CH (B) (indirizzo `0x1`) | Velocità ventola fancoil e modulazione valvola di miscelazione (uscite 0–10V) | 🔵 Solo sistema climatico — nessuna controparte nell'illuminazione. |
| Monitor di salute bus CAN | Waveshare ESP32-S3-RS485-CAN (solo WiFi) | Sorveglia il bus CAN e segnala quali dispositivi sono rimasti silenziosi | ⚠️ **Lacuna nota**: questo è attualmente l'unico dispositivo in casa senza un piano predefinito di "ricambio identico sullo scaffale" — vedi il [Registro di affidabilità](reference/confidence-ledger.md). La sua logica può, se necessario, essere spostata su una T-Connect Pro di ricambio, poiché le due schede condividono un cablaggio compatibile. |
| Bridge di segmento CAN | LilyGO T-2CAN | Unisce sezioni separate del cablaggio del bus CAN | 🔵 Deliberatamente privo di WiFi e di capacità di aggiornamento over-the-air — può essere riprogrammato solo via cavo USB, per progettazione, per motivi di affidabilità. |
| Sensore ambiente (avanzato) | S1-Pro Multi-Sense | Temperatura/umidità/qualità dell'aria ambiente più rilevamento presenza basato su radar | 🔵 |
| Sensore ambiente (semplice) | Scheda sensore da parete | Solo temperatura/umidità/qualità dell'aria ambiente, senza radar | 🔵 |

Il dettaglio completo — indirizzi esatti, quale file punto d'ingresso corrisponde a quale dispositivo, e codici articolo — vive nella pagina di riferimento [Tabella hardware e indirizzi](reference/hardware-table.md). Se hai davanti un dispositivo effettivamente guasto, vai a [Guasto hardware](hardware/index.md) invece di cercare di capirlo da questa tabella.

## Dove andare adesso

- **Prima volta che configuri un computer per lavorare su questo repository?** Inizia da [Per iniziare](setup.md).
- **Vuoi sapere com'è "sano" il sistema giorno per giorno, o come leggere i log?** Vai a [Controlli quotidiani](monitoring.md).
- **Qualcosa si comporta male ma niente sembra fisicamente rotto?** Controlla prima [Risoluzione problemi](troubleshooting/canbus.md).
- **Un dispositivo fisico è effettivamente guasto?** Vai direttamente a [Guasto hardware](hardware/index.md).
- **Stai facendo un controllo programmato, non reagendo a un problema?** Vedi [Manutenzione ordinaria](maintenance-tasks.md).
- **Ti serve un termine definito, o vuoi sapere quale documento è autorevole per un dato fatto?** Vedi il [Glossario](reference/glossary.md) e la [Mappa dei documenti](reference/doc-map.md).
