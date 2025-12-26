TODO:
- gestire fancoil per umidità
- margine di sicurezza per dew point regolabile da home assistant
- dividire il fancoil boost tra soggiorno e cucina
- assicurarsi che non ci sia acqua fredda nel circuito radiante prima di spegnere la pompa
- attualmente la temperatura di mandata basata su dew point è calcolata due volte: una per il sensore di minima temperatura di mandata, una per il controllo della valvola miscelatrice. Unificare la logica in un unico punto.
- aggiungere una logica per evitare che durante l'autotune dei radianti il sistema entri in boost mode