# Review del repository — 2026-10-25

| Campo | Valore |
|-------|--------|
| **Data** | 2026-10-25 |
| **Baseline** | `main` @ `9d0bc28` (Upgrade ESPHome to 2026.8.0, ADR-0022) |
| **Branch dei fix** | `claude/repo-review-fixes` |
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
| [R-02](#r-02--i-controller-si-riavviano-ogni-15-minuti-senza-home-assistant) | 🔴 | I controller si riavviano ogni 15 min senza Home Assistant | ✅ | `5b53b0d` |
| [R-03](#r-03--lilluminazione-non-raggiunge-mai-home-assistant) | 🔴 | Nomi dei servizi HA errati: l'illuminazione non raggiunge mai HA | ✅ | `2aeb15e` |
| [R-04](#r-04--il-tier-ha-del-failover-non-diventa-mai-nan) | 🔴 | Il tier HA del failover non diventa mai NaN (valori congelati) | ✅ | `ad79881` |
| [R-05](#r-05--loverride-del-radiante-scavalca-la-sicurezza-nan) | 🟠 | L'override del radiante scavalca la sicurezza NaN; boost bloccato | ⬜ | — |
| [R-06](#r-06--doppia-azione-con-binding-toggle) | 🟠 | Doppia azione con binding `toggle` e ACK a 500 ms | ⬜ | — |
| [R-07](#r-07--errori-can-invisibili) | 🟠 | Errori CAN invisibili (bridge TX, `ERR_CAN_*` mai impostati) | ⬜ | — |
| [R-08](#r-08--nan-nei-timer-e-soglie-da-ha) | 🟠 | NaN nei timer (`predictive_minutes`) e min-fan MEV da HA | ⬜ | — |
| [R-09](#r-09--fail-safe-hardware-dei-relè) | 🟠 | Nessun fail-safe se il master Modbus si blocca | ⬜ | — |
| [R-10](#r-10--lacune-di-testing) | 🟠 | Lacune di testing e CI | 🔧 parziale | `2aeb15e`, `ad79881`, `1472a90`, `bf1aa11` |
| [R-11](#r-11--drift-della-documentazione) | 🟡 | Drift della documentazione | 🔧 parziale | `1472a90` (sezione PID) |
| [R-12](#r-12--temperatura-esterna-da-ha-congelata) | 🟠 | Temperatura esterna da HA: stesso pattern di R-04 | ⬜ | — |
| [R-13](#r-13--windup-dellintegrale-pid) | 🟠 | Windup dell'integrale PID (nessun `min/max_integral`) | ⬜ | — |
| [R-14](#r-14--window-guard-riaccende-un-fancoil-boost) | 🟠 | Il window guard riaccende un fancoil `boost` fuori dal coordinatore | ⬜ | — |
| [R-15](#r-15--var-di-radiantyaml-ignorate) | 🟡 | `pwm_period`/`kp`/`ki`/`kd` passati a `radiant.yaml` ignorati | ⬜ | — |
| [R-16](#r-16--primo-boot-dei-pid-solo-cool) | 🟡 | Al primo boot i PID solo-cool partono in COOL | ⬜ | — |

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

**Correzione prevista.** `api: reboot_timeout: 0s` sui tre controller; `wifi: reboot_timeout: 0s` sulle
board dual-interface (Ethernet primaria).

**Fix applicato:** ✅ `5b53b0d` — `boards: disable API/WiFi reboot timeouts on autonomous controllers (R-02)`

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
- **Da verificare su hardware al bring-up:** controller acceso per più di 15 min con HA spento e con l'AP spento.
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
  4. controllare che `binary_sensor.light_controller_ha_ready` diventi `on` entro circa 5 s.

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
    numerico → tier "HA", `unavailable` → Emergency, disconnessione breve → resta "HA", disconnessione oltre la grazia → NaN.
  - Aggiunti al job CI su `main` e alla battery completa; l'harness è aggiunto anche al gate `esphome config` della CI.
- **Verificato:**
  - battery nativa PASS in un worktree isolato sul commit;
  - `esphome config` OK su climate-control, sui due harness climate, su light-controller e health-monitor;
  - l'API scelta esiste in 2026.8.0.
- **Non verificato qui** (PlatformIO bloccato): la compilazione ESP32 per il device.
- **e2e eseguito in seguito** su un binario host costruito localmente (`esphome compile --only-generate` + g++):
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

### R-07 — Errori CAN invisibili

Il bridge ignora il ritorno di `send_data` (`canbus/packages/bridge.yaml:135,138`): un frame fallito
viene contato come "forwarded". `ERR_CAN_TX_FAIL` / `ERR_CAN_BUS_OFF` non vengono mai impostati da
alcun firmware: la classe di alert "node_error" funziona solo per l'overflow del bridge.

### R-08 — NaN nei timer e soglie da HA

`delay: predictive_minutes * 60000` con NaN ⇒ ritardo indefinito (probabile boost immediato). La
velocità minima MEV arriva ancora da HA (`homeassistant` sensor), mentre le soglie di sicurezza sono
già state rese locali.

### R-09 — Fail-safe hardware dei relè

Se il master si blocca, i relè Modbus mantengono l'ultimo stato (valvole/pompe accese). Valutare un
watchdog o un timeout lato scheda relè.

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
  - compile ed e2e solo su push a `main`, non sulle PR;
  - `assert()` nudo nei test C++;
  - nessun pre-commit né yamllint.

### R-11 — Drift della documentazione

- ~~`climate/CLAUDE.md:99` descrive un "Dual PID Pattern" che il codice non implementa.~~ Sostituito in `1472a90` (R-01).
- Range di tuning fancoil (Kp 1.0–2.0) incoerenti con il default 0.2 di `fancoil.yaml`.
- `CLAUDE.md` radice: versione 1.17 nell'intestazione vs changelog fino a 1.19; indice ADR fermo a
  0017/0019 mentre esistono fino a 0023 (0019 assente).
- Changelog molto lungo dentro `CLAUDE.md`: meglio un `CHANGELOG.md` separato.

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

_Le voci vengono aggiunte man mano che i fix sono committati sul branch `claude/repo-review-fixes`._

| Data | Issue | Commit | Sintesi | Verifica |
|------|-------|--------|---------|----------|
| 2026-10-25 | R-02 | `5b53b0d` | `api`/`wifi` `reboot_timeout: 0s` sui controller autonomi | `esphome config` ×5; hardware da fare al bring-up |
| 2026-10-25 | R-03 | `2aeb15e` | Nomi servizi HA derivati dal `device_name` + test di contratto | test Python ×4, battery nativa PASS |
| 2026-10-25 | R-04 | `ad79881` | Tier HA → NaN su `unavailable` o assenza di HA oltre 5 min | test nativo, `esphome config` ×5, battery PASS; e2e in CI |
| 2026-10-25 | R-01 | `1472a90` | Uscite PID gated su `hp_mode`, ruoli fancoil, sottotetto riscalda | test nativo, e2e host 20/20, `esphome config` ×5, battery PASS |
| 2026-10-25 | R-01b | `ed4d157` | Domanda pompe = attuazione gated (`is_active`) | test nativi, e2e host 34/34, battery PASS |
| 2026-10-25 | R-10 (parz.) | `bf1aa11` | e2e fancoil-boost in CI/battery; guard porta API in `conftest.py` | e2e host 8/8 ×4; tutti gli e2e climate PASS |
