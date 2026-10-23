"""DeepSky Lab AI — free exoplanet research dashboard.
Run locally with: streamlit run app.py
This tool identifies possible transit-like signals; it does not confirm discoveries.
"""
from __future__ import annotations
import io
import json
import urllib.parse
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

APP_NAME = "DeepSky Lab AI"
NASA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query="
CATALOG_QUERY = (
    "select pl_name,hostname,discoverymethod,disc_year,pl_orbper,pl_rade,pl_bmasse,"
    "pl_eqt,sy_dist,st_teff,st_rad,st_mass from pscomppars "
    "where pl_name is not null order by disc_year desc"
)

st.set_page_config(page_title=APP_NAME, page_icon="🪐", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.block-container{padding-top:1.5rem;padding-bottom:2.5rem;max-width:1550px}
[data-testid="stSidebar"]{border-right:1px solid rgba(120,130,150,.18)}
.hero{padding:1.35rem 1.55rem;border-radius:18px;background:linear-gradient(115deg,#101b35,#183b62 65%,#256b82);color:#f4f8ff;margin-bottom:1rem}
.hero h1{font-size:2.05rem;margin:0 0 .25rem}.hero p{color:#d2e4f5;margin:0}
.small-muted{color:#738095;font-size:.86rem}
div[data-testid="stMetric"]{background:rgba(120,130,150,.06);padding:13px 15px;border-radius:14px;border:1px solid rgba(120,130,150,.15)}
</style>
<div class="hero"><h1>🪐 DeepSky Lab AI</h1><p>Exoplanet Research Platform · Catalogo NASA, curve di luce e ricerca di segnali candidati</p></div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def load_catalog() -> pd.DataFrame:
    url = NASA_TAP + urllib.parse.quote(CATALOG_QUERY) + "&format=csv"
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content))
    for col in ["disc_year", "pl_orbper", "pl_rade", "pl_bmasse", "pl_eqt", "sy_dist", "st_teff", "st_rad", "st_mass"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def load_lightcurve(target: str, mission: str, cadence: str):
    import lightkurve as lk
    kwargs = {"mission": mission}
    if cadence != "Qualsiasi":
        kwargs["exptime"] = {"Breve": 120, "Lunga": 1800}.get(cadence)
    results = lk.search_lightcurve(target, **kwargs)
    if len(results) == 0:
        return None, "Nessuna curva di luce trovata. Prova un identificativo diverso o un'altra missione.", ""
    # Prefer the first available public product; display its identifier for reproducibility.
    chosen = results[0]
    product_id = str(chosen)
    curve = chosen.download()
    if curve is None:
        return None, "MAST ha restituito una ricerca ma il download non è riuscito.", product_id
    curve = curve.remove_nans().normalize()
    if len(curve.time) < 20:
        return curve, "Sono disponibili meno di 20 punti: il risultato è poco robusto.", product_id
    return curve, None, product_id

def to_float_array(series):
    return np.asarray(series.value if hasattr(series, "value") else series, dtype=float)

def save_analysis(record: dict):
    st.session_state.setdefault("saved_analyses", [])
    st.session_state["saved_analyses"].insert(0, record)
    st.session_state["saved_analyses"] = st.session_state["saved_analyses"][:50]

with st.sidebar:
    st.markdown("### Navigazione")
    page = st.radio("Apri sezione", ["Panoramica", "Catalogo esopianeti", "AI Research Lab", "Analisi salvate", "Metodo e fonti"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Fonti scientifiche**")
    st.caption("NASA Exoplanet Archive · MAST/Lightkurve")
    st.caption("Kepler · K2 · TESS")
    st.caption("Budget software: 0 €")
    st.caption("Il servizio di hosting gratuito può avere limiti.")

if page == "Panoramica":
    st.subheader("Centro di controllo")
    st.write("Esplora i pianeti confermati, analizza curve di luce pubbliche e salva i risultati della sessione.")
    try:
        with st.spinner("Controllo il catalogo NASA…"):
            df = load_catalog()
        years = df["disc_year"].dropna() if "disc_year" in df else pd.Series(dtype=float)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pianeti nel catalogo", f"{len(df):,}")
        c2.metric("Sistemi ospiti", f"{df['hostname'].nunique():,}")
        c3.metric("Anno più recente", str(int(years.max())) if not years.empty else "—")
        c4.metric("Analisi in questa sessione", len(st.session_state.get("saved_analyses", [])))
    except Exception:
        c1, c2, c3 = st.columns(3)
        c1.metric("Catalogo NASA", "Non raggiungibile")
        c2.metric("Motore BLS", "Disponibile")
        c3.metric("Costo software", "€ 0")
        st.info("Il catalogo NASA non risponde in questo momento. Puoi riprovare più tardi.")
    st.markdown("#### Flusso di lavoro")
    a, b, c = st.columns(3)
    a.markdown("##### 1 · Esplora il catalogo")
    a.write("Filtra pianeti confermati e confronta i loro parametri.")
    b.markdown("##### 2 · Analizza una curva")
    b.write("Scarica osservazioni Kepler, K2 o TESS e applica BLS.")
    c.markdown("##### 3 · Verifica il segnale")
    c.write("Confronta i periodi con i pianeti noti e salva un rapporto.")
    st.warning("Un picco BLS è soltanto un segnale candidato. Rumore, stelle binarie, variabilità e artefatti possono imitarne la forma.")

elif page == "Catalogo esopianeti":
    st.subheader("Catalogo esopianeti confermati")
    st.caption("Fonte live: NASA Exoplanet Archive, tabella pscomppars. I dati sono aggiornati dalla fonte, non da DeepSky Lab AI.")
    try:
        with st.spinner("Scarico il catalogo NASA…"):
            df = load_catalog()
        if df.empty:
            st.warning("Il catalogo non ha restituito risultati.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Pianeti caricati", f"{len(df):,}")
            c2.metric("Sistemi stellari", f"{df['hostname'].nunique():,}")
            yrs = df["disc_year"].dropna()
            c3.metric("Ultimo anno disponibile", str(int(yrs.max())) if not yrs.empty else "—")
            f1, f2, f3 = st.columns([1.5, 1.15, 1])
            with f1:
                search = st.text_input("Cerca pianeta o stella", placeholder="Es. Kepler-10")
            with f2:
                methods = sorted(df["discoverymethod"].dropna().astype(str).unique())
                method = st.selectbox("Metodo di scoperta", ["Tutti"] + methods)
            with f3:
                years = df["disc_year"].dropna()
                min_year, max_year = (int(years.min()), int(years.max())) if not years.empty else (1990, datetime.now().year)
                year_range = st.slider("Anno di scoperta", min_year, max_year, (min_year, max_year))
            filtered = df.copy()
            if search.strip():
                q = search.strip().lower()
                filtered = filtered[filtered["pl_name"].astype(str).str.lower().str.contains(q, na=False) | filtered["hostname"].astype(str).str.lower().str.contains(q, na=False)]
            if method != "Tutti":
                filtered = filtered[filtered["discoverymethod"].astype(str) == method]
            filtered = filtered[filtered["disc_year"].between(year_range[0], year_range[1]) | filtered["disc_year"].isna()]
            st.caption(f"Risultati filtrati: {len(filtered):,}. I valori mancanti non equivalgono a zero.")
            labels = {"pl_name":"Pianeta", "hostname":"Stella ospite", "discoverymethod":"Metodo", "disc_year":"Anno", "pl_orbper":"Periodo (giorni)", "pl_rade":"Raggio (R⊕)", "pl_bmasse":"Massa (M⊕)", "pl_eqt":"Temperatura eq. (K)", "sy_dist":"Distanza (pc)"}
            shown = ["pl_name", "hostname", "discoverymethod", "disc_year", "pl_orbper", "pl_rade", "pl_bmasse", "pl_eqt", "sy_dist"]
            st.dataframe(filtered[shown].rename(columns=labels), use_container_width=True, hide_index=True, height=430)
            numeric = [x for x in ["pl_orbper", "pl_rade", "pl_bmasse", "pl_eqt", "sy_dist"] if filtered[x].notna().sum() > 1]
            if numeric:
                gx, gy = st.columns(2)
                xcol = gx.selectbox("Asse X", numeric, index=0)
                ycol = gy.selectbox("Asse Y", numeric, index=min(1, len(numeric)-1))
                plot_df = filtered[["pl_name", xcol, ycol]].dropna().head(3000)
                if not plot_df.empty:
                    fig = px.scatter(plot_df, x=xcol, y=ycol, hover_name="pl_name", log_x=xcol in ["pl_orbper", "sy_dist"], log_y=ycol in ["pl_orbper", "sy_dist"], title="Confronto tra parametri dei pianeti")
                    fig.update_layout(height=430, margin=dict(l=10, r=10, t=55, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            st.download_button("Esporta risultati filtrati (CSV)", filtered.to_csv(index=False).encode("utf-8"), "deepsky_exoplanet_catalog.csv", "text/csv")
    except Exception as exc:
        st.error("Impossibile caricare il catalogo NASA in questo momento.")
        st.caption(f"Dettaglio tecnico: {exc}")
        st.button("Riprova caricando di nuovo", on_click=load_catalog.clear)

elif page == "AI Research Lab":
    st.subheader("AI Research Lab · Ricerca di segnali")
    st.write("Analisi esplorativa di curve di luce pubbliche con Box Least Squares (BLS). Il sistema non usa un modello AI per certificare pianeti.")
    with st.form("research_form"):
        target = st.text_input("Nome della stella o identificativo", value="Kepler-10", help="Esempi: Kepler-10, KIC 11904151, TOI-700")
        c1, c2 = st.columns(2)
        mission = c1.selectbox("Missione", ["Kepler", "TESS", "K2"])
        cadence = c2.selectbox("Cadenza", ["Qualsiasi", "Breve", "Lunga"], help="La disponibilità dipende dai prodotti pubblici della missione.")
        c3, c4 = st.columns(2)
        min_period = c3.number_input("Periodo minimo (giorni)", min_value=0.1, max_value=100.0, value=0.5, step=0.1)
        max_period = c4.number_input("Periodo massimo (giorni)", min_value=0.2, max_value=500.0, value=10.0, step=0.5)
        bins = st.slider("Risoluzione della ricerca", 500, 6000, 2500, step=500, help="Valori più alti richiedono più tempo.")
        run = st.form_submit_button("Scarica dati e avvia analisi", type="primary", use_container_width=True)
    if run:
        if not target.strip():
            st.warning("Inserisci il nome di una stella o un identificativo.")
        elif max_period <= min_period:
            st.warning("Il periodo massimo deve essere maggiore del minimo.")
        else:
            try:
                with st.spinner(f"Cerco osservazioni pubbliche per {target} ({mission})…"):
                    curve, warning, product_id = load_lightcurve(target.strip(), mission, cadence)
                if curve is None:
                    st.warning(warning)
                else:
                    if warning:
                        st.warning(warning)
                    times, flux = to_float_array(curve.time), to_float_array(curve.flux)
                    good = np.isfinite(times) & np.isfinite(flux)
                    times, flux = times[good], flux[good]
                    st.success(f"Curva caricata: {len(times):,} punti validi.")
                    with st.expander("Dettagli osservazione", expanded=True):
                        st.write(f"**Target:** {target.strip()}  ")
                        st.write(f"**Missione:** {mission} · **Prodotto selezionato:** `{product_id}`")
                        st.write(f"**Intervallo temporale:** {times.min():.3f} – {times.max():.3f} giorni (tempo della missione)")
                    lf = go.Figure(go.Scatter(x=times, y=flux, mode="markers", marker=dict(size=3), name="Flusso normalizzato"))
                    lf.update_layout(title="Curva di luce normalizzata", xaxis_title="Tempo della missione (giorni)", yaxis_title="Flusso normalizzato", height=390, margin=dict(l=10, r=10, t=50, b=10))
                    st.plotly_chart(lf, use_container_width=True)
                    if len(times) < 20:
                        st.stop()
                    with st.spinner("Eseguo la ricerca BLS…"):
                        periods = np.linspace(float(min_period), float(max_period), int(bins))
                        pg = curve.to_periodogram(method="bls", period=periods)
                        power = to_float_array(pg.power)
                        pvals = to_float_array(pg.period)
                        finite = np.isfinite(power) & np.isfinite(pvals)
                        if not finite.any():
                            st.error("BLS non ha prodotto valori validi per questo intervallo.")
                            st.stop()
                        # Show separated local peaks rather than treating the single maximum as a discovery.
                        order = np.argsort(power[finite])[::-1]
                        p_good, pow_good = pvals[finite], power[finite]
                        chosen = []
                        for idx in order:
                            p = float(p_good[idx])
                            if all(abs(p - old[0]) / max(old[0], 1e-9) > 0.015 for old in chosen):
                                chosen.append((p, float(pow_good[idx])))
                            if len(chosen) >= 5:
                                break
                        best_period = float(pg.period_at_max_power.value)
                        best_power = float(np.nanmax(power))
                        st.markdown("#### Segnale candidato più forte")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Periodo candidato", f"{best_period:.6f} giorni")
                        m2.metric("Potenza BLS", f"{best_power:.5g}")
                        m3.metric("Punti analizzati", f"{len(times):,}")
                        st.caption("La potenza BLS non è una probabilità che il segnale sia un pianeta e non va interpretata come significatività statistica.")
                        pf = go.Figure(go.Scatter(x=pvals, y=power, mode="lines", name="Potenza BLS"))
                        pf.add_vline(x=best_period, line_dash="dash", annotation_text="Picco massimo")
                        pf.update_layout(title="Periodogramma BLS", xaxis_title="Periodo (giorni)", yaxis_title="Potenza BLS", height=360, margin=dict(l=10, r=10, t=50, b=10))
                        st.plotly_chart(pf, use_container_width=True)
                        peak_df = pd.DataFrame([{"Rank": i+1, "Periodo (giorni)": p, "Potenza BLS": powr} for i, (p, powr) in enumerate(chosen)])
                        st.markdown("#### Picchi distinti da controllare")
                        st.dataframe(peak_df, use_container_width=True, hide_index=True)
                        folded = curve.fold(period=pg.period_at_max_power)
                        ff = go.Figure(go.Scatter(x=to_float_array(folded.phase), y=to_float_array(folded.flux), mode="markers", marker=dict(size=3, opacity=.45), name="Curva ripiegata"))
                        ff.update_layout(title="Curva ripiegata sul periodo candidato", xaxis_title="Fase orbitale", yaxis_title="Flusso normalizzato", height=360, margin=dict(l=10, r=10, t=50, b=10))
                        st.plotly_chart(ff, use_container_width=True)
                        known_note = "Confronto catalogo non disponibile."
                        try:
                            cat = load_catalog()
                            q = target.strip().lower()
                            known = cat[(cat["hostname"].astype(str).str.lower() == q) | (cat["pl_name"].astype(str).str.lower() == q)]
                            if not known.empty:
                                known_note = "Possibili corrispondenze nel catalogo confermato: " + ", ".join(known["pl_name"].astype(str).head(12).tolist())
                            else:
                                known_note = "Nessuna corrispondenza esatta per il testo inserito nel catalogo confermato; questo NON dimostra che il segnale sia un nuovo pianeta."
                        except Exception:
                            pass
                        st.info(known_note)
                        record = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "target": target.strip(), "mission": mission, "cadence": cadence, "product": product_id, "points": int(len(times)), "period_min_days": float(min_period), "period_max_days": float(max_period), "best_period_days": best_period, "best_bls_power": best_power, "top_peaks": chosen, "catalog_check": known_note}
                        # Save automatically so a Streamlit rerun does not lose the result.
                        if st.session_state.get("last_saved_analysis_key") != (target.strip(), mission, product_id, best_period):
                            save_analysis(record)
                            st.session_state["last_saved_analysis_key"] = (target.strip(), mission, product_id, best_period)
                        st.success("Rapporto aggiunto all'archivio della sessione corrente.")
                        report = pd.DataFrame([record])
                        st.download_button("Scarica rapporto analisi (JSON)", json.dumps(record, indent=2, ensure_ascii=False, default=str).encode("utf-8"), file_name=f"deepsky_{target.strip().replace(' ', '_')}_report.json", mime="application/json")
                        st.download_button("Scarica curva di luce usata (CSV)", pd.DataFrame({"time_days": times, "normalized_flux": flux}).to_csv(index=False).encode("utf-8"), file_name=f"deepsky_{target.strip().replace(' ', '_')}_lightcurve.csv", mime="text/csv")
                        st.warning("Prima di interpretare un candidato: controlla altri prodotti e settori, cerca eventi ripetuti, verifica i parametri del transito, confronta cataloghi di falsi positivi e considera conferme indipendenti.")
            except ImportError:
                st.error("Manca Lightkurve o una sua dipendenza. Verifica requirements.txt e riavvia l'app.")
            except Exception as exc:
                st.error("L'analisi non è riuscita. Prova un altro target o intervallo di periodi.")
                st.caption(f"Dettaglio tecnico: {type(exc).__name__}: {exc}")

elif page == "Analisi salvate":
    st.subheader("Analisi salvate")
    saved = st.session_state.get("saved_analyses", [])
    st.caption("Le analisi restano disponibili solo nella sessione attiva del browser; non sono un archivio permanente sul server.")
    if not saved:
        st.info("Non hai ancora salvato analisi in questa sessione. Vai in AI Research Lab e salva un risultato.")
    else:
        st.metric("Analisi salvate nella sessione", len(saved))
        df_saved = pd.DataFrame([{k: v for k, v in row.items() if k not in ["top_peaks"]} for row in saved])
        st.dataframe(df_saved, use_container_width=True, hide_index=True)
        st.download_button("Esporta archivio sessione (JSON)", json.dumps(saved, indent=2, ensure_ascii=False, default=str).encode("utf-8"), file_name="deepsky_saved_analyses.json", mime="application/json")
        if st.button("Svuota archivio di questa sessione"):
            st.session_state["saved_analyses"] = []
            st.rerun()

else:
    st.subheader("Metodo, fonti e limiti")
    st.markdown("""
**Fonti pubbliche**
- **NASA Exoplanet Archive (`pscomppars`)**: catalogo di pianeti confermati e parametri pubblicati.
- **MAST / Lightkurve**: accesso a curve di luce pubbliche delle missioni Kepler, K2 e TESS.

**Metodo di ricerca**
- La ricerca **Box Least Squares (BLS)** cerca periodicità compatibili con cali di flusso simili a transiti.
- Il laboratorio visualizza la curva di luce, il periodogramma, la curva ripiegata e alcuni picchi distinti.
- I rapporti possono essere scaricati in JSON e le curve utilizzate in CSV.

**Cosa non fa**
- Non è un sistema autonomo di scoperta e non certifica esopianeti.
- La potenza BLS non equivale a una probabilità di esistenza del pianeta.
- L'assenza di una corrispondenza esatta nel catalogo non dimostra una scoperta nuova.
- Non sono ancora implementati un calcolo completo di significatività, un modello robusto dei falsi positivi o una conferma indipendente.

**Privacy e costi**
Il nome del target viene usato per interrogare servizi astronomici pubblici. Non inserire dati personali. Il codice e le librerie sono gratuiti; i servizi di hosting gratuiti possono avere limiti o sospendere temporaneamente le app inattive.
""")
    st.caption("DeepSky Lab AI · Versione migliorata · " + datetime.now().strftime("%Y-%m-%d"))
