TODO:
- Gestione della temperatura di mandata in base alla temperatura esterna e alle condizioni interne
- - Integrazione con sensore di temperatura esterna
- - Algoritmo di regolazione della temperatura di mandata in base alla temperatura esterna
- - Considerazione delle condizioni interne (umidità, occupazione) per ottimizzare il comfort

- Gestione della temperatura della pompa di calore

- Integrazione con sistemi di accumulo di energia elettrica (batterie domestiche)
- - Gestione intelligente dell'energia accumulata per riscaldamento e raffreddamento
- - Ottimizzazione dei tempi di carica/scarica in base alle previsioni di consumo e produzione energetica

- Recupero bus-off TWAI sul posto (invece del riavvio del watchdog TX): fork locale di esp32_can con twai_get_status_info_v2 + twai_initiate_recovery_v2, da verificare sull'IDF pinnato

Idee:
- Algoritmi di apprendimento per la regolazione (oggi assenti)
- Previsioni meteo come nei termostati commerciali
- Consapevolezza dell'energia (fotovoltaico, tariffe)
- Sensori ESP32 per rilevare la presenza

DONE:
- dividire il fancoil boost tra soggiorno e cucina
- gestire fancoil per umidità
- margine di sicurezza per dew point regolabile da home assistant
- attualmente la temperatura di mandata basata su dew point è calcolata due volte: una per il sensore di minima temperatura di mandata, una per il controllo della valvola miscelatrice. Unificare la logica in un unico punto.
- aggiungere una logica per evitare che durante l'autotune dei radianti il sistema entri in boost mode
- Gestione VMC (MEV)
- - Integrazione con sensori di qualità dell'aria (CO2, VOC, PM2.5)
- - Logica di controllo della VMC basata sulla qualità dell'aria interna
- - Coordinamento tra riscaldamento/raffreddamento e VMC per ottimizzare il comfort e l'efficienza energetica
- - Calcolo rateo umidità e state machine 3-stati su ESPHome
