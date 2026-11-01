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
| [R-05](#r-05--loverride-del-radiante-scavalca-la-sicurezza-nan) | 🟠 | L'override del radiante scavalca la sicurezza NaN | ✅ | `504300a`, `342cc1c` |
| [R-06](#r-06--doppia-azione-con-binding-toggle) | 🟠 | Doppia azione con binding `toggle` e ACK a 500 ms | 🔧 parziale (timeout ⏸️ dati da banco) | `50103e2` |
| [R-07](#r-07--errori-can-invisibili) | 🟠 | Errori CAN invisibili (bridge TX, `ERR_CAN_*` mai impostati) | ✅ | `085bb05`, `a2db85c` |
| [R-08](#r-08--nan-nei-timer-e-soglie-da-ha) | 🟠 | NaN nei timer e nelle soglie da HA (boost predittivo, MEV) | ✅ | R-08a `0583674`; R-08b `e1d8e68`, `bd32bc6` |
| [R-09](#r-09--fail-safe-hardware-dei-relè) | 🟠 | Nessun fail-safe se il master Modbus si blocca | ⏸️ ADR-0024 *Proposed*: decisione del proprietario | ADR-0024 (`710f088`) |
| [R-10](#r-10--lacune-di-testing) | 🟠 | Lacune di testing e CI | ✅ (resta `assert()` nei test C++) | `2aeb15e`, `ad79881`, `1472a90`, `bf1aa11`, `32b6ea2`, `e2cb259`, `3a0cc0a` |
| [R-11](#r-11--drift-della-documentazione) | 🟡 | Drift della documentazione | ✅ | `1472a90`, `2f56444`, `633025f` |
| [R-12](#r-12--temperatura-esterna-da-ha-congelata) | 🟠 | Temperatura esterna da HA: stesso pattern di R-04 | ✅ | `449be90`, `2763cdf` |
| [R-13](#r-13--windup-dellintegrale-pid) | 🟠 | Windup dell'integrale PID (limiti simmetrici) | ✅ | `dea1047`, `583eb8d` |
| [R-14](#r-14--window-guard-riaccende-un-fancoil-boost) | 🟠 | Il window guard riaccende un fancoil `boost` fuori dal coordinatore | ✅ | `173722e`, `bf1681e` |
| [R-15](#r-15--var-di-radiantyaml-ignorate) | 🟡 | `pwm_period`/`kp`/`ki`/`kd` passati a `radiant.yaml` ignorati | ✅ | `5014afd`, `638342f` |
| [R-16](#r-16--primo-boot-dei-pid-solo-cool) | 🟡 | Al primo boot i PID solo-cool partono in COOL | ✅ | `d509ff3`, `7d28baa` |
| [R-17](#r-17--nessun-recovery-da-bus-off-sui-nodi-esp32) | 🟠 | Nessun recovery da bus-off sui nodi ESP32 (TWAI) | ✅ (recovery diretto ⏸️ fork) | `bef6792` |
| [R-18](#r-18--merge-silenzioso-degli-on_boot-dei-package) | 🟡 | Merge silenzioso degli `on_boot` dei package (priorità perse, hook scartati) | ✅ | `3553901`, `d53e285` |
| [R-19](#r-19--le-pompe-di-circolazione-erano-sempre-accese) | 🔴 | Pompe di circolazione sempre accese (`id(binary_sensor)` è un puntatore) | ✅ | `504300a` |
| [N-01](#n-01--il-minimo-di-rugiada-era-solo-un-setpoint) | 🟠 | Minimo di rugiada solo setpoint, margine 1 °C (doc: 2 °C) | ✅ | `cb70161` |
| [N-02](#n-02--doppio-handler-hp_mode-sulle-zone-radianti) | 🟡 | Doppio handler `hp_mode`: ogni COOL passa da OFF (valvola a 0) | ✅ | `a87b3c3` |
| [N-03](#n-03--setpoint-di-mandata-vecchio-fino-a-30-s) | 🟡 | Setpoint di mandata letto da un template vecchio fino a 30 s | ✅ | `0535bd0` |
| [N-04](#n-04--drift-documentazione-e-dashboard) | 🟡 | Drift: tracker, esempio "nuova stanza", dashboard su entità inesistenti, helper HA obsoleti | ✅ | vedi sezione |

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

**Fix applicato:** ✅ `504300a` (`climate: boost/override no longer bypass sensor loss; pump demand sees held valves (R-05)`)
+ `342cc1c` (collegamento alla battery e documentazione).

- **Boost:**
  - il nuovo binary sensor interno "Boost Sensor Lost" chiude un boost se la temperatura della zona resta NaN,
    senza ritardo anti-ciclo, sulla stessa via dell'override stagionale, con un log WARN. Dopo `7d28baa` (R-16) scatta
    solo se il NaN persiste per `sensor_lost_grace` (default 120 s); la valvola è comunque chiusa fin dal primo
    istante;
  - nessun trigger (temperatura, umidità, predittivo) può avviare un boost con temperatura NaN;
  - dopo un reboot un boost ripristinato sopravvive se la prima lettura arriva entro la tolleranza; altrimenti
    termina (vedi R-16).
- **Override manuale (HA):** decisione presa di **ignorarlo** quando il sensore è perso. È una comodità sopra il loop,
  non un bypass di sicurezza; in raffrescamento anche il dew point dipende da quei sensori.
  - La regola è in `climate/protocol/radiant_override.h` (`final_level`, `holds_open`).
  - Lo stadio finale chiude la valvola con zona NaN. Lo switch resta com'è e l'hold riprende quando torna il sensore.
- **Domanda pompe:** il nuovo `${room}_radiant_override_active` entra nelle somme `*_any_zone_open` di piano terra e
  primo piano, per tutte e 12 le zone radianti. `verify_seasonal_mode_aggregation.py` controlla che ogni zona abbia
  entrambi gli ingressi.
- **Umidità:** la sua perdita durante un boost volutamente *non* lo ferma. Il boost serve anche a deumidificare, e il
  sensore morto è già coperto dal ramo temperatura.
- **Verificato:**
  - nuovo test nativo `test_radiant_override.cpp`;
  - e2e host con preferenze isolate: `test_fancoil_boost.py` e `test_radiant_direction.py` passano (15/15 e 40/40 dopo
    R-08a e R-15);
  - mutation check: disattivando il trigger o lo stop NaN, i nuovi test falliscono.

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
**Fix R-08a:** ✅ `0583674` — `climate: refuse a NaN/non-positive predictive boost delay, clamp a huge one (R-08a)`

- Lo script predittivo si arma solo se `isfinite(minutes) && minutes > 0`; altrimenti logga un WARN e non parte. È stato
  scelto di rifiutare invece di usare un default, per non introdurre una latenza di boost che l'operatore non ha impostato.
- Il ritardo è limitato a `[0, predictive_max_minutes]`, nuova var con default 120, coerente con il range del numero di
  produzione.
- Gli altri ritardi del coordinatore moltiplicano un intero noto a compile time, quindi non serve una protezione.
- I ritardi MEV (`state * 60000`) usano ora numeri locali con range 1–120 min (R-08b): non possono più essere NaN.
- e2e `test_fancoil_boost.py` **15/15** (5 nuovi casi), con preferenze isolate. Ripristinando il codice vecchio, i 5 nuovi
  casi falliscono.

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
- **Seconda tranche:** `32b6ea2`, `e2cb259` (subagente) + `3a0cc0a`.
  - **`climate-e2e`**, un nuovo job CI su **ogni PR e push**, esegue `pytest climate/tests/e2e` (tutti i file, in serie,
    perché ogni harness usa la porta 6053). Gli step e2e per file sono rimossi dal job di compilazione, che resta solo su
    `main`.
  - Nella battery l'e2e diventa un unico step su tutta la directory.
  - **`lint`**, nuovo job su PR e push: `yamllint --strict -c .yamllint .` più `check_repo_hygiene.py`.
    - `.yamllint` è tarato perché il repo attuale passi. Sono disattivate le regole di stile `line-length`,
      `document-start`, `comments`, `comments-indentation`, `braces`, `commas`, `new-line-at-end-of-file`, mentre `truthy`
      è allentata.
    - Nessun errore YAML reale è stato trovato.
  - **`.pre-commit-config.yaml`** esegue yamllint, hygiene e `verification-battery.sh --fast`, una nuova modalità: è
    `--native-only` senza il controllo di idempotenza, quindi funziona anche su un albero modificato, in circa 5 s. Per
    installarlo: `pip install pre-commit && pre-commit install`.
  - **Isolamento delle preferenze host** (`3a0cc0a`): `conftest.py` diceva che una cwd nuova isolava lo stato, ma l'host
    platform salva le preferenze in `$ESPHOME_PREFDIR`, altrimenti in `~/.esphome/prefs/<nome>.prefs`, file condivisi tra
    esecuzioni, checkout e agenti.
    - Lo stato `restore_value` passava da un test all'altro: `test_radiant_direction` falliva 6/34 dopo altre
      esecuzioni, e `test_fancoil_boost` passava solo grazie a un OFF ereditato che mascherava R-16.
    - Ora ogni test usa `ESPHOME_PREFDIR` sulla propria workdir. L'harness boost fissa il PID fancoil a OFF al boot,
      salvo un boost in replay, come nel ruolo `boost`.
  - **Verificato:**
    - yamllint `--strict` OK, battery `--fast` e `--native-only` PASS, workflow con i job
      `native`/`lint`/`esphome-config`/`climate-e2e`/`esphome-compile`;
    - **tutti e 6 gli e2e climate passano con preferenze isolate: 1+4+4+6+34+8.**
  - **Da verificare in CI:** la cache PlatformIO del nuovo job e il primo run reale.
- **Ancora aperto:** `assert()` nudo nei test C++ (minore).
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

**Correzione della premessa:** ESPHome limita già l'integrale a ±1 per default (`pid/climate.py`). Il problema è che il
limite è **simmetrico**: il lato bloccato dal gate accumula fino a un'escursione piena. Inoltre ESPHome integra anche in
OFF, quindi i loop solo-caldo accumulano anche d'estate.

**Fix applicato:** ✅ `dea1047` (`climate: confine PID integral to the active direction (R-13)`) + `583eb8d` (CI, include
dell'harness, documentazione).

- `pid.yaml` rende espliciti i limiti ±`integral_limit` (default 1.0, in unità di uscita perché l'accumulatore include già
  `ki`).
- A ogni cambio di `hp_mode` li restringe con `pid_direction::integral_bounds()`, usando i setter pubblici
  `set_min_integral` / `set_max_integral`:
  - HEAT → `[0, limit]`;
  - COOL → `[-limit, 0]`;
  - SANITARY_ONLY mantiene i limiti precedenti, così una breve fase di sola ACS non cancella l'offset appreso.
- Non c'è un reset esplicito: l'integrale della stagione precedente viene azzerato dal clamp al primo aggiornamento,
  mentre un `hp_mode` ripubblicato identico non tocca un integrale legittimo.
- **Effetto collaterale:** in HEAT l'intenzione `is_cooling` compare solo dopo che l'integrale è sceso a 0 (circa 200 s per
  unità d'errore con ki 0.005). Il tier di domanda del seasonal mode reagisce un po' più tardi.
- **Test:**
  - nuovi test nativi `integral_bounds` in `test_pid_direction.cpp`;
  - nuovo harness host `pid_behaviour.yaml` con guadagni compressi e `test_pid_behaviour.py`: 13/13 a questo stadio;
  - senza il fix 9 casi falliscono.
- **Integrazione:** l'harness non includeva `radiant_override.h`, necessario dopo R-05, e la build host falliva.
  `esphome config` non lo vede.
- **Flake osservato dal subagente:** 3 fallimenti su ~75 esecuzioni in
  `test_legitimate_integral_survives_a_republished_or_idle_mode[HEAT]`, causa ignota, non riprodotto in 80 esecuzioni
  successive.

### R-14 — Window guard riaccende un fancoil boost

`window_guard.yaml` ripristina il modo salvato (COOL) se il PID è OFF a fine recovery. Se un boost è terminato mentre la
finestra era aperta, un fancoil `boost` torna acceso come raffrescatore permanente, scavalcando il coordinatore e il gate.

**Fix applicato:** ✅ `173722e` (`climate: window guard resumes the fancoil via its owner, never a snapshot (R-14)`) + `bf1681e`
(documentazione).

- Il guard non salva più la modalità. Riceve una var obbligatoria `resume_script_id` e, quando la recovery termina con il
  PID ancora OFF, esegue lo script del ruolo `${room_slug}_fancoil_resume_mode`, che ricalcola la modalità:
  - `boost`: COOL solo se il boost è ancora attivo e `hp_mode` è COOL;
  - `cool_only` e `heat_cool`: lo stesso script di sync.
- Un PID avviato da altro durante la recovery resta com'è. Usano il guard solo soggiorno e cucina, entrambi `boost`.
- Nuova var `poll_interval` (default 10 s), che i test comprimono.
- **Compromesso documentato:** un cambio di modalità manuale da HA, fatto prima che la finestra si aprisse, non viene più
  ripristinato.
- **e2e:** `test_pid_behaviour.py` 23/23 in cima allo stack. Senza il fix, i 3 casi "boost finito" (boost fermato, gate
  chiuso, stagione cambiata) ripristinano COOL e falliscono.

### R-15 — Var di radiant.yaml ignorate

`pwm_period`, `kp`, `ki` e `kd` passati a `radiant.yaml` vengono ignorati, perché vincono i `defaults:` di
`heat_only_radiant.yaml`. Oggi il problema è invisibile perché soggiorno e cucina passano i valori di default.

**Fix applicato:** ✅ `5014afd` (`climate: forward pwm_period/kp/ki/kd from radiant.yaml to heat_only_radiant (R-15)`) + `638342f`
(nota in `climate/CLAUDE.md`).

- `radiant.yaml` ripete i 4 default e li inoltra come `vars` all'include annidato. La duplicazione è voluta e commentata
  ("keep in sync"): senza, una var omessa non si risolve.
- **Nessun valore risolto cambia:** la config di climate-control prima e dopo è identica, una volta ordinata.
- **Propagazione verificata** con valori temporanei poi rimossi:
  - `camera_nord` via `radiant.yaml`: prima 0.8 / 60 s, dopo 0.91 / 31 s;
  - `bagno_grande` via `heat_only_radiant.yaml`: valori propagati;
  - una var omessa risolve il default.
- e2e `test_radiant_direction.py` **40/40**, con un nuovo caso sulla taratura, e preferenze isolate.

### R-16 — Primo boot dei PID solo-cool

Un PID con sola `cool_output` (fancoil `boost` e `cool_only`) senza stato salvato parte in COOL al primissimo boot.
Se in quel momento `hp_mode` è già COOL, il fancoil potrebbe partire prima che l'handler stagionale lo spenga.

**Fix applicato:** ✅ `d509ff3` (`climate: deterministic boot mode for fancoil PIDs per role (R-16)`) + `7d28baa` (tolleranza
sul sensore perso, riconciliazione con R-05).

- **Causa reale:** il select `hp_mode` (setup HARDWARE) eseguiva gli handler di ruolo prima del `setup()` del PID (DATA).
  Il restore del PID sovrascriveva poi la modalità impostata dall'handler.
- **Fix:**
  - ogni `fancoil_role_*.yaml` ha uno script `${room_slug}_fancoil_sync_mode`, eseguito dall'`on_value` del select e da
    un `on_boot` **a mappa, a -100**, fuso nello stesso trigger dei replay del coordinatore (vedi R-18);
  - `boost` → OFF, salvo un boost ripristinato come attivo, che resta al replay;
  - `cool_only` → COOL solo con `hp_mode` COOL;
  - `heat_cool` → segue `hp_mode`.
- **Conflitto con R-05 emerso in integrazione:** R-05 chiudeva subito il boost con temperatura NaN, e dopo un reboot la
  temperatura è NaN fino alla prima lettura. Ogni boost ripristinato veniva quindi annullato.
- **Decisione:** tolleranza `sensor_lost_grace` (default 120 s), implementata con un filtro `delayed_on` che si annulla
  quando il sensore torna e non si riarma sui valori ripetuti.
  - È sicuro perché con R-05 la valvola radiante si chiude subito con zona NaN e il PID scrive 0. Lo stato del boost
    decide solo cosa succede quando il sensore torna.
  - Avviare un boost con temperatura NaN resta vietato.
- **Osservazione del subagente, assorbita:** la "season override" del boost leggeva `hp_mode_summer` prima che avesse
  uno stato e poteva chiudere un boost appena ripristinato. Con la tolleranza e il controllo NaN il caso non produce
  attuazioni; resta un possibile irrigidimento futuro (`has_state()`).
- **Test** (e2e con preferenze isolate):
  - `test_pid_behaviour.py` 19/19 a questo stadio: stato al boot per ruolo, replay dopo un restart, restart con e senza
    lettura entro la tolleranza;
  - `test_fancoil_boost.py` 16/16;
  - senza il fix, i tre test sullo stato al boot falliscono.

### R-17 — Nessun recovery da bus-off sui nodi ESP32

_Emersa durante il fix di R-07._ `esp32_can` (ESPHome 2026.8.0) non chiama mai `twai_initiate_recovery`. Un nodo ESP32
che va in bus-off non torna sul bus senza un riavvio: riguarda health monitor, An-Penta, An-Quad e il bridge T-2CAN.
Servono un componente esterno, oppure un riavvio automatico in caso di `ERR_CAN_TX_FAIL` persistente.

**Fix applicato:** ✅ `bef6792` — `canbus: reboot stuck ESP32 TWAI transmitters via a TX watchdog (R-17)`

- **Esposizione reale.** Riguarda solo i nodi ESP32 che **trasmettono**: il bridge T-2CAN (backbone su TWAI), An-Penta e
  An-Quad (heartbeat).
  - Climate controller e health monitor non trasmettono mai. Il bus-off richiede che il contatore degli errori di
    trasmissione superi 255, quindi un nodo che solo riceve arriva al massimo a error-passive.
  - I nodi MCP2515 escono dal bus-off in hardware (128 × 11 bit recessivi).
- **Watchdog** (`canbus/packages/tx_watchdog.yaml` più la logica pura in `tx_health.h`):
  - conta solo gli **heartbeat** consecutivi rifiutati su `can0`, quindi un lato zona MCP2515 morto non riavvia il bridge;
  - alla soglia di 10 heartbeat (5 min) scrive un log ERROR, sincronizza le preferenze e chiama `App.safe_reboot()`;
  - **backoff esponenziale con tetto**: soglie 10 → 20 → 40 → 80, poi fisso. Su un bus davvero morto significa circa un
    riavvio ogni 43 min, mai un loop stretto, e un nodo resta comunque recuperabile dopo la riparazione;
  - il livello di backoff è persistente e si azzera dopo 12 heartbeat accettati di fila, più della profondità della coda
    TWAI, così un bus morto non può fingere il recupero.
- **Dove è collegato:** riga `bridge-t2can` di `PROFILES` e `led_can_actuator.yaml` (An-Penta, An-Quad). Non sui nodi
  MCP2515, dove andrebbe in loop di riavvii.
- **Lighting controller:** solo un contatore diagnostico "CAN TX Refused" sui `CAT_OUTPUT` di fallback, senza watchdog.
  Non ha heartbeat per distinguere un bus-off da un bus inattivo, e un riavvio costa secondi di controllo dei relè.
- **Recovery diretto (⏸️).** `esp32_can` usa il driver v2 (`twai_*_v2`) con un handle protetto in una classe `final`, e non
  chiama mai `twai_initiate_recovery`. Servirebbe un fork in `libs/esphome_overrides/` come per ethernet; lo snippet e i
  passi di verifica sono in `canbus/README.md`, non attivato.
- **Verificato:**
  - `test_tx_health.cpp` esteso: soglie, transitorio che non arriva mai alla soglia, sequenza di riavvii su bus morto,
    prova di recupero;
  - battery nativa PASS, yamllint OK;
  - `esphome config` OK su 9 target, con il watchdog presente solo su T-2CAN, An-Penta e An-Quad.
- **Non verificato:**
  - compilazione ESP32 dei lambda (`App.safe_reboot()`);
  - prova al banco: CANH-CANL in corto per circa 1 s su un An-Penta, poi bus scollegato per un'ora controllando che i
    riavvii si diradino (circa 8, 13, 23, 43 min).

### R-18 — Merge silenzioso degli on_boot dei package

_Emersa durante R-10._ In ESPHome 2026.8.0, quando più package dichiarano `esphome: on_boot:` le regole di merge sono:

- **Forma a mappa:** tutti gli hook diventano **un solo trigger**. Le azioni `then` si concatenano e sopravvive una sola
  `priority`.
  - climate-control: un unico trigger a -100;
  - bridge T-2CAN: il reset dell'MCP2515 a 800, `node_core` a 200 e `bridge` a 190 diventano un trigger a 190.
- **Forma a lista:** le voci (`- priority: …`) si concatenano come trigger separati, come nel lighting controller.
- **Forme miste:** un lato viene **scartato**. Nell'harness boost una lista nel file principale ha fatto sparire l'hook
  -100 del coordinatore.

Oggi l'effetto in produzione è innocuo: sulla T-2CAN il reset precede comunque il setup dell'MCP2515, che è a -100.
Però le priorità dichiarate nei package (e i commenti che le giustificano) non corrispondono a quelle effettive.

**Proposta:** usare ovunque la forma a lista con priorità esplicite e aggiungere un test che controlli il numero e la
priorità dei trigger nelle config risolte.

**Fix applicato:** ✅ `3553901` — `climate: list-form on_boot with explicit priorities everywhere (R-18)`, `d53e285` —
`repo: guard against mapping-form on_boot and merged-trigger drift (R-18)`

- **Forma a lista ovunque.** Ogni `on_boot` è una voce di lista con `priority` esplicita, anche quelle che prima erano
  implicite a 600. Ogni hook diventa un trigger separato alla priorità dichiarata (board, `canbus/packages/`,
  `lighting/packages/`, ruoli fancoil, coordinatore boost, harness).
- **Ordine deterministico del boost.** Il replay del coordinatore boost passa da -100 a -110, quindi gira dopo la
  sincronizzazione del ruolo fancoil (-100) e ha l'ultima parola su un boost ripristinato. Prima i due erano nello stesso
  trigger e l'ordine dipendeva dall'ordine dei package.
- **Commenti corretti** dove giustificavano priorità che non erano quelle effettive, con una nota sui `delay` del reset
  T-2CAN (sono timer dello scheduler).
- **Guardie:**
  - `scripts/check_on_boot_form.py` (solo stdlib) fallisce su qualsiasi YAML tracciato con `on_boot` a mappa o con una
    voce senza `priority`. È nella battery (quindi `--fast`/`--native-only`, pre-commit e job CI `native`);
  - `scripts/check_on_boot_resolved.py` risolve gli entry point con `esphome config` e confronta il numero di trigger per
    priorità con `scripts/on_boot_baseline.json` (battery completa e job CI `esphome-config`; `--update` dopo una
    modifica voluta).
- **Guida aggiornata:** `CLAUDE.md` (Code Style), `canbus/CLAUDE.md`, `climate/CLAUDE.md`. Sostituisce la regola R-16
  "tenere la role sync a mappa a -100".
- **Verificato:**
  - `on_boot` risolti prima → dopo: climate-control 1×(-100) → 4×(-100) + 2×(-110); bridge T-2CAN 1×(190) →
    800/200/190; harness boost 1×(-200) → -110 e -200; harness pid_behaviour 1×(-100) → 4×(-100) + 1×(-110);
  - il controllo di forma fallisce sui file pre-fix (`boards/lilygo-t-2can.yaml` a mappa, `lighting/packages/buttons.yaml`
    senza `priority`); self-test inclusi PASS;
  - dopo il rebase su `main`, sopra R-17: battery nativa PASS, yamllint OK, 15 entry point / 63 trigger uguali alla
    baseline, e2e climate host 94/94 (7 harness).
- **Non verificato:** compilazione ESP32 e ordine di boot sull'hardware (in particolare il reset MCP2515 a 800 sulla
  T-2CAN, ora davvero prima di `node_core`).

### R-19 — Le pompe di circolazione erano sempre accese

_Emersa durante il fix di R-05; risolta in `504300a`._

- **Problema.** Le somme `*_any_zone_open` (`return id(a) || id(b) …`) e i wrapper di `mixing_pump.yaml` e
  `direct_pump.yaml` (`return id(${sensor_id});`) usavano `id(binary_sensor)`. In un lambda quello è il **puntatore**
  al sensore, sempre vero, quindi le pompe di circolazione di tutti i piani risultavano sempre richieste.
- **Fix.** Tutte le espressioni ora leggono `.state`, e `verify_seasonal_mode_aggregation.py` (già nella battery) lo
  impone.
- **Verifica.** Il bug è stato visto nel C++ generato dell'harness. La produzione non si può generare qui (PlatformIO
  bloccato), ma il pattern è identico.

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
| 2026-10-25 | R-10 | `32b6ea2`, `e2cb259`, `3a0cc0a` | e2e host su ogni PR, lint yamllint/hygiene, pre-commit, isolamento preferenze host | yamllint OK, battery PASS, e2e climate 57/57 |
| 2026-10-25 | R-05 + R-19 | `504300a`, `342cc1c` | Sensore perso → boost chiuso e valvola chiusa; domanda pompe con override; pompe non più sempre accese | test nativo, e2e host, verify script |
| 2026-10-25 | R-08a | `0583674` | Ritardo predittivo del boost: NaN/≤0 rifiutato, valori enormi limitati | e2e host 15/15 |
| 2026-10-25 | R-15 | `5014afd`, `638342f` | Le var di `radiant.yaml` arrivano a PID e PWM | config invariata, e2e host 40/40 |
| 2026-10-25 | R-13 | `dea1047`, `583eb8d` | Integrale PID confinato alla direzione attiva (`hp_mode`) | test nativi, e2e host 13/13 |
| 2026-10-25 | R-16 | `d509ff3`, `7d28baa` | Stato al boot dei fancoil per ruolo; tolleranza sul sensore perso (riconcilia R-05) | e2e host 19/19 + 16/16 |
| 2026-10-25 | R-14 | `173722e`, `bf1681e` | Il window guard riconsegna il fancoil al proprietario, senza snapshot | e2e host 23/23 |
| 2026-10-25 | R-17 | `bef6792` | Watchdog TX con backoff per i trasmettitori ESP32 TWAI | test nativi, battery PASS, `esphome config` ×9 |
| 2026-10-26 | R-18 | `3553901`, `d53e285` | `on_boot` a lista con priorità esplicite ovunque; controlli di forma e di trigger risolti | battery PASS, yamllint OK, baseline 15/63, e2e climate host 94/94 |
| 2026-10-30 | N-01 | `cb70161` | Interblocco rugiada sull'uscita cool della miscelatrice; margine 2 °C | test nativo, e2e host 69/69 (mutazione: 2 fail) |
| 2026-10-30 | N-02 | `a87b3c3` | Un solo handler `hp_mode` per zona radiante | e2e host (fallisce sul codice vecchio) |
| 2026-10-30 | N-03 | `0535bd0` | Minimo di mandata ricalcolato prima del setpoint | `esphome config` |
| 2026-10-30 | N-04 | vedi sezione | Tracker, esempio nuova stanza, dashboard, guide helper HA | review diff (docs), yamllint |

---

## Review di follow-up — 2026-10-30

| Campo | Valore |
|-------|--------|
| **Baseline** | `main` @ `7c5accf` |
| **Branch dei fix** | `claude/review-2026-10-30-fixes` (un commit per issue) |

**Metodo.** Battery `--native-only` **20/20 PASS**; `esphome config` (2026.8.0, secrets dummy) sulle **17** configurazioni
della CI: tutte valide. Il registry PlatformIO resta bloccato (HTTP error), ma gli harness host si compilano
**senza PlatformIO**: `esphome compile --only-generate` più g++ diretto sui sorgenti generati, tramite uno shim `esphome` locale
(fuori dal repo) che mette il binario dove `conftest.py` lo cerca. Così gli e2e host sono stati **eseguiti** qui. Il
sorgente PID di ESPHome 2026.8.0 conferma le ipotesi di R-01 e R-13: il cambio di modo non azzera l'integrale e i setter dei limiti
non toccano l'accumulatore.

### N-01 — Il minimo di rugiada era solo un setpoint

- **Problema.** `{floor}_supply_temp_minimum` (rugiada max + margine) era solo il *target* COOL del PID della valvola
  miscelatrice: un overshoot portava la mandata sotto il minimo. Il margine di default era **1.0 °C**, regolabile fino a
  0.5 °C, mentre la documentazione dichiarava +2 °C. Il primo piano raffresca con un **soffitto** radiante.
- **Fix** (`cb70161`). Nuovo `climate/protocol/dew_point_interlock.h`, applicato all'uscita cool della valvola dopo il gate
  `hp_mode`: sotto *minimo − margine/2* (rugiada + margine/2) l'acqua refrigerata viene chiusa e resta chiusa fino a
  quando la mandata torna al minimo. Con supply, minimo o margine NaN l'interblocco blocca. `mixing_pump.yaml` richiede
  `supply_minimum_id` e `safe_margin_id` ed espone `{valve}_dew_point_interlock` (solo in COOL). Margine di default
  **2.0 °C**, minimo impostabile **1.0 °C**.
- **Nota.** Un margine già persistito sul controller viene ripristinato così com'è, quindi va reinserito. Il sistema è pre-live.
- **Verifica.** Test nativo; 3 nuovi e2e host. Con l'interblocco disattivato, i 2 casi COOL falliscono. e2e
  `test_radiant_direction.py` + `test_pid_behaviour.py`: **69/69**.

### N-02 — Doppio handler `hp_mode` sulle zone radianti

- **Problema.** L'handler di `radiant.yaml` non sostituiva quello di `heat_only_radiant.yaml`: ESPHome concatena le liste
  `on_value` estese, quindi venivano eseguiti entrambi, prima OFF e poi COOL. `control(OFF)` scrive 0 sulla valvola fino al
  successivo aggiornamento del PID, e in HA compariva uno stato OFF spurio.
- **Fix** (`a87b3c3`). Ora c'è un solo handler, in `heat_only_radiant.yaml`, con la sostituzione `radiant_cool_capable`, che
  `radiant.yaml` inoltra come `"true"`.
- **Verifica.** Nuovo e2e: ripubblica COOL e controlla che la valvola resti aperta. Fallisce sul codice vecchio.

### N-03 — Setpoint di mandata vecchio fino a 30 s

- **Problema.** L'`on_value` della rugiada massima leggeva `{floor}_supply_temp_minimum.state`, un template ricalcolato solo
  ogni 30 s.
- **Fix** (`0535bd0`). `component.update` del minimo prima di usarlo. Ne beneficia anche l'interblocco di N-01.
- **Verifica.** `esphome config` OK. I floor file di produzione non hanno un harness e2e.

### N-04 — Drift documentazione e dashboard

- Il tracker aveva righe duplicate per R-07 e R-09 e mancavano le righe di R-05 e R-08: corretto.
- In `climate/CLAUDE.md`, l'esempio "Adding a New Room" usava percorsi ormai sbagliati. Ora segue la forma di
  `anticamera.yaml` ed elenca le somme da aggiornare.
- Le dashboard puntavano a sensori `sensor.climate_control_effective_*` che il firmware non pubblica (margini e soglie
  boost): ora puntano ai `number` del controller.
- `QUICK_START.md` e `README.md` delle dashboard facevano creare helper `input_number` per margini e soglie boost, che
  nessuno legge. Ora rimandano ai `number` del controller e a `mev_helpers.yaml`.
