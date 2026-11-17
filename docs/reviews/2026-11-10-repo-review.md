# Review del repository — 2026-11-10

| Campo | Valore |
|-------|--------|
| **Data** | 2026-11-10 (fix del 2026-11-17) |
| **Baseline** | `main` @ `2487999` |
| **Autore** | AI Assistant (Claude Code), su richiesta di Alberto |
| **Scopo** | Review di maturità del progetto e verifica dell'implementazione; seguito di [2026-10-25](2026-10-25-repo-review.md) |

## Metodo

- `scripts/verification-battery.sh --native-only`: 23/23 step PASS sulla baseline.
- `yamllint --strict` e `esphome config` (2026.8.0) sui 19 entry point della CI: tutti validi.
- CI su `main` verde sugli ultimi 5 push (compile ESP32/RP2040 ed e2e inclusi).
- `esphome compile` non eseguibile nell'ambiente della review (PlatformIO non scarica le piattaforme).
  Gli e2e host sono stati eseguiti compilando con `g++` i sorgenti generati da
  `esphome compile --only-generate`.

## Tracker

| ID | Sev. | Titolo | Stato |
|----|------|--------|-------|
| V-01 | 🟠 | Tier "demand" di `seasonal_mode.yaml`: bloccato in SANITARY_ONLY, oscillazione HEAT/COOL, muove `hp_mode` senza che la sorgente lo segua | ✅ |
| V-02 | 🟡 | Il reset di mezza stagione a SANITARY_ONLY scatta solo nel minuto 00:00 del giorno di confine | ⏸️ aperto |
| V-03 | 🟡 | Driver MEV piano terra (`climate/mev_innova_modbus.yaml`) ancora scheletro: registri `TODO(innova-register)`, allarme sempre `false` | ⏸️ serve il manuale Innova |
| V-04 | 🟡 | Residui: provider UDP inutilizzati, commento "log-only" in `bindings.yaml`, profili `led-*` assenti da `registry/README.md` | ✅ |

Restano aperti dalla review precedente: R-09 (ADR-0024 *Proposed*), R-06 (timeout ACK, dati da banco),
R-17 (recovery bus-off diretto).

## V-01 — Tier demand della modalità stagionale

**Problema.** `check_demand` leggeva `any_pid_requesting_heat/cool`, cioè le *azioni* dei PID, e cambiava
`hp_mode` al primo controllo:

1. In SANITARY_ONLY tutti i PID di zona sono in `OFF` (azione `OFF`), quindi la domanda era sempre falsa e
   il tier non poteva più uscire da quella modalità.
2. Con una zona che chiede caldo e una che chiede freddo la catena `if heat && mode != HEAT … else if cool
   && mode != COOL` alternava HEAT e COOL a ogni `check_interval` (1 min). Nessuna conferma, nessun tempo
   minimo, nessuna banda morta: bastava l'overshoot di una stanza.
3. `hp_mode` rispecchia la sorgente e non la comanda, ma il tier partiva appena rilasciato
   `hp_mode_manual_hold`.

**Fix.**

- Nuovi ingressi `any_zone_wants_heat/cool`, somma dei `*_pid_wants_heat/_wants_cool` di
  `pid_sensors.yaml`: temperatura di zona oltre il setpoint di più di `demand_deadband` (1 °C), validi
  anche con il PID in `OFF` (`pid_direction::wants`). `any_pid_requesting_heat/cool` restano come sono per
  dashboard e pannello.
- Regola in `climate/protocol/seasonal_demand.h`: domanda mista o assente = nessun cambio; la domanda da un
  solo lato deve durare `demand_confirm_checks` (15) controlli consecutivi; nessun cambio entro
  `demand_min_dwell_checks` (120) controlli dall'ultimo cambio di `hp_mode`, chiunque l'abbia fatto.
- Nuovo gate `hp_mode_demand_enabled`, default OFF: rilasciando il manual hold gira solo il calendario. Il
  tier demand va acceso solo dove la sorgente segue davvero `hp_mode`.

**Verifica.** `climate/tests/test_seasonal_demand.cpp` e `test_pid_direction.cpp` (nativi);
`climate/tests/e2e/test_seasonal_mode.py` sul nuovo harness `climate/tests/harness/seasonal_mode.yaml`
(coordinatore reale + due zone radianti reali, 13 test); `scripts/verify_seasonal_mode_aggregation.py`
controlla anche le due nuove liste.

## V-04 — Residui

- `devices/climate-control.yaml`: rimossi `udp:` e i 14 provider `packet_transport`, senza consumatori dal
  passaggio al failover CAN → HA.
- `registry/bindings.yaml`: il commento diceva "fallback still log-only"; l'attuazione è reale, mancano
  solo i binding (ADR-0013 open item 4).
- `registry/README.md`: aggiunti i profili `led-penta` e `led-quad`.
- ADR-0019: numero mai assegnato; ora annotato nel `CLAUDE.md` di root.
