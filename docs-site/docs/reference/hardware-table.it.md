# Tabella hardware e indirizzi

Questa pagina è il riferimento unico e consolidato per capire quale hardware esiste
nei tre sistemi della casa (bus CAN, illuminazione, climatizzazione), a cosa serve
ogni dispositivo, e tutti gli indirizzi Modbus e le assegnazioni di relè/canale
attualmente in uso. Se puoi tenere aperta una sola pagina mentre lavori
sull'installazione fisica, probabilmente è questa.

!!! note "Come leggere le etichette di affidabilità in questa pagina"
    🟢 **VERIFICATO** — confermato su banco o sul campo.
    🔵 **PROGETTATO** — costruito e pensato per funzionare così, ma non ancora
    provato con un'installazione reale (vero per quasi tutto ciò che segue — la casa
    non è ancora cablata fisicamente).
    ⚠️ **LACUNA NOTA** — questione realmente irrisolta.

## Famiglie hardware, in parole semplici

La casa ha standardizzato deliberatamente su una piccola famiglia di dispositivi
intercambiabili (vedi [Mappa dei documenti](doc-map.md) per dove è registrata questa
decisione — ADR-0014), in modo che un solo scaffale di scorte possa coprire un guasto
in quasi ogni parte della casa. 🔵 PROGETTATO

