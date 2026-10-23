"""DeepSky Lab AI — free exoplanet research dashboard prototype.
Run with: streamlit run app.py
"""
from __future__ import annotations
import io
import urllib.parse
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

APP_NAME = "DeepSky Lab AI"
NASA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query="

st.set_page_config(page_title=APP_NAME, page_icon="🪐", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { color-scheme: light; }
.block-container {padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1500px;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(120,130,150,.18);}
.hero {padding: 1.3rem 1.5rem; border-radius: 18px; background: linear-gradient(115deg,#101b35,#183b62 65%,#256b82); color: #f4f8ff; margin-bottom: 1.1rem;}
.hero h1 {font-size: 2.05rem; margin: 0 0 .3rem 0;}
.hero p {color:#d2e4f5; margin:0;}
.metric {border:1px solid rgba(120,130,150,.22); border-radius:14px; padding:1rem 1.1rem;}
.small-muted {color:#738095;font-size:.86rem;}
div[data-testid="stMetric"] {background:rgba(120,130,150,.06); padding:14px 16px; border-radius:14px; border:1px solid rgba(120,130,150,.15);}
</style>
<div class="hero"><h1>🪐 DeepSky Lab AI</h1><p>Exoplanet Research Platform · Catalogo scientifico e laboratorio di analisi</p></div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def load_catalog(limit: int = 5000) -> pd.DataFrame:
    """Download the NASA Exoplanet Archive confirmed-planet table."""
    query = (
        "select pl_name,hostname,discoverymethod,disc_year,pl_orbper,pl_rade,pl_bmasse,"
        "pl_eqt,sy_dist,st_teff,st_rad,st_mass from pscomppars "
        "where pl_name is not null order by disc_year desc"
    )
    url = NASA_TAP + urllib.parse.quote(query) + "&format=csv"
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content))
    return df.head(limit)

@st.cache_data(ttl=3600, show_spinner=False)
def load_lightcurve(target: str, mission: str):
    """Download one available light curve using Lightkurve, imported only on demand."""
    import lightkurve as lk
    result = lk.search_lightcurve(target, mission=mission)
    if len(result) == 0:
        return None, "Nessuna curva di luce trovata per questa combinazione di stella e missione."
    curve = result[0].download()
    if curve is None:
        return None, "Il download della curva di luce non è riuscito. Prova un'altra missione o stella."
    curve = curve.remove_nans().normalize()
    if len(curve.time) < 20:
        return curve, "Sono disponibili pochi punti: i risultati potrebbero essere poco affidabili."
    return curve, None

with st.sidebar:
    st.markdown("### Navigazione")
    page = st.radio("Apri sezione", ["Panoramica", "Catalogo esopianeti", "AI Research Lab", "Informazioni"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Fonti scientifiche**")
    st.caption("NASA Exoplanet Archive · MAST/Lightkurve")
    st.caption("Budget software: 0 €")
    st.caption("Dati aggiornati al momento del caricamento")

if page == "Panoramica":
    st.subheader("Centro di controllo")
    st.write("Consulta i pianeti conosciuti oppure avvia un'analisi esplorativa di una curva di luce.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Aree disponibili", "02", "Catalogo + ricerca")
    c2.metric("Fonti dati", "NASA / MAST", "Pubbliche")
    c3.metric("Costo previsto", "€ 0", "Servizi gratuiti")
    st.markdown("#### Avvio rapido")
    a, b = st.columns(2)
    with a:
        st.markdown("##### 🪐 Catalogo esopianeti")
        st.write("Filtra i pianeti conosciuti per nome, metodo di scoperta e anno.")
        if st.button("Apri il catalogo", use_container_width=True):
            st.session_state["nav_override"] = "Catalogo esopianeti"
            st.info("Scegli 'Catalogo esopianeti' dal menu laterale per aprirlo.")
    with b:
        st.markdown("##### 📈 AI Research Lab")
        st.write("Scarica una curva di luce e cerca periodi compatibili con transiti.")
        if st.button("Apri il laboratorio", use_container_width=True):
            st.info("Scegli 'AI Research Lab' dal menu laterale per aprirlo.")
    st.info("Nota scientifica: un segnale periodico è un candidato da verificare, non una scoperta confermata.")

elif page == "Catalogo esopianeti":
    st.subheader("Catalogo esopianeti")
    st.write("Dati dal NASA Exoplanet Archive, tabella dei pianeti confermati. La prima apertura può richiedere alcuni secondi.")
    try:
        with st.spinner("Scarico il catalogo NASA…"):
            df = load_catalog()
        if df.empty:
            st.warning("Il catalogo non ha restituito risultati.")
        else:
            top1, top2, top3 = st.columns(3)
            top1.metric("Pianeti caricati", f"{len(df):,}")
            top2.metric("Sistemi stellari", f"{df['hostname'].nunique():,}")
            years = pd.to_numeric(df["disc_year"], errors="coerce")
            top3.metric("Anno più recente nei dati", str(int(years.max())) if years.notna().any() else "—")
            f1, f2, f3 = st.columns([1.5,1,1])
            with f1:
                search = st.text_input("Cerca pianeta o stella", placeholder="Es. Kepler-10")
            with f2:
                methods = sorted(df["discoverymethod"].dropna().astype(str).unique())
                method = st.selectbox("Metodo", ["Tutti"] + methods)
            with f3:
                year_vals = pd.to_numeric(df["disc_year"], errors="coerce").dropna()
                min_year = int(year_vals.min()) if not year_vals.empty else 1990
                max_year = int(year_vals.max()) if not year_vals.empty else datetime.now().year
                year_range = st.slider("Anno di scoperta", min_year, max_year, (min_year, max_year))
            filtered = df.copy()
            if search.strip():
                q = search.strip().lower()
                filtered = filtered[filtered["pl_name"].astype(str).str.lower().str.contains(q, na=False) | filtered["hostname"].astype(str).str.lower().str.contains(q, na=False)]
            if method != "Tutti":
                filtered = filtered[filtered["discoverymethod"].astype(str) == method]
            filtered_year = pd.to_numeric(filtered["disc_year"], errors="coerce")
            filtered = filtered[filtered_year.between(year_range[0], year_range[1]) | filtered_year.isna()]
            st.caption(f"Risultati: {len(filtered):,} · I campi vuoti indicano dati non disponibili, non valore zero.")
            shown_cols = ["pl_name","hostname","discoverymethod","disc_year","pl_orbper","pl_rade","pl_bmasse","pl_eqt","sy_dist"]
            labels = {"pl_name":"Pianeta","hostname":"Stella ospite","discoverymethod":"Metodo","disc_year":"Anno","pl_orbper":"Periodo (giorni)","pl_rade":"Raggio (R⊕)","pl_bmasse":"Massa (M⊕)","pl_eqt":"Temp. equilibrio (K)","sy_dist":"Distanza (pc)"}
            st.dataframe(filtered[shown_cols].rename(columns=labels), use_container_width=True, hide_index=True, height=430)
            numeric_cols = [c for c in ["pl_orbper","pl_rade","pl_bmasse","pl_eqt","sy_dist"] if pd.to_numeric(filtered[c], errors="coerce").notna().sum() > 1]
            if numeric_cols:
                x_col = st.selectbox("Asse X del grafico", numeric_cols, index=0)
                y_col = st.selectbox("Asse Y del grafico", numeric_cols, index=min(1, len(numeric_cols)-1))
                plot_df = filtered[["pl_name", x_col, y_col]].copy()
                plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
                plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
                plot_df = plot_df.dropna().head(2500)
                fig = px.scatter(plot_df, x=x_col, y=y_col, hover_name="pl_name", log_x=(x_col in ["pl_orbper","sy_dist"]), log_y=(y_col in ["pl_orbper","sy_dist"]), title="Confronto tra proprietà dei pianeti")
                fig.update_layout(height=450, margin=dict(l=10,r=10,t=55,b=10))
                st.plotly_chart(fig, use_container_width=True)
            st.download_button("Esporta risultati filtrati in CSV", filtered.to_csv(index=False).encode("utf-8"), file_name="deepsky_exoplanet_catalog.csv", mime="text/csv")
    except Exception as exc:
        st.error("Non riesco a caricare il catalogo NASA in questo momento.")
        st.caption(f"Dettaglio tecnico: {exc}")
        st.write("Controlla la connessione e riprova più tardi. Il catalogo richiede accesso a Internet.")

elif page == "AI Research Lab":
    st.subheader("AI Research Lab")
    st.write("Analisi esplorativa di curve di luce pubbliche. Questa versione cerca segnali periodici: non certifica nuovi pianeti.")
    with st.form("research_form"):
        target = st.text_input("Nome della stella o target", value="Kepler-10", help="Esempi: Kepler-10, KIC 11904151, TOI-700")
        mission = st.selectbox("Missione", ["Kepler", "TESS", "K2"])
        min_period = st.number_input("Periodo minimo (giorni)", min_value=0.1, max_value=100.0, value=0.5, step=0.1)
        max_period = st.number_input("Periodo massimo (giorni)", min_value=0.2, max_value=500.0, value=10.0, step=0.5)
        bins = st.slider("Risoluzione ricerca periodi", 500, 6000, 2500, step=500)
        run = st.form_submit_button("Scarica dati e avvia analisi", type="primary", use_container_width=True)
    if run:
        if not target.strip():
            st.warning("Inserisci il nome di una stella o un target.")
        elif max_period <= min_period:
            st.warning("Il periodo massimo deve essere maggiore del minimo.")
        else:
            try:
                with st.spinner(f"Cerco dati pubblici per {target} ({mission})…"):
                    curve, warning = load_lightcurve(target.strip(), mission)
                if curve is None:
                    st.warning(warning)
                else:
                    if warning:
                        st.warning(warning)
                    st.success(f"Curva caricata: {len(curve.time):,} punti disponibili.")
                    st.markdown("##### Curva di luce")
                    light_fig = go.Figure()
                    light_fig.add_trace(go.Scatter(x=np.asarray(curve.time.value), y=np.asarray(curve.flux.value), mode="markers", marker=dict(size=3), name="Flusso normalizzato"))
                    light_fig.update_layout(xaxis_title="Tempo (BJD)", yaxis_title="Flusso normalizzato", height=380, margin=dict(l=10,r=10,t=20,b=10))
                    st.plotly_chart(light_fig, use_container_width=True)
                    with st.spinner("Cerco periodicità compatibili con transiti…"):
                        periods = np.linspace(float(min_period), float(max_period), int(bins))
                        pg = curve.to_periodogram(method="bls", period=periods)
                        best_period = float(pg.period_at_max_power.value)
                        st.metric("Periodo candidato più forte", f"{best_period:.6f} giorni")
                        st.caption("Il picco più forte non prova da solo l'esistenza di un pianeta: può derivare da rumore, binarietà, rotazione stellare o altri fenomeni.")
                        pfig = go.Figure()
                        pfig.add_trace(go.Scatter(x=np.asarray(pg.period.value), y=np.asarray(pg.power.value), mode="lines", name="Potenza BLS"))
                        pfig.add_vline(x=best_period, line_dash="dash", annotation_text="Picco selezionato")
                        pfig.update_layout(xaxis_title="Periodo (giorni)", yaxis_title="Potenza BLS", height=350, margin=dict(l=10,r=10,t=25,b=10))
                        st.plotly_chart(pfig, use_container_width=True)
                        folded = curve.fold(period=pg.period_at_max_power)
                        ff = go.Figure()
                        ff.add_trace(go.Scatter(x=np.asarray(folded.phase.value), y=np.asarray(folded.flux.value), mode="markers", marker=dict(size=3, opacity=.45), name="Curva ripiegata"))
                        ff.update_layout(xaxis_title="Fase orbitale", yaxis_title="Flusso normalizzato", height=350, margin=dict(l=10,r=10,t=25,b=10))
                        st.plotly_chart(ff, use_container_width=True)
                        st.info("Prossima verifica scientifica: controllare altri prodotti/osservazioni, stimare la significatività del segnale e confrontare il target con i cataloghi dei pianeti già noti.")
            except ImportError:
                st.error("Manca Lightkurve. Installa le dipendenze con: pip install -r requirements.txt")
            except Exception as exc:
                st.error("L'analisi non è riuscita. Prova un altro target o un intervallo di periodi diverso.")
                st.caption(f"Dettaglio tecnico: {exc}")

else:
    st.subheader("Informazioni sul progetto")
    st.markdown("""
**DeepSky Lab AI** è un progetto didattico di analisi astronomica basato su fonti pubbliche.

- **Catalogo:** NASA Exoplanet Archive, tabella `pscomppars`.
- **Curve di luce:** missioni Kepler, K2 e TESS attraverso MAST/Lightkurve.
- **Metodo iniziale:** Box Least Squares (BLS), utile per individuare periodicità compatibili con transiti.
- **Limiti:** il software produce segnali candidati, non conferme. La validazione richiede controlli indipendenti, valutazione dei falsi positivi e spesso osservazioni aggiuntive.
- **Costi:** il codice usa librerie open source e dati pubblici; hosting gratuito e disponibilità possono avere limiti.

**Privacy:** il nome del target viene usato per interrogare le fonti astronomiche pubbliche. Non inserire informazioni personali.
""")
    st.caption("Versione prototipo · " + datetime.now().strftime("%Y-%m-%d"))
