DEEPSKY LAB AI — AVVIO

Questa è una prima app Streamlit con:
- dashboard iniziale
- catalogo esopianeti aggiornato dalla tabella NASA Exoplanet Archive
- ricerca per nome, metodo e anno
- grafici interattivi ed esportazione CSV
- laboratorio per scaricare curve di luce Kepler/TESS/K2 e cercare periodi con BLS

AVVIO LOCALE (Windows)
1. Installa Python 3.11 o successivo da python.org, selezionando "Add Python to PATH".
2. Apri il Prompt dei comandi nella cartella che contiene app.py e requirements.txt.
3. Esegui: py -m venv .venv
4. Esegui: .venv\\Scripts\\activate
5. Esegui: python -m pip install -r requirements.txt
6. Esegui: streamlit run app.py
7. Si aprirà il browser all'indirizzo locale indicato nel terminale.

DEPLOY GRATUITO
Puoi mettere app.py e requirements.txt in un repository GitHub e collegarlo a Streamlit Community Cloud. La disponibilità gratuita, i limiti e i requisiti dell'account dipendono dal provider e possono cambiare. Non è un servizio garantito 24/7.

IMPORTANTE
- Le prime richieste possono richiedere tempo perché scaricano dati pubblici.
- Il catalogo contiene pianeti noti/confirmati, non candidati nuovi.
- Un periodo BLS è un segnale da verificare, non una scoperta confermata.