| Modello scheda | Ruolo | Usato da | Storia delle scorte |
|---|---|---|---|
| **LilyGO T-Connect Pro** (ESP32-S3, Ethernet W5500, RS485 + CAN nativi) | Controller | Controller climatizzazione (`devices/climate-control.yaml`) **e** controller illuminazione (`devices/light-controller.yaml`) — due schede fisiche separate, stesso modello | Un solo tipo di scheda di riserva copre un controller guasto su **entrambi** i sistemi — riflashala con l'entry point giusto e diventa qualunque controller sia andato in avaria. |
| **Waveshare ESP32-S3-RS485-CAN** (solo WiFi, CAN + RS485 isolati) | Monitor di salute del bus CAN | Solo il dispositivo dedicato al monitoraggio (`devices/health-monitor.yaml`) | Scheda a scopo unico, solo WiFi, dedicata a osservare la salute del bus — vedi [Mappa dei documenti](doc-map.md) per il perché questo dispositivo è stato separato (ADR-0015). |
| **Waveshare Modbus RTU Relay 32CH** | Banco relè a 32 canali | Climatizzazione (commutazione zone/pompe) **e** illuminazione (circuiti luce) — una scheda per sistema, entrambe all'indirizzo `0x2` | Una singola scheda relè di riserva sostituisce direttamente il banco relè di **entrambi** i sistemi — stesso modello, stesso indirizzo, nessuna riconfigurazione di indirizzo necessaria. |
| **Waveshare Modbus RTU Analog Output 8CH (B)** | Uscite analogiche 0–10V | Solo climatizzazione (velocità ventilatore fancoil, modulazione valvola miscelatrice) | Dispositivo esclusivo della climatizzazione; nessun gemello lato illuminazione con cui condividere scorte. Verifica di avere la variante **(B)** in tensione, non il modello base, che eroga invece 0–20mA in corrente — non sono intercambiabili. |
| **S1 Pro Multi-Sense** | Scheda sensore ambiente (temperatura, umidità, qualità dell'aria, radar di presenza LD2450) | Climatizzazione (rilevamento ambiente) | Scheda custom; vedi [Scheda sensore ambiente](../hardware/room-sensor.md) per quanto è noto sulla sua sostituzione — attualmente ⚠️ **LACUNA NOTA**, non esiste ancora una procedura di sostituzione documentata. |
| **CANBed RP2040** | Nodo bus CAN (dietro un pulsante a muro / integrato in schede sensore) | Bus CAN / illuminazione (decodifica pulsanti) | Firmware congelato, senza WiFi/OTA; l'identità vive in `registry/nodes.csv`, non sulla scheda stessa, quindi una scheda di riserva diventa un qualsiasi nodo una volta flashata con la configurazione di quel nodo. |

## Membri del bus Modbus e indirizzi

Nella casa ci sono **due bus RS485 separati**, non uno condiviso: il controller
climatizzazione ha il proprio, il controller illuminazione ha il proprio. Per
progetto usano lo stesso indirizzo per la scheda relè (vedi nota sotto).

### Bus climatizzazione (`rs485_bus`, target 38400 8E1)

| Dispositivo | Indirizzo Modbus | Canali | Note |
|---|---|---|---|
| T-Connect Pro (controller climatizzazione) | — (master del bus) | — | L'unico master Modbus su questo bus; nessun altro dispositivo può scrivere sul bus. |
| Scheda uscite analogiche 8CH (B) | `0x1` | `analog_output_1`–`analog_output_8` | Uscite 0–10V, registri di holding `0x0000`–`0x0007`. |
| Scheda relè 32CH | `0x2` | `relay_1`–`relay_32` | Coil `0x0000`–`0x001F`. |
| VMC (Cappellotto Air Fresh I, unità di ventilazione) | `0x10` | — | Ha un proprio set di registri specifico del dispositivo; vedi `climate/mev_modbus.yaml` nel repository, non riprodotto qui. |

I dati di temperatura/umidità/qualità dell'aria delle stanze **non** viaggiano affatto
su questo bus — arrivano tramite il bus CAN, con un ripiego (fallback) su Home
Assistant. Vedi la voce del [Glossario](glossary.md) sui livelli di failover se il
concetto non è familiare.

### Bus illuminazione (bus fisico separato, stesso target 38400 8E1)

| Dispositivo | Indirizzo Modbus | Canali | Note |
|---|---|---|---|
| T-Connect Pro (controller illuminazione) | — (master del bus) | — | Il suo bus separato; non collegato elettricamente al bus della climatizzazione. |
| Scheda relè 32CH | `0x2` | `relay_0`–`relay_31` (base 0 su questo bus) | Commutazione dei circuiti luce. |

!!! note "Perché `0x2` compare su entrambi i bus"
    L'ADR-0014 §4 rispecchia deliberatamente l'indirizzo della scheda relè (`0x2`) su
    entrambi i bus, climatizzazione e illuminazione, in modo che una singola scheda
    Relay 32CH di riserva possa essere inserita in **entrambi** i sistemi senza
    doverne prima riconfigurare l'indirizzo. La scheda uscite analogiche (`0x1`) e
    l'unità VMC (`0x10`) sono indirizzi esclusivi della climatizzazione — non esiste
    un dispositivo lato illuminazione a quegli indirizzi con cui rispecchiarli, quindi
    una scorta per questi due torna sempre e solo nel sistema di climatizzazione. 🔵 PROGETTATO

I parametri del bus (38400 baud, 8 bit dati, parità pari, 1 bit di stop — "38400 8E1")
sono la configurazione **target** su entrambi i bus, in attesa di una verifica in fase
di avviamento che confermi che ogni dispositivo fisico possa effettivamente
funzionare con quell'impostazione — l'unità di ventilazione (VMC) è il membro meno
flessibile ed è il vincolo determinante se non ci riesce. ⚠️ **LACUNA NOTA** fino a
quella verifica su hardware reale (ADR-0014 §4, punto aperto 1).

## Tabella di assegnazione relè (bus climatizzazione, indirizzo `0x2`)

Questa è la mappatura dei canali attualmente in vigore per la scheda relè a 32 canali
del sistema di climatizzazione. La fonte di verità nel repository è
`devices/climate-control.yaml` e i file di stanza/piano sotto `climate/rooms/**` — se
cambi un'assegnazione lì, aggiorna anche questa tabella, altrimenti le due andranno
alla deriva.

| Relè | Zona / circuito | Componente |
|---|---|---|
| `relay_1` | Radiante piano terra | Pompa di miscelazione |
| `relay_2` | Fancoil piano terra | Pompa diretta |
| `relay_3` | Radiante primo piano | Pompa di miscelazione |
| `relay_4` | Fancoil secondo piano | Pompa diretta |
| `relay_5` | — | Non allocato |
| `relay_6` | Anticamera | Radiante |
| `relay_7` | Bagno (piano terra) | Radiante |
| `relay_8` | Cucina | Radiante |
| `relay_9` | Soggiorno | Radiante |
| `relay_10` | Bagno Grande | Radiante |
| `relay_11` | Bagno Ospiti | Radiante |
| `relay_12` | Bagno Padronale | Radiante |
| `relay_13` | Camera Nord | Radiante |
| `relay_14` | Camera Ospiti | Radiante |
| `relay_15` | Camera Padronale | Radiante |
| `relay_16` | Camera Sud | Radiante |
| `relay_17` | Lavanderia | Radiante |
| `relay_18`–`relay_21` | — | Riservati (liberati da una passata migrazione della VMC; nulla li usa attualmente) |
| `relay_22`–`relay_32` | — | Capacità di riserva non allocata |

I fancoil non hanno un proprio canale relè. La circolazione del fancoil di ogni piano
gira sulla pompa condivisa di quel piano (`relay_2` o `relay_4` sopra); la velocità
del ventilatore del fancoil è invece controllata separatamente, tramite la scheda
uscite analogiche (tabella seguente).

Se stai [aggiungendo una nuova stanza](../maintenance-tasks.md#aggiungere-o-spostare-una-stanza-di-climatizzazione),
scegli un canale non allocato tra `relay_22`–`relay_32` (oppure `relay_5`) e aggiorna
questa tabella nella stessa modifica.

## Assegnazione canali uscite analogiche (bus climatizzazione, indirizzo `0x1`)

| Canale | Assegnazione |
|---|---|
| `analog_output_1` | Valvola miscelatrice radiante piano terra |
| `analog_output_2` | Valvola miscelatrice radiante primo piano |
| `analog_output_3` | Fancoil Soggiorno |
| `analog_output_4` | Fancoil Cucina |
| `analog_output_5` | Fancoil Locale Tecnico |
| `analog_output_6` | Fancoil Sottotetto |
| `analog_output_7` | Velocità ventilatore VMC primo piano |
| `analog_output_8` | Non allocato |

## Correlati

- [Quale dispositivo è guasto?](../hardware/index.md) — parti da lì per la
  risoluzione dei problemi hardware; questa pagina è il riferimento di
  indirizzi/assegnazioni a cui rimanda.
- [Manutenzione ordinaria](../maintenance-tasks.md) — aggiungere una stanza o un
  dispositivo Modbus richiede di scegliere un relè/canale libero dalle tabelle sopra.
- [Mappa dei documenti](doc-map.md) — dove sono registrate per intero le decisioni
  hardware sottostanti (ADR-0014, ADR-0015).
