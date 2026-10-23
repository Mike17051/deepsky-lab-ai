DEEPSKY LAB AI — VERSIONE MIGLIORATA

Funzioni
- Dashboard con statistiche dal NASA Exoplanet Archive.
- Catalogo live dei pianeti confermati con ricerca, filtri, grafici e CSV.
- Laboratorio Kepler / K2 / TESS con download curve di luce via Lightkurve.
- Analisi BLS con periodogramma, curva ripiegata e fino a cinque picchi distinti.
- Controllo preliminare del target nel catalogo NASA.
- Esportazione della curva di luce in CSV e del rapporto in JSON.
- Archivio temporaneo delle analisi salvate nella sessione corrente.

IMPORTANTE
Questa applicazione trova segnali candidati, non conferma esopianeti. Un picco BLS può essere prodotto da rumore, stelle binarie, variabilità stellare o artefatti. L'assenza di una corrispondenza nel catalogo non dimostra una nuova scoperta. I risultati richiedono controlli scientifici indipendenti.

AVVIO LOCALE (Windows)
1. Installa Python 3.11 o 3.12 da https://www.python.org/downloads/ e attiva "Add Python to PATH".
2. Estrai lo ZIP.
3. Apri il Prompt dei comandi nella cartella contenente app.py e requirements.txt.
4. Esegui:
   py -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   streamlit run app.py

AGGIORNARE L'APP GIÀ PUBBLICATA
1. Apri il repository GitHub collegato a Streamlit Community Cloud.
2. Apri app.py, scegli la matita/modifica e sostituisci il contenuto con il nuovo app.py, oppure elimina il vecchio app.py e carica quello nuovo.
3. Sostituisci anche requirements.txt se è cambiato.
4. Conferma con Commit changes. Streamlit dovrebbe ricostruire l'app automaticamente.
5. Se il deploy fallisce, apri Manage app / Logs e controlla il messaggio.

PUBBLICAZIONE
Puoi usare Streamlit Community Cloud collegato a GitHub. Il piano gratuito e la disponibilità possono avere limiti e possono cambiare.

FONTI
NASA Exoplanet Archive: https://exoplanetarchive.ipac.caltech.edu/
MAST: https://mast.stsci.edu/
Lightkurve: https://lightkurve.org/
