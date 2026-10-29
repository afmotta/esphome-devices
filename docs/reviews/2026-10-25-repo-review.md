# Review del repository — 2026-10-25

| Campo | Valore |
|-------|--------|
| **Data** | 2026-10-25 |
| **Baseline** | `main` @ `9d0bc28` (Upgrade ESPHome to 2026.8.0, ADR-0022) |
| **Branch dei fix** | uno per issue, es. `claude/fix-r02-reboot-timeouts` |
| **Autore** | AI Assistant (Claude Code), su richiesta di Alberto |
| **Scopo** | Review completa (firmware, logiche, testing, documentazione) e registro vivo di issue e fix |

Questo documento è il **registro di riferimento** per le issue emerse dalla review e per i relativi fix.
Ogni fix aggiorna la riga del [tracker](#tracker-delle-issue) e la sezione *Fix applicato* dell'issue.

---

## Metodo

- `scripts/verification-battery.sh --native-only`: **14/14 step PASS** sulla baseline.
- `esphome config` (ESPHome 2026.8.0, secrets dummy di CI) su 16 configurazioni — tutti gli entry
  point della CI, le fixture `canbus/tests/compile_*.yaml`, i nodi generati `canbus/nodes/*.yaml` e
  gli harness e2e `climate/tests/harness/*.yaml`: **16/16 valide**.
- `esphome compile` e gli e2e host-platform **non eseguibili** nell'ambiente della review (il registry
  PlatformIO è bloccato dalla policy di rete, 403): restano coperti dalla CI su `main`.
- I comportamenti di ESPHome citati sono verificati sul **sorgente di ESPHome 2026.8.0**
  (`esphome/components/...`), non a memoria.

---

## Tracker delle issue

Legenda severità: 🔴 critica · 🟠 importante · 🟡 minore. Stato: ⬜ aperta · 🔧 in lavorazione · ✅ risolta · ⏸️ rimandata.

| ID | Sev. | Titolo | Stato | Fix |
|----|------|--------|-------|-----|
| [R-01](#r-01--il-pid-pilota-la-valvola-con-errore-in-valore-assoluto) | 🔴 | Il PID pilota la valvola con \|errore\| (heat/cool sulla stessa uscita) | ✅ | `1472a90`, `ed4d157` |
| [R-02](#r-02--i-controller-si-riavviano-ogni-15-minuti-senza-home-assistant) | 🔴 | I controller si riavviano ogni 15 min senza Home Assistant | ✅ | PR #67 |
| [R-03](#r-03--lilluminazione-non-raggiunge-mai-home-assistant) | 🔴 | Nomi dei servizi HA errati: l'illuminazione non raggiunge mai HA | ✅ | `2aeb15e` |
| [R-04](#r-04--il-tier-ha-del-failover-non-diventa-mai-nan) | 🔴 | Il tier HA del failover non diventa mai NaN (valori congelati) | ✅ | `ad79881` |
| [R-05](#r-05--loverride-del-radiante-scavalca-la-sicurezza-nan) | 🟠 | L'override del radiante scavalca la sicurezza NaN; boost bloccato | ⬜ | — |
| [R-07](#r-07--errori-can-invisibili) | 🟠 | Errori CAN invisibili (bridge TX, `ERR_CAN_*` mai impostati) | 🔧 parziale | `085bb05`, `a2db85c` |
| [R-07](#r-07--errori-can-invisibili) | 🟠 | Errori CAN invisibili (bridge TX, `ERR_CAN_*` mai impostati) | ✅ | `085bb05`, `a2db85c` |
| [R-09](#r-09--fail-safe-hardware-dei-relè) | 🟠 | Nessun fail-safe se il master Modbus si blocca | ⏸️ ADR-0024 *Proposed*: decisione del proprietario | ADR-0024 |
| [R-09](#r-09--fail-safe-hardware-dei-relè) | 🟠 | Nessun fail-safe se il master Modbus si blocca | ⏸️ ADR-0024 *Proposed*: decisione del proprietario | `710f088` |
| [R-10](#r-10--lacune-di-testing) | 🟠 | Lacune di testing e CI | 🔧 parziale | `2aeb15e`, `ad79881`, `1472a90`, `bf1aa11` |
| [R-11](#r-11--drift-della-documentazione) | 🟡 | Drift della documentazione | ✅ | `1472a90`, `2f56444`, `633025f` |
| [R-12](#r-12--temperatura-esterna-da-ha-congelata) | 🟠 | Temperatura esterna da HA: stesso pattern di R-04 | ✅ | `449be90`, `2763cdf` |
| [R-13](#r-13--windup-dellintegrale-pid) | 🟠 | Windup dell'integrale PID (nessun `min/max_integral`) | ⬜ | — |
| [R-14](#r-14--window-guard-riaccende-un-fancoil-boost) | 🟠 | Il window guard riaccende un fancoil `boost` fuori dal coordinatore | ⬜ | — |
| [R-15](#r-15--var-di-radiantyaml-ignorate) | 🟡 | `pwm_period`/`kp`/`ki`/`kd` passati a `radiant.yaml` ignorati | ⬜ | — |
| [R-16](#r-16--primo-boot-dei-pid-solo-cool) | 🟡 | Al primo boot i PID solo-cool partono in COOL | ⬜ | — |
| [R-17](#r-17--nessun-recovery-da-bus-off-sui-nodi-esp32) | 🟠 | Nessun recovery da bus-off sui nodi ESP32 (TWAI) | ⬜ | — |

---

## Issue critiche

### R-01 — Il PID pilota la valvola con errore in valore assoluto

**Dove:** `climate/packages/components/radiant.yaml:49`, `climate/packages/components/mixing_pump.yaml:76-77`,
`climate/packages/components/fancoil.yaml:57`.

**Problema.** `heat_output` e `cool_output` puntano alla **stessa** uscita. Il PID di ESPHome
(`pid_climate.cpp`, `update_pid_()` / `write_output_()`) **non usa la modalità HEAT/COOL** per scegliere
l'uscita — distingue solo OFF: con valore negativo scrive `-value` su `cool_output`. Con le due uscite
coincidenti la valvola riceve |errore|:

- **Radiante (7 zone), inverno:** stanza sopra setpoint ⇒ la valvola si apre in proporzione al
  surriscaldamento (retroazione positiva).
- **Valvola miscelatrice (2 piani), estate:** mandata *sotto* il minimo di punto di rugiada ⇒ il PID
  apre di più l'acqua fredda. La protezione anticondensa agisce al contrario.
- **Fancoil:** solo `cool_output`. In HEAT girano quando la stanza è troppo calda e non scaldano mai;
  il **sottotetto** ("Heating: Fancoil") non ha di fatto riscaldamento. Nelle stanze con boost
  (soggiorno, cucina) l'handler stagionale mette il fancoil in COOL a ogni passaggio di `hp_mode` a
  COOL, **scavalcando** il gate di commissioning `{zone}_boost_enabled`.

**Correzione prevista.** Uscite heat/cool distinte e *gated* sulla direzione dell'acqua prodotta dalla
sorgente (`hp_mode`): la direzione concorde scrive il livello, quella discorde scrive 0 — corretto
per ogni ordine di scrittura di `write_output_()`. Ruolo esplicito per i fancoil (boost / solo
raffrescamento / caldo+freddo). Test nativo della regola + e2e host.

**Fix applicato:** ✅ `1472a90` — `climate: gate PID heat/cool outputs on the heat pump's water (R-01)`

- **Regola** (`climate/protocol/pid_direction.h`):
  - La direzione heat è attiva solo con `hp_mode == "HEAT"`, quella cool solo con `hp_mode == "COOL"`; `SANITARY_ONLY`,
    un testo sconosciuto o null chiudono entrambe.
  - Ogni attuatore ha due template output gated. La direzione attiva inoltra il livello, quella inattiva inoltra 0.
  - È corretta per ogni ordine di scrittura di `write_output_()`: prima arrivano gli azzeramenti, poi al massimo una
    scrittura non nulla, sempre per ultima.
- **Radiante:**
  - `${room_slug}_radiant_heat_output` in `heat_only_radiant.yaml` e `${room_slug}_radiant_cool_output` in `radiant.yaml`
    inoltrano a `${room_slug}_radiant_output`.
  - `_radiant_output` resta lo stadio finale (override + slow PWM) su cui scrive `fancoil_boost`.
- **Valvole miscelatrici:** `${valve_slug}_heat_output` e `_cool_output` inoltrano all'uscita analogica. In COOL, una
  mandata sotto il minimo di dew point ora **chiude** la valvola.
- **Fancoil:** nuova var obbligatoria `fancoil_role`, con la parte specifica in `fancoil_role_<ruolo>.yaml`:
  - `boost` (soggiorno, cucina): l'handler stagionale porta il PID solo a OFF; lo mette in COOL esclusivamente il
    coordinatore boost. Il bypass di `{zone}_boost_enabled` è chiuso.
  - `cool_only` (locale tecnico): COOL in stagione COOL, altrimenti OFF.
  - `heat_cool` (sottotetto): ha un'uscita heat gated e segue HEAT, COOL e OFF. **Il sottotetto ora scalda.**
- **Autotune**, documentato nei commenti:
  - va eseguito nella stagione del loop;
  - sui loop con entrambe le uscite l'escursione reale è 0..1, quindi i guadagni stimati vanno dimezzati;
  - i fancoil `boost` vanno messi in COOL a mano prima di lanciarlo.
- **Test:**
  - `climate/tests/test_pid_direction.cpp` riproduce fedelmente `write_output_()` di ESPHome 2026.8.0. Copre
    hp_mode × valore e tutte le transizioni. Con il gate disattivato il test fallisce, come previsto.
  - Harness host `climate/tests/harness/radiant_direction.yaml` con i package reali e
    `climate/tests/e2e/test_radiant_direction.py` (20 casi). Il subagente li ha **eseguiti davvero**: binario host costruito
    con `esphome compile --only-generate` + g++, **20/20 PASS**; con il gate disattivato 7 casi falliscono.
  - Aggiunti alla battery, al gate `esphome config` della CI e agli e2e su `main`.
- **Verifica nella config risolta di climate-control:** 18 PID, nessuno con `heat_output == cool_output`; tutte le uscite
  sono wrapper gated.
- **Altre verifiche:** `verify_seasonal_mode_aggregation.py` passa (16 heat, 11 cool). In un worktree isolato sul commit
  la battery nativa passa e `esphome config` è OK su climate-control e sui 4 harness.
- **Documentazione:** in `climate/CLAUDE.md` la sezione "Dual PID Pattern", che non era mai stata implementata, è sostituita
  dal pattern gated, con la regola *mai la stessa uscita per heat e cool*. L'esempio "Adding a New Room" ora cita
  `fancoil_role`.
- **Non verificato qui:** la compilazione ESP32 di `devices/locals/climate-control.yaml`.

**Seguito R-01b:** ✅ `ed4d157` — `climate: pump demand follows the gated actuation, not PID intent (R-01b)`

- **Problema introdotto da R-01.** `*_pid_is_active` è l'unico ingresso della domanda delle pompe di circolazione
  (`*_any_zone_open` dei piani e pompa diretta del secondo piano) e seguiva l'*intenzione* del PID. Dopo il gating, in HEAT,
  una stanza sopra setpoint risultava "cooling": la pompa sarebbe partita con tutte le valvole tenute chiuse.
- **Fix.** `is_active` applica lo stesso gate tramite `pid_direction::actuating()`: il riscaldamento conta solo con
  `hp_mode` HEAT, il raffrescamento solo con COOL. `is_heating` e `is_cooling` restano l'intenzione non filtrata, che serve
  al seasonal mode; `verify_seasonal_mode_aggregation.py` passa.
- **Test:**
  - nativi: matrice azione × modo, più la verifica che `actuating()` coincida con "il sink condiviso resta non nullo";
  - e2e: 14 nuovi casi per la domanda pompe (matrice stagione × temperatura su 5 zone e sulla valvola miscelatrice). Il file
    passa **34/34** sul binario host; col vecchio lambda ripristinato 7 casi falliscono.
- **Verificato** in un worktree isolato sul commit: battery nativa PASS ed `esphome config` di climate-control OK.
  `${seasonal_mode_id}` risolve in `hp_mode` in tutti i 18 lambda.
- **Effetto collaterale (positivo):** le dashboard che leggono `*_is_active` come "zona attiva" ora mostrano "valvola
  davvero aperta".

---

### R-02 — I controller si riavviano ogni 15 minuti senza Home Assistant

**Dove:** `boards/t-connect-pro.yaml` (climate-control, light-controller),
`boards/waveshare-s3-rs485-can.yaml` (health-monitor).

**Problema.** Default `api: reboot_timeout: 15min` (confermato nella config risolta): il sorgente fa
`"No clients; rebooting"`. Senza HA il controller climate si riavvia ogni 15 minuti, perdendo integrali
PID, timer di boost e stato di arbitraggio — in contrasto con l'autonomia dichiarata. An-Penta/An-Quad
avevano già `reboot_timeout: 0s`. Anche `wifi: reboot_timeout` (default 15 min) riavvia se il WiFi non
si connette, e il watchdog WiFi **ignora Ethernet** (confermato sul sorgente, vedi sotto): con l'AP
spento un controller sano su Ethernet si riavvierebbe comunque.

**Correzione prevista.** `api: reboot_timeout: 0s` su t-connect-pro e waveshare-s3-rs485-can (An-Penta/An-Quad già a 0s); `wifi: reboot_timeout: 0s` sulle
board dual-interface (Ethernet primaria).

**Fix applicato:** ✅ PR #67 — `boards: disable API/WiFi reboot timeouts on autonomous controllers (R-02)`

| Board | `api: reboot_timeout` | `wifi: reboot_timeout` | Device |
|-------|----------------------|------------------------|--------|
| `boards/t-connect-pro.yaml` | `0s` (nuovo) | `0s` (nuovo) | climate-control, light-controller |
| `boards/waveshare-s3-rs485-can.yaml` | `0s` (nuovo) | 15min (default, voluto) | health-monitor |
| `boards/an-penta-plus.yaml` | `0s` (già in `devices/an-penta-1.yaml`) | `0s` (nuovo) | an-penta-1 |
| `boards/an-quad.yaml` | `0s` (già in `devices/an-quad-1.yaml`) | 15min (default, voluto) | an-quad-1 |

- **Verifica sul sorgente ESPHome 2026.8.0:** `api_server.cpp:151-155` riavvia con "No clients; rebooting".
  In `wifi_component.cpp`, `last_connected_` è scritto solo al setup (r. 650) e in
  `WIFI_COMPONENT_STATE_STA_CONNECTED` (r. 825); il componente wifi non ha riferimenti a ethernet e
  `network: priority:` influenza solo la setup priority. Quindi il watchdog WiFi non tiene conto di Ethernet.
- **Scelta per le board solo WiFi** (health monitor, An-Quad, S1 Pro): il reboot WiFi resta al default perché,
  senza Ethernet, è il percorso di recupero da uno stack WiFi bloccato.
- **Verificato:** `esphome config` valido sui 5 entry point, con i valori risolti indicati in tabella.
- **Da verificare su hardware al bring-up:** controller acceso per più di 15 min con HA spento e con l'AP spento;
  conferma sul campo che il watchdog WiFi ignora Ethernet (controller sano su Ethernet con AP spento >15 min non si
  riavvia); Ethernet giù + AP giù: nessun auto-recupero atteso (trade-off accettato, vedi commento in
  `boards/t-connect-pro.yaml`).
- **Non toccate:** le board legacy senza consumer (`a6`, `a16`, `waveshare-s3`).

---

### R-03 — L'illuminazione non raggiunge mai Home Assistant

**Dove:** `devices/light-controller.yaml:42` (`device_name: light-controller`),
`canbus/tools/generate_nodes.py:629`, `canbus/home-assistant/ha_manifest_package.yaml`,
`canbus/home-assistant/ha_arbitration_automations.yaml:38`, `canbus/tests/test_generate_exports.py`.

**Problema.** I servizi API sono esposti come `esphome.light_controller_ha_*`, ma il package HA generato
e l'automazione ACK chiamano `esphome.canbus_gateway_*` (nome del vecchio gateway pre-ADR-0015).
Nessun heartbeat arriva ⇒ `ha_ready` sempre falso ⇒ **ogni pressione va in fallback** e nessun evento
`esphome.canbus_button` raggiunge HA. Il test `test_ha_package_bakes_hash` verifica proprio il nome
sbagliato.

**Correzione prevista.** Nomi dei servizi derivati dal `device_name` del lighting controller; test di
contratto che incrocia `device_name`, servizi dichiarati in `lighting/packages/buttons.yaml` e
automazioni HA.

**Fix applicato:** ✅ `2aeb15e` — `canbus: call the light controller's real HA service names (R-03)`

- **Unica fonte del nome.** `canbus/tools/generate_nodes.py` ha la costante `LIGHTING_DEVICE_NAME = "light-controller"`,
  da cui derivano `LIGHTING_HA_SLUG` e `LIGHTING_SERVICE_PREFIX`. Da lì vengono generati l'id e l'action dell'heartbeat e
  gli entity id del package di health, il cui output resta identico byte per byte. È una costante e non una lettura dello
  YAML, così il generatore resta ermetico anche nei test che usano repo temporanei; il contratto la lega al file reale.
- **Package rigenerato.** `ha_manifest_package.yaml` ora chiama `esphome.light_controller_ha_readiness_heartbeat`
  (id `light_controller_readiness_heartbeat`).
- **Automazione ACK** (`ha_arbitration_automations.yaml`, mantenuta a mano): action `esphome.light_controller_ha_ack_event`,
  id `light_controller_ack_button_events`, header aggiornato.
- **Nuovo test di contratto `canbus/tests/test_ha_contract.py`** (solo stdlib, 5 test). Legge i file reali e verifica che:
  - il `device_name` in `devices/light-controller.yaml` coincida con la costante del generatore;
  - i servizi dichiarati in `lighting/packages/buttons.yaml` corrispondano alle action del package (renderizzato e su
    disco) e dell'automazione ACK;
  - gli entity id `HA Ready` e `Fallback Events` corrispondano a quelli usati dal package di health;
  - non resti alcun `canbus_gateway`.
  
  È stato provato anche in negativo: fallisce se si ripristina il vecchio nome o si rinomina l'entità. Il test era stato
  aggiunto alla battery nativa, che è anche il job `native` della CI (`scripts/verification-battery.sh`), e a `canbus/CLAUDE.md`.
- **Verificato:** tutti i test Python passano (18 + 47 + 6 + 5). `verification-battery.sh --native-only` passa per intero,
  idempotenza del generatore compresa.
- **Azione una tantum lato HA** (gli id delle automazioni cambiano; il sistema è pre-live, quindi è accettabile):
  1. ricaricare il package `ha_manifest_package.yaml`;
  2. sostituire l'automazione ACK;
  3. eliminare le vecchie automazioni orfane `canbus_gateway_*`;
  4. controllare che `binary_sensor.lighting_controller_ha_ready` diventi `on` entro circa 5 s. Se il controller era già stato adottato in HA con un nome precedente, gli entity id restano quelli della prima registrazione (HA non li rinomina): verificare in Impostazioni > Entità e rinominare `binary_sensor.lighting_controller_ha_ready` / `sensor.lighting_controller_fallback_events` (o rimuovere e riaggiungere il dispositivo) prima di fidarsi degli alert.

---

### R-04 — Il tier HA del failover non diventa mai NaN

**Dove:** `climate/room_sensors.yaml:109,116`.

**Problema.** `filter_out: nan` sui sensori `homeassistant`: il sorgente pubblica NAN quando HA invia
`unavailable`, ma il filtro lo scarta. Il sensore inoltre non ha staleness: a HA disconnesso conserva
l'ultimo valore. PID, punto di rugiada e boost lavorano su valori **congelati** indefinitamente. Oggi
solo il soggiorno ha un nodo CAN: 12 zone su 13 dipendono solo da questo tier.

Nota: risolve anche la discrepanza "5 minuti" del confidence-ledger — il PID azzera le uscite **subito**
quando riceve NaN (`pid_climate.cpp:130`), ma per R-04 e R-05 quel NaN spesso non arriva o viene
scavalcato.

**Correzione prevista.** Rimuovere il filtro; il tier HA vale NaN se il valore è `unavailable` oppure se
l'API non ha un client connesso da oltre un periodo di grazia. Test nativo della regola + e2e host.

**Fix applicato:** ✅ `ad79881` — `climate: make the HA sensor tier go NaN when HA is gone (R-04)`

- **Valori `unavailable` di nuovo visibili.** Rimossi i due `filter_out: nan`: `unavailable` e `unknown` di HA arrivano
  al failover come NaN.
- **Il failover legge ora sensori filtrati per staleness** (`${room_slug}_temp_ha_gated`, `${room_slug}_humidity_ha_gated`,
  interni). Restituiscono il valore grezzo finché c'è un client API **con sottoscrizione agli stati** connesso, oppure
  entro un periodo di grazia dall'ultima connessione; poi NaN. Gli id grezzi `_temp_ha` e `_humidity_ha` restano invariati.
- **Criterio di connessione:** `api::global_api_server->is_connected_with_state_subscription()` (`api_server.cpp:660`),
  l'equivalente C++ di `api.connected: state_subscription_only: true`. L'integrazione di HA invia sempre la
  sottoscrizione agli stati, mentre `is_connected()` conterebbe qualsiasi client.
- **Grazia di 5 min** (`ha_staleness_grace_s: "300"`), sufficiente a coprire un riavvio di HA. Il criterio è la vita della
  connessione e non il tempo dall'ultimo aggiornamento, perché HA invia solo i cambi di stato.
- **Regola pura** in `climate/protocol/ha_tier.h`:
  - aritmetica su `millis()` sicura al wrap;
  - scadenza memorizzata finché non c'è una riconnessione;
  - al boot il gate è chiuso;
  - un NaN in ingresso passa come NaN.
  
  Allo scadere della grazia anche il sensore grezzo viene azzerato a NaN, così una riconnessione non riespone il valore
  vecchio prima che HA invii quello nuovo.
- **Test:**
  - `climate/tests/test_ha_tier.cpp`: 9 casi nativi (connesso, boot, entro e oltre la grazia, riconnessione, blip, NaN,
    wrap di `millis()`, scadenza che sopravvive a un wrap completo); aggiunto alla battery.
  - Nuovo harness host `climate/tests/harness/room_sensors.yaml`, che include `room_sensors.yaml` reale.
  - `climate/tests/e2e/test_room_sensors.py`: un finto HA risponde alla sottoscrizione agli stati. Coperti: valore
    numerico → tier "HA", `unavailable` → Emergency, disconnessione breve → resta "HA" (temperatura e umidità), disconnessione oltre la
    grazia → NaN, e a riconnessione senza stato da HA il grezzo azzerato mantiene Emergency/NaN (temperatura e umidità).
  - Aggiunti a un job CI host su ogni PR e alla battery completa; l'harness è aggiunto anche al gate `esphome config` della CI.
- **Verificato:**
  - battery nativa PASS in un worktree isolato sul commit;
  - `esphome config` OK su climate-control, sui due harness climate, su light-controller e health-monitor;
  - l'API scelta esiste in 2026.8.0.
- **Non verificato qui** (PlatformIO bloccato): la compilazione ESP32 per il device, che gira in CI su `main`.
- **e2e eseguito in locale (ora anche in CI sulle PR)** su un binario host costruito localmente (`esphome compile --only-generate` + g++):
  **4/4 PASS**, stabile su 3 esecuzioni. Mutation check:
  - con un tracker che non scade mai, `test_disconnect_past_grace_is_nan_then_recovers` fallisce;
  - con la grazia a 0, `test_disconnect_within_grace_keeps_value` fallisce;
  - rimettendo `filter_out: nan`, `test_unavailable_ha_state_is_emergency` fallisce.

  Il ramo `: NAN` di `ha_tier_gate` è coperto solo dal test nativo, perché a runtime è ridondante con il reset a NaN del
  sensore grezzo.
- **Rischio residuo documentato:** anche `esphome logs` si sottoscrive agli stati per default. Una sessione di log lasciata
  aperta durante un blackout di HA mantiene vivo il valore; per evitarlo usare `--no-states`.
- **Latenza:** un cambio di valore da HA arriva al PID con fino a ~20 s di ritardo (gate a 10 s più failover a 10 s).
  È trascurabile per la temperatura ambiente.
- **Minimo di mandata per piano:** `ground_floor_supply_temp_minimum` e `first_floor_supply_temp_minimum` mantengono il valore
  precedente (mai più basso) finché il punto di rugiada di una stanza membro è NaN, perché il `max` della `combination`
  scarta le sorgenti NaN e altrimenti la stanza uscirebbe dalla protezione.
- **Conseguenza operativa:** finché le altre 12 zone non hanno un nodo CAN, un blackout di HA oltre la grazia
  (`ha_staleness_grace_s`, 300 s) porta tutte e 12 in Emergency (uscite PID a 0); la grazia è la leva da regolare.
  Anche le entità che HA riporta `unavailable`/`unknown` mentre si riavvia valgono NaN subito, per scelta (tenere
  l'ultimo valore è il congelamento che R-04 elimina).
- **Interazione con R-05:** l'override del radiante scavalca ancora il NaN, quindi R-05 resta necessaria.

---

## Issue importanti

### R-05 — L'override del radiante scavalca la sicurezza NaN

`heat_only_radiant.yaml:99` applica l'override anche quando il PID scrive 0 per sensore NaN, e
`should_end_boost` ritorna false con delta NaN (`fancoil_boost.yaml:464`): se il sensore muore durante
un boost la zona resta al **100% di freddo** indefinitamente.

_Nota da R-01b:_ l'override del boost tiene aperta la valvola radiante scavalcando PID e gate. Inoltre
`ground_floor_radiant_any_zone_open` non include `soggiorno_boost_active` e `cucina_boost_active`. Oggi in boost la pompa
gira comunque, perché il PID radiante è in COOLING; ma il fix di R-05 dovrebbe trattare l'override attivo come domanda
pompa, oppure aggiungere i `*_boost_active` alla somma.

### R-06 — Doppia azione con binding toggle

ACK timeout a 500 ms con binding `toggle` ⇒ possibile doppio toggle (nessun effetto visibile). L'ACK di
HA parte inoltre *prima* di eseguire l'azione. Preferire on/off nei binding e alzare il timeout.

**Fix parziale:** `50103e2` — `canbus: warn on every toggle binding at generation time (R-06, partial)`

- `bindings.advisories()` restituisce un avviso deterministico per ogni binding `op: toggle`, con nodo, bottone e
  destinazione, e raccomanda `on`/`off`.
- `generate_nodes.py` lo stampa come `WARNING:` su stderr. Exit code, file generati e hash del manifest non cambiano.
  L'header di `registry/bindings.yaml` lo menziona.
- Test: due nuovi casi in `test_bindings.py`, più una prova manuale del generatore in un repo temporaneo.
- **Rimandati (⏸️):**
  - Il valore di `ack_timeout_ms` richiede dati da banco (ADR-0003 open item 2).
  - L'ACK di HA che parte prima dell'azione è un cambio di design: un'automazione ACK generata dal manifest dovrebbe
    rispondere dopo l'azione. Oggi i binding sono vuoti, quindi il rischio non è ancora attivo.

### R-07 — Errori CAN invisibili

Il bridge ignora il ritorno di `send_data` (`canbus/packages/bridge.yaml:135,138`): un frame fallito
viene contato come "forwarded". `ERR_CAN_TX_FAIL` / `ERR_CAN_BUS_OFF` non vengono mai impostati da
alcun firmware: l'evento `node_error` (classe maintenance, logbook: ADR-0011) scatta solo per l'overflow del bridge.

**Fix applicato:** 🔧 parziale — `ERR_CAN_BUS_OFF` è rimandato a R-17; `085bb05` (`canbus: report CAN TX failures instead of losing them silently (R-07)`) + `a2db85c`
(collegamento alla battery e documentazione).

- **Bridge:**
  - `bridge_drain_send()` riceve l'esito di `send_data()`: un frame esce dalla coda e conta come `forwarded` solo se il
    controller lo accetta.
  - Un frame rifiutato resta in testa e viene ritentato al tick successivo, mantenendo l'ordine FIFO e il ritmo di
    10 ms che protegge i 3 buffer TX dell'MCP2515.
  - Dopo circa 5 tick (circa 50 ms al tick nominale di 10 ms, circa 100 ms dove il loop è limitato, es. T-2CAN) il frame viene scartato e conteggiato in `dropped_tx`, con `ERR_CAN_TX_FAIL`
    **permanente**, accanto a `ERR_BRIDGE_QUEUE_OVERFLOW`.
- **Nodi** (`canbus/protocol/tx_health.h`, nuovo):
  - ogni invio rifiutato (bottoni, sensor kit, bridge, heartbeat, attuatori An-Penta/An-Quad) attiva `ERR_CAN_TX_FAIL`
    sul prossimo heartbeat;
  - il flag si azzera solo quando un heartbeat che lo portava è stato accettato. Così HA vede sia il guasto sia il
    recupero;
  - viene aggiunto in OR al momento dell'heartbeat, non in `error_flags`, così non interferisce con i bit permanenti.
- **`ERR_CAN_BUS_OFF`** resta riservato (rimandato a [R-17](#r-17--nessun-recovery-da-bus-off-sui-nodi-esp32)): ESPHome 2026.8.0 non espone lo stato di bus-off (`mcp2515` e `esp32_can` sono
  classi `final` con helper protetti). È documentato accanto alla costante.
- **Gateway lighting:** un `CAT_OUTPUT` di fallback rifiutato ora produce un log di errore.
- **Test:**
  - nuovo `canbus/tests/test_tx_health.cpp`, aggiunto alla battery;
  - `test_bridge_forwarding.cpp` esteso: ordine dei retry, scarto dopo il limite, flag permanente, cadenza.
- **Verificato:**
  - battery nativa PASS;
  - `esphome config` OK su 4 fixture, 2 nodi generati, An-Penta, An-Quad, light-controller e health-monitor;
  - i lambda sono stati compilati anche contro un mock host.
- **Non verificato:** compilazione ESP32/RP2040 e comportamento reale del retry sul bus.
- **Limiti noti:**
  - Sull'MCP2515 "OK" significa "caricato in un buffer TX", non "ricevuto": un bus morto emerge solo quando i 3 buffer
    restano occupati.
  - Il `CAT_OUTPUT` di fallback resta fire-and-forget: se si perde, ora viene loggato, ma non ritentato.

### R-08 — NaN nei timer e soglie da HA

`delay: predictive_minutes * 60000` con NaN ⇒ ritardo indefinito (probabile boost immediato). La
velocità minima MEV arriva ancora da HA (`homeassistant` sensor), mentre le soglie di sicurezza sono
già state rese locali.

**Fix parziale (R-08b, MEV):** ✅ `e1d8e68` (`climate: make MEV min fan speed, cascade thresholds and delays local numbers (R-08b)`)
+ `bd32bc6` (collegamento a battery/CI e documentazione).

- **Valori resi locali.** Diventano `number` template sul controller, persistenti (`restore_value`, `entity_category: config`),
  con gli stessi id e default uguali ai vecchi helper:

  | Entità | Range | Default | Unità MEV |
  |---|---|---|---|
  | `<mev>_min_fan_speed` | 0–50 % (primo piano: 0–30 %) | 20 | entrambe |
  | `<mev>_escalation_threshold` | 50–100 % | 80 | primo piano |
  | `<mev>_deescalation_threshold` | 35–50 % | 40 | primo piano |
  | `<mev>_escalation_delay` | 1–120 min | 10 | primo piano |
  | `<mev>_deescalation_delay` | 1–120 min | 15 | primo piano |
- **Range ristretti rispetto ai vecchi helper (0–100).** Scelta voluta: le soglie di escalation e de-escalation non possono
  incrociarsi (cascata senza oscillazioni) e il minimo del primo piano resta sotto la soglia di de-escalation (la
  velocità finale non scende sotto il minimo: con minimo >= soglia la cascata non uscirebbe più da Deumidifica/Integrazione).
  Un valore persistito con il vecchio range viene ripristinato così com'è (il `number` template limita solo le scritture): va reinserito. I default 80/40 sostituiscono i 70/30 raccomandati dalle
  vecchie guide.
- **Problema risolto.** Prima, con HA giù, le soglie a NaN disattivavano in silenzio la cascata di deumidificazione e i
  ritardi calcolavano `NaN * 60000`.
- **Lato HA:**
  - `mev_helpers.yaml` perde i 6 helper obsoleti;
  - la dashboard `system-monitoring` punta ai numeri del controller;
  - README e QUICK_START sono aggiornati;
  - ADR-0018 è emendato.
- **Restano su HA i limiti di domanda** CO2/VOC/NOx/PM/umidità (`proportional_demand_sensor.yaml`). Con HA giù la domanda
  scende al fallback del 20%: degrada senza danni.
- **Verificato:** e2e host `test_mev_ventilation.py` **6/6**, rieseguito anche da me, con i due coordinatori reali e senza
  HA; `esphome config` OK.
- **Azione una tantum lato HA:** cancellare `input_number.mev_minimum_fan_speed`, `ground_floor_mev_minimum_fan_speed`,
  `mev_escalation_fan_threshold`, `mev_deescalation_fan_threshold`, `mev_escalation_delay_minutes` e
  `mev_deescalation_delay_minutes`, ed eventualmente reinserire i valori personalizzati sui numeri del controller.
- **`predictive_minutes` (R-08a):** in lavorazione con R-05.

### R-09 — Fail-safe hardware dei relè

Se il master si blocca, i relè Modbus mantengono l'ultimo stato (valvole/pompe accese). Valutare un
watchdog o un timeout lato scheda relè.

**Proposta:** `docs/adr/0024-actuator-fail-safe-on-controller-loss.md`, stato **Proposed**. Nessun firmware è cambiato:
la decisione spetta al proprietario.

- **Già coperto da ESPHome** (verificato sul sorgente 2026.8.0): un loop bloccato. Il task watchdog lo riavvia in circa 5 s.
- **Non coperto:**
  - controller morto o senza alimentazione;
  - bus RS485 interrotto con il controller sano;
  - boot loop: dopo 10 tentativi parte il safe mode senza Modbus.
  
  In tutti questi casi le schede **mantengono l'ultimo stato**: i relè hanno `restore_mode: DISABLED` e al boot non viene
  scritto nulla.
- **Cosa offrono le schede:** la Relay 32CH ha comandi **flash-on/flash-off temporizzati**; nessun timeout per perdita
  di comunicazione trovato su nessuna delle due schede. Fonti e livello di fiducia: nell'ADR.
- **Raccomandazione (dettagli nell'ADR-0024):** un relè di riserva ri-armato con flash-on ogni 15 s (impulso di 60 s)
  che comanda un contattore in serie all'alimentazione delle **sole pompe** (SG-Ready escluso), come "dead-man"; ripiego:
  contattore con watchdog esterno. Fermare le pompe protegge dal funzionamento fuori controllo, non dal gelo: vedi i
  prerequisiti dell'ADR (O9).
- **Da verificare al banco prima di decidere:** il gate dell'ADR (O1–O5, O7, O9; O6 e O8 per il boot sicuro).

### R-10 — Lacune di testing

- La composizione climate reale non ha test di comportamento (R-01 sarebbe stato intercettato da un e2e
  host "stanza sopra setpoint in HEAT ⇒ valvola a 0").
- `climate/tests/e2e/test_fancoil_boost.py` esiste ma non gira né in CI né nella battery.
- Compile ed e2e girano solo su push a `main`.
- Manca un test di contratto servizi API ↔ automazioni HA (R-03).
- I test C++ usano `assert()` nudo (nessun messaggio, spariscono con `-DNDEBUG`).
- `CLAUDE.md` cita hook pre-commit inesistenti; nessun yamllint.

**Progressi** (fix parziale):
- **Nuovi test aggiunti con i fix:**
  - contratto servizi API ↔ automazioni HA: `test_ha_contract.py` (R-03);
  - test nativi `test_ha_tier.cpp` (R-04) e `test_pid_direction.cpp` (R-01);
  - e2e host `test_room_sensors.py` (R-04) e `test_radiant_direction.py` (R-01), che coprono il comportamento della
    composizione climate reale.
- **`bf1aa11`:**
  - `test_fancoil_boost.py` è ora nella CI su `main` e nella battery: 8/8, stabile su 4 esecuzioni;
  - il suo harness entra nel gate `esphome config` della CI;
  - `conftest.py` fallisce subito se la porta API 6053 è già occupata, invece di collegarsi al binario sbagliato.
- **Verifica locale indipendente** dopo tutti i fix, su binari host costruiti con g++: failover 1/1, room_sensors 4/4,
  fancoil_boost 8/8, radiant_direction 34/34.
- **Restano aperti:**
  - compile ed e2e (tranne room_sensors) solo su push a `main`, non sulle PR;
  - `assert()` nudo nei test C++;
  - nessun pre-commit né yamllint.

### R-11 — Drift della documentazione

- ~~`climate/CLAUDE.md:99` descrive un "Dual PID Pattern" che il codice non implementa.~~ Sostituito in `1472a90` (R-01).
- Range di tuning fancoil (Kp 1.0–2.0) incoerenti con il default 0.2 di `fancoil.yaml`.
- `CLAUDE.md` radice: versione 1.17 nell'intestazione vs changelog fino a 1.19; indice ADR fermo a
  0017/0019 mentre esistono fino a 0023 (0019 assente).
- Changelog molto lungo dentro `CLAUDE.md`: meglio un `CHANGELOG.md` separato.

**Fix applicato:** ✅ `2f56444` (`docs: fix documentation drift, split out CHANGELOG.md (R-11)`) + `633025f` (istruzioni Copilot).

- **`CLAUDE.md` alla radice:**
  - versione 1.22 (le voci 1.20/1.21 di R-02/R-04 sono nel `CHANGELOG.md`);
  - range degli ADR 0001…0023, con la nota che lo 0019 non è mai esistito (numero saltato, assente dalla storia git);
  - il changelog è spostato in **`CHANGELOG.md`**, con una voce 1.22 per R-11 (e per le note su R-01, R-03, R-10) accanto alle voci 1.20/1.21 di R-02/R-04;
  - sezione "Failover Architecture" riscritta: tier HA → NaN su `unavailable` o dopo 5 min, Emergency → PID a 0
    **subito**. Non esiste più alcuno "spegnimento dopo 5 minuti".
- **`climate/CLAUDE.md`, Appendice D:** guadagni allineati al codice (radiante 0.8/0.005/0.05, fancoil 0.2/0.01/0.05,
  valvola miscelatrice 0.2/0.01/0.0), più gli avvertimenti sull'autotune.
- **docs-site (EN + IT):**
  - confidence-ledger: discrepanza dei "5 minuti" marcata come risolta, con una riga "DESIGNED" per la verifica al banco;
  - monitoring, troubleshooting climate e maintenance-tasks allineati;
  - doc-map aggiornata con il range ADR.
- **`docs/architecture/architecture-diagram.md`:** la sezione 4 (failover) è riscritta; il resto del file è segnalato come
  storico Gen-1.
- **`.github/copilot-instructions.md`:** al posto del pattern "un PID con heat e cool sulla stessa uscita" ora descrive il
  pattern gated e `fancoil_role`.
- **Lasciati com'erano** (storico Gen-1, da riscrivere a parte): il resto di `architecture-diagram.md`,
  `docs/product-brief.md` e `docs/deployment-guide.md`. Il sito MkDocs non è stato ricompilato: le pagine sono controllate
  solo sul diff.

### R-12 — Temperatura esterna da HA congelata

_Emersa durante il fix di R-04._

- **Problema.** `climate/outdoor.yaml:39-45` (`outdoor_temp_ha`) ha lo stesso pattern di R-04: `filter_out: nan` e nessuna
  staleness. Un valore esterno congelato alimenta la compensazione climatica e la media a 24 h del seasonal mode.
- **Impatto.** Non c'è rischio di condensa, perché la protezione dew point usa i sensori delle stanze. Il fix è
  lo stesso: rimuovere il filtro e aggiungere un `HaTierTracker`.
- **Altri sensori `homeassistant` valutati e lasciati com'erano:**
  - `window_guard.yaml`: con HA giù il guard si degrada in un no-op, come previsto dal design.
  - I limiti di `proportional_demand_sensor`: sono dati di configurazione.
  - Le soglie MEV: vedi R-08.

**Fix applicato:** ✅ `449be90` (`climate: make the outdoor-temperature HA tier go NaN when HA is gone (R-12)`) + `2763cdf`
(collegamento a battery e CI).

- **Fix:** in `climate/outdoor.yaml` è rimosso `filter_out: nan` e il failover legge il nuovo `outdoor_temp_ha_gated`, con
  lo stesso gate `ha_tier.h` di R-04 (grazia `ha_outdoor_staleness_grace_s`, default 300 s).
- **Consumatori in caso di NaN** (analizzati, nessuna modifica necessaria):
  - `weather_compensation.yaml` non scrive nulla e logga un avviso al massimo ogni 10 min. Il target della valvola
    miscelatrice resta l'ultimo, limitato tra mandata minima e massima, e i PID di stanza continuano a correggere.
  - La media a 24 h scarta i campioni NaN e resta congelata durante il blackout; oggi è solo diagnostica.
  - Il Tier 2 del seasonal mode è ancora un placeholder.
- **Verificato:**
  - e2e host `test_outdoor.py`: **4/4**, rieseguito anche da me. Con un gate sempre aperto il caso "oltre la grazia"
    fallisce, come previsto.
  - `esphome config` OK su climate-control e sull'harness; battery nativa PASS.

_Le issue R-13–R-16 sono emerse durante il fix di R-01._

### R-13 — Windup dell'integrale PID

`pid.yaml` non imposta `min_integral` / `max_integral`. Con il gating, la direzione inattiva accumula integrale senza
limiti: per esempio, una stanza sopra setpoint in un pomeriggio invernale. Quando poi scende sotto target, può restare
fredda a lungo. Aggiungere limiti in `control_parameters`.

### R-14 — Window guard riaccende un fancoil boost

`window_guard.yaml` ripristina il modo salvato (COOL) se il PID è OFF a fine recovery. Se un boost è terminato mentre la
finestra era aperta, un fancoil `boost` torna acceso come raffrescatore permanente, scavalcando il coordinatore e il gate.

### R-15 — Var di radiant.yaml ignorate

`pwm_period`, `kp`, `ki` e `kd` passati a `radiant.yaml` vengono ignorati, perché vincono i `defaults:` di
`heat_only_radiant.yaml`. Oggi il problema è invisibile perché soggiorno e cucina passano i valori di default.

### R-16 — Primo boot dei PID solo-cool

Un PID con sola `cool_output` (fancoil `boost` e `cool_only`) senza stato salvato parte in COOL al primissimo boot.
Se in quel momento `hp_mode` è già COOL, il fancoil potrebbe partire prima che l'handler stagionale lo spenga.

### R-17 — Nessun recovery da bus-off sui nodi ESP32

_Emersa durante il fix di R-07._ `esp32_can` (ESPHome 2026.8.0) non chiama mai `twai_initiate_recovery`. Un nodo ESP32
che va in bus-off non torna sul bus senza un riavvio: riguarda health monitor, An-Penta, An-Quad e il bridge T-2CAN.
Servono un componente esterno, oppure un riavvio automatico in caso di `ERR_CAN_TX_FAIL` persistente.

---

## Cosa va bene

- Monorepo a strati con confini netti (canbus / lighting / climate) e contratti congelati
  (`map.json`, hash del manifest).
- Registry come system of record con artefatti generati, test di idempotenza e gate
  `check_registry_pushed`.
- Protocollo CAN curato: ID a 29 bit, aritmetica wrap-safe su `millis()`, profili single-purpose resi
  irrappresentabili invece che rifiutati.
- Logica pura isolata in header testati nativamente; e2e su piattaforma `host` con `aioesphomeapi`.
- Commissioning gate con default sicuri; restore del boost al riavvio.
- ADR sistematici con alternative; confidence-ledger che dichiara cosa non è verificato; procedura di
  upgrade del fork ethernet.

---

## Registro dei fix

_Le voci vengono aggiunte man mano che i fix sono committati (un branch per issue)._

| Data | Issue | Commit | Sintesi | Verifica |
|------|-------|--------|---------|----------|
| 2026-10-25 | R-02 | PR #67 | vedi la sezione R-02 | vedi la sezione R-02 |
| 2026-10-25 | R-03 | `2aeb15e` | Nomi servizi HA derivati dal `device_name` + test di contratto | test Python ×5, battery nativa PASS |
| 2026-10-25 | R-04 | `ad79881` | Tier HA → NaN su `unavailable` o assenza di HA oltre 5 min | test nativo, `esphome config` ×5, battery PASS; e2e locale 4/4 + CI |
| 2026-10-25 | R-01 | `1472a90` | Uscite PID gated su `hp_mode`, ruoli fancoil, sottotetto riscalda | test nativo, e2e host 20/20, `esphome config` ×5, battery PASS |
| 2026-10-25 | R-01b | `ed4d157` | Domanda pompe = attuazione gated (`is_active`) | test nativi, e2e host 34/34, battery PASS |
| 2026-10-25 | R-10 (parz.) | `bf1aa11` | e2e fancoil-boost in CI/battery; guard porta API in `conftest.py` | e2e host 8/8 ×4; tutti gli e2e climate PASS |
| 2026-10-25 | R-11 | `2f56444`, `633025f` | Drift documentazione, `CHANGELOG.md`, istruzioni Copilot | review diff (docs) |
| 2026-10-25 | R-09 | ADR-0024 | ADR-0024 *Proposed*: fail-safe attuatori (dead-man su alimentazione pompe) | ricerca; verifiche al banco da fare |
| 2026-10-25 | R-07 | `085bb05`, `a2db85c` | Errori TX CAN segnalati (bridge con retry limitato, nodi con `tx_health.h`) | test nativi, battery PASS, `esphome config` ×10 |
| 2026-10-25 | R-06 (parz.) | `50103e2` | Avviso del generatore per ogni binding `toggle` | test Python, battery PASS |
| 2026-10-25 | R-12 | `449be90`, `2763cdf` | Gate HA-tier sulla temperatura esterna | e2e host 4/4, `esphome config`, battery PASS |
| 2026-10-25 | R-08b | `e1d8e68`, `bd32bc6` | Min-fan, soglie e ritardi MEV come numeri locali | e2e host 6/6, `esphome config`, battery PASS |
