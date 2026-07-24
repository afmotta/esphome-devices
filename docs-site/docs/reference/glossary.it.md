# Glossario (termini italiani + acronimi)

L'automazione di questa casa è stata realizzata per una residenza italiana, quindi
molti nomi di entità, nomi di stanze e nomi di file usano parole italiane. La
documentazione e i commenti nel codice sono in inglese, ma incontrerai continuamente
termini italiani nel sistema vero e proprio. Questa pagina raccoglie sia quel
vocabolario sia gli acronimi/il gergo tecnico usati in tutto il sito, ciascuno
definito in una frase semplice.

## Termini italiani

Queste parole compaiono nei nomi delle stanze, negli ID delle entità (i nomi di
sensori/interruttori in Home Assistant) e nei nomi dei file in tutto il repository.

| Italiano | Inglese | Contesto |
|---|---|---|
| soggiorno | living room | Il nome di zona più comune della casa. |
| cucina | kitchen | Un tipo di stanza. |
| bagno | bathroom | Ce ne sono diversi; si distinguono con una parola aggiuntiva (es. "Bagno Grande", "Bagno Padronale"). |
| camera | bedroom | Di solito abbinata a una direzione o a un descrittore (es. "Camera Nord"). |
| anticamera | entry hall / foyer | Una zona del piano terra. |
| lavanderia | laundry room | Un locale di servizio del primo piano. |
| sottotetto | attic | L'unica zona del secondo piano. |
| locale tecnico | technical room | Il locale che ospita l'impianto di riscaldamento/raffrescamento. |
| piano terra | ground floor | Livello 0 dell'edificio. |
| primo piano | first floor | Livello 1 dell'edificio. |
| secondo piano | second floor | Livello 2 dell'edificio. |
| gruppo miscelazione | mixing valve group | Un nome usato dall'hardware controller di prima generazione, ormai ritirato; potresti trovarlo in vecchia documentazione, ma non fa parte del sistema attuale. |
| distribuzione | distribution | Un'altra convenzione di nomenclatura della prima generazione ritirata (per le vecchie schede slave); anch'essa non fa parte del sistema attuale. |
| radiante | radiant | Si riferisce al riscaldamento/raffrescamento radiante a pavimento (o a soffitto) — il sistema ad acqua incorporato nel pavimento o nel soffitto, in contrapposizione a un'unità a ventilazione forzata. |

## Acronimi e gergo tecnico

| Termine | Definizione in parole semplici |
|---|---|
| **ADR** (Architecture Decision Record) | Un documento scritto che registra una decisione di progettazione significativa e il ragionamento dietro di essa — usato qui per documentare cose come "quale hardware controller usare", così che il ragionamento non vada perso in seguito. |
| **PID** (Proporzionale-Integrale-Derivativo) | Un algoritmo di controllo che porta gradualmente una temperatura verso il suo obiettivo, regolando costantemente l'uscita in base a quanto è distante dal target, da quanto tempo lo è, e a quanto velocemente sta cambiando — il metodo standard con cui questo sistema gestisce sia il riscaldamento/raffrescamento radiante sia quello a fancoil. |
| **VMC** (Ventilazione Meccanica Controllata) | Il sistema di ventilazione della casa — estrae l'aria viziata/umida e aiuta a controllare la qualità dell'aria interna e l'umidità; nella documentazione tecnica in inglese viene chiamata "MEV" (Mechanical Extract Ventilation). |
| **RS485** | Un tipo di collegamento elettrico via cavo (due fili, "A" e "B") usato per collegare il controller alle schede relè, alle schede di uscita analogica e all'unità di ventilazione. È il cavo fisico; il Modbus (sotto) è il linguaggio parlato su quel cavo. |
| **CAN** (Controller Area Network) / **bus CAN** | Una rete via cavo diversa, separata dall'RS485, usata per collegare i pulsanti a muro e le schede sensore ambiente ai controller. Nato per il settore automobilistico, si adatta bene a una casa perché un guasto o un'interruzione in una sezione non porta necessariamente giù l'intera rete. |
| **HA** (Home Assistant) | Il software open-source di domotica con cui questo sistema si integra per monitoraggio, dashboard e override manuali. Il controllo climatico e dell'illuminazione della casa continua a funzionare anche se HA è offline — HA aggiunge visibilità e comodità sopra a quello. |
| **OTA** (Over-The-Air, aggiornamento via rete) | Aggiornare il firmware di un dispositivo tramite la rete (WiFi/Ethernet) invece di collegare un cavo USB. La maggior parte dei controller della casa lo supporta; le piccole schede dei pulsanti a muro sul bus CAN deliberatamente no (vedi la voce sui nodi qui sotto). |
| **`node_id`** | Il numero univoco che identifica una scheda del bus CAN (un pulsante a muro o una scheda sensore) nel file di riferimento `registry/nodes.csv`. Una scheda fisica non ha un'identità propria — diventa qualunque `node_id` con cui è stata flashata più di recente. |
| **Modbus** (in particolare Modbus RTU) | Un formato di messaggistica parlato su un cavo RS485 — definisce come il controller chiede a una scheda relè "accendi il canale 5" o chiede all'unità di ventilazione "qual è la tua velocità attuale del ventilatore", e come questi dispositivi rispondono. |
| **Coil** / **registro** (termini Modbus) | Due tipi di "spazi di memoria" esposti da un dispositivo Modbus. Un **coil** è un singolo valore on/off (usato per i canali relè — acceso o spento). Un **registro** contiene un valore numerico (usato, per esempio, per un livello di uscita analogica 0–10V o una lettura di temperatura). |
| **Livello di failover** (failover tier) | Questo sistema legge alcuni valori dei sensori da più di una fonte, in ordine di priorità: prova prima la fonte primaria, ripiega su una fonte secondaria se la primaria non è disponibile, e ripiega su uno stato "di emergenza" sicuro se nessuna delle due è disponibile. Ognuna di queste fonti è un "livello" (tier). Vedi il [Registro di affidabilità](confidence-ledger.md) per una lacuna nota nel comportamento attuale del livello di emergenza. |
| **Commissioning** (messa in servizio) | Il processo di portare un componente hardware nuovo o sostituito pienamente in servizio — assegnargli un'identità, verificare che riporti correttamente i dati e (per le zone di climatizzazione) dimostrare gradualmente che l'anello di controllo è sicuro prima di fidarsene senza supervisione. Vedi [Manutenzione ordinaria](../maintenance-tasks.md) per le versioni passo-passo di questo processo. |
| **Pre-live** | Il termine del progetto per "progettato e in gran parte costruito, ma non ancora installato fisicamente in casa." Quasi tutto in questa documentazione è pre-live, motivo per cui così tante affermazioni sono etichettate 🔵 PROGETTATO invece di 🟢 VERIFICATO — vedi il [Registro di affidabilità](confidence-ledger.md). |

## Correlati

- [Tabella hardware e indirizzi](hardware-table.md) — dove diversi di questi termini
  (relè, coil, registro, indirizzo Modbus) sono usati in una tabella concreta.
- [Registro di affidabilità](confidence-ledger.md) — spiega il sistema di etichette
  🟢/🔵/⚠️ usato in tutto questo sito.
- [Mappa dei documenti](doc-map.md) — se un termine qui ti rimanda a un file nel
  repository e non sei sicuro quale documento sia attuale o storico.
