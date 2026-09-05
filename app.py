import streamlit as st
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Magazzino Officina", layout="wide")

if os.path.exists("magazzino.csv"):
    df = pd.read_csv("magazzino.csv")
else:
    df = pd.DataFrame(columns=["Codice", "Articolo", "Quantita", "Scorta_Minima", "Targa", "Data"])

df.columns = df.columns.str.strip()

menu = st.sidebar.selectbox("Menu", [
    "Cerca articolo",
    "Giacenza in magazzino", 
    "Aggiungi Articolo", 
    "Modifica / Elimina Articoli", 
    "Installa su Veicolo (Storico)", 
    "Storico Veicolo", 
    "Scansione Codice a Barre"
])

col_qta = "Quantita" if "Quantita" in df.columns else "Quantità"
col_min = "Scorta_Minima" if "Scorta_Minima" in df.columns else "Minimo"

if menu == "Cerca articolo":
    st.title("Magazzino Officina")
    st.subheader("Cerca Articolo")
    search_query = st.text_input("Inserisci il nome o il codice dell'articolo:").strip().lower()
    if search_query:
        if not df.empty:
            df_grouped = df.groupby(["Codice", "Articolo"], as_index=False).agg({
                col_qta: "sum", col_min: "min", "Targa": "first", "Data": "max"
            })
            df_filtered = df_grouped[
                df_grouped["Articolo"].astype(str).str.lower().str.contains(search_query) | 
                df_grouped["Codice"].astype(str).str.lower().str.contains(search_query)
            ]
            if not df_filtered.empty:
                st.success(f"Trovati {len(df_filtered)} risultati:")
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.warning("Nessun articolo trovato con questo nome o codice.")
        else:
            st.info("Il magazzino è vuoto.")

elif menu == "Giacenza in magazzino":
    st.title("Magazzino Officina")
    st.subheader("Giacenza Attuale del Magazzino")
    if not df.empty:
        df_grouped = df.groupby(["Codice", "Articolo"], as_index=False).agg({
            col_qta: "sum", col_min: "min", "Targa": "first", "Data": "max"
        })
        st.dataframe(df_grouped, use_container_width=True)
        st.write("---")
        st.subheader("⚠️ Avvisi Prodotti in Esaurimento")
        prodotti_bassi = df_grouped[df_grouped[col_qta] <= df_grouped[col_min]]
        if not prodotti_bassi.empty:
            for _, row in prodotti_bassi.iterrows():
                st.warning(f"Attenzione: Il prodotto {row.get('Articolo')} (Codice: {row.get('Codice')}) è in esaurimento! Rimasti: {row.get(col_qta)} pezzi.")
        else:
            st.success("Tutti i prodotti hanno una giacenza sufficiente.")
    else:
        st.info("Nessun articolo presente nel magazzino.")

elif menu == "Aggiungi Articolo":
    st.title("Magazzino Officina")
    st.subheader("Aggiungi o Carica Articolo")
    codice_input = st.text_input("Scansiona o inserisci il Codice Articolo (Barcode):").strip()
    articolo_esistente = ""
    scorta_minima_val = 2
    targa_val = "MAGAZZINO"
    if codice_input and not df.empty:
        match = df[df["Codice"].astype(str) == str(codice_input)]
        if not match.empty:
            articolo_esistente = match.iloc[0]["Articolo"]
            if col_min in match.columns:
                scorta_minima_val = int(match.iloc[0][col_min])
            st.success(f"Articolo trovato nel sistema: **{articolo_esistente}**")
        else:
            st.info("Nuovo articolo! Inserisci il nome dell'articolo qui sotto.")

    with st.form("form_aggiungi"):
        if articolo_esistente:
            articolo_input = articolo_esistente
            st.write(f"**Articolo:** {articolo_input}")
        else:
            articolo_input = st.text_input("Nome del Nuovo Articolo:").strip()
        qta_input = st.number_input("Quantità da aggiungere:", min_value=1, value=1)
        scorta_input = st.number_input("Scorta Minima:", min_value=0, value=scorta_minima_val)
        targa_input = st.text_input("Targa (opzionale):", value=targa_val).strip().upper()
        submitted = st.form_submit_button("Registra Carico")
        if submitted:
            if codice_input and articolo_input:
                data_oggi = datetime.now().strftime("%Y-%m-%d")
                nuovo_movimento = pd.DataFrame([{
                    "Codice": str(codice_input), "Articolo": str(articolo_input),
                    "Quantita": int(qta_input), "Scorta_Minima": int(scorta_input),
                    "Targa": str(targa_input), "Data": data_oggi
                }])
                df_updated = pd.concat([df, nuovo_movimento], ignore_index=True)
                df_updated.to_csv("magazzino.csv", index=False)
                st.success(f"Aggiunti con successo {qta_input} pezzi per '{articolo_input}'!")
                st.rerun()
            else:
                st.warning("Compila sia il codice che il nome dell'articolo.")

elif menu == "Modifica / Elimina Articoli":
    st.title("Magazzino Officina")
    st.subheader("Modifica o Elimina Articoli")
    if not df.empty:
        riga_selezionata = st.selectbox("Seleziona la riga da modificare/eliminare:", df.index.tolist())
        row = df.loc[riga_selezionata]
        with st.form("form_modifica"):
            c_code = st.text_input("Codice", value=str(row.get("Codice", "")))
            c_art = st.text_input("Articolo", value=str(row.get("Articolo", "")))
            c_qta = st.number_input("Quantità", value=int(row.get(col_qta, 1)))
            c_min = st.number_input("Scorta Minima", value=int(row.get(col_min, 2)))
            c_targa = st.text_input("Targa", value=str(row.get("Targa", "")))
            salva = st.form_submit_button("Salva Modifiche")
            elimina = st.form_submit_button("Elimina Riga")
            if salva:
                df.loc[riga_selezionata, "Codice"] = c_code
                df.loc[riga_selezionata, "Articolo"] = c_art
                df.loc[riga_selezionata, col_qta] = c_qta
                df.loc[riga_selezionata, col_min] = c_min
                df.loc[riga_selezionata, "Targa"] = c_targa
                df.to_csv("magazzino.csv", index=False)
                st.success("Modifiche salvate!")
                st.rerun()
            if elimina:
                df = df.drop(index=riga_selezionata)
                df.to_csv("magazzino.csv", index=False)
                st.success("Riga eliminata!")
                st.rerun()
    else:
        st.info("Nessun dato disponibile.")

elif menu == "Installa su Veicolo (Storico)":
    st.title("Magazzino Officina")
    st.subheader("Installa Ricambio su Veicolo")
    
    if "inst_targa" not in st.session_state:
        st.session_state.inst_targa = ""
    if "inst_codice" not in st.session_state:
        st.session_state.inst_codice = ""
    if "inst_articolo" not in st.session_state:
        st.session_state.inst_articolo = ""

    targa_inst = st.text_input("Targa del Veicolo:", value=st.session_state.inst_targa).strip().upper()
    if targa_inst != st.session_state.inst_targa:
        st.session_state.inst_targa = targa_inst

    col1, col2 = st.columns(2)
    with col1:
        cod_input = st.text_input("Codice a Barre / Codice Ricambio:", value=st.session_state.inst_codice).strip()
    with col2:
        art_input = st.text_input("Nome Articolo (Cerca per nome):", value=st.session_state.inst_articolo).strip()

    min_val = 2
    cod_finale = ""
    nome_finale = ""

    if not df.empty:
        if cod_input and cod_input != st.session_state.get("inst_codice_prev", ""):
            match = df[df["Codice"].astype(str) == str(cod_input)]
            if not match.empty:
                st.session_state.inst_articolo = match.iloc[0]["Articolo"]
                st.session_state.inst_codice = cod_input
                st.session_state.inst_codice_prev = cod_input
                st.rerun()

        if art_input and art_input != st.session_state.get("inst_articolo_prev", ""):
            match = df[df["Articolo"].astype(str).str.lower().str.contains(art_input.lower())]
            if not match.empty:
                st.session_state.inst_codice = str(match.iloc[0]["Codice"])
                st.session_state.inst_articolo = art_input
                st.session_state.inst_articolo_prev = art_input
                st.rerun()

    cod_finale = st.session_state.inst_codice if st.session_state.inst_codice else cod_input
    nome_finale = st.session_state.inst_articolo if st.session_state.inst_articolo else art_input

    if cod_finale and not df.empty:
        match_min = df[df["Codice"].astype(str) == str(cod_finale)]
        if not match_min.empty and col_min in match_min.columns:
            min_val = int(match_min.iloc[0][col_min])

    with st.form("form_installa"):
        qta_inst = st.number_input("Quantità da scaricare:", min_value=1, value=1)
        installa_btn = st.form_submit_button("Registra Installazione (Scarico)")
        
        if installa_btn:
            if cod_finale and targa_inst and nome_finale:
                data_oggi = datetime.now().strftime("%Y-%m-%d")
                scarico_df = pd.DataFrame([{
                    "Codice": str(cod_finale), "Articolo": str(nome_finale),
                    "Quantita": -int(qta_inst), "Scorta_Minima": int(min_val),
                    "Targa": str(targa_inst), "Data": data_oggi
                }])
                df_updated = pd.concat([df, scarico_df], ignore_index=True)
                df_updated.to_csv("magazzino.csv", index=False)
                
                st.session_state.inst_targa = ""
                st.session_state.inst_codice = ""
                st.session_state.inst_articolo = ""
                st.session_state.inst_codice_prev = ""
                st.session_state.inst_articolo_prev = ""
                
                st.success(f"Scaricati {qta_inst} pezzi di '{nome_finale}' per la targa {targa_inst}!")
                st.rerun()
            else:
                st.warning("Compila la targa e assicurati che l'articolo/codice esista in magazzino.")

elif menu == "Storico Veicolo":
    st.title("Magazzino Officina")
    st.subheader("Storico Veicolo")
    targa_query = st.text_input("Inserisci la targa del veicolo:").strip().upper()
    
    if targa_query:
        if not df.empty and "Targa" in df.columns:
            df_targa = df[df["Targa"].astype(str).str.upper() == targa_query]
            if not df_targa.empty:
                # Group and drop Scorta_Minima from display
                df_targa_grouped = df_targa.groupby(["Codice", "Articolo"], as_index=False).agg({
                    col_qta: "sum", "Targa": "first", "Data": "max"
                })
                st.success(f"Trovati movimenti per la targa: {targa_query}")
                st.dataframe(df_targa_grouped, use_container_width=True)
                
                with st.expander("⚙️ Gestione Eliminazione (Modifica Storico)"):
                    tipo_eliminazione = st.radio(
                        "Scegli l'operazione di eliminazione:", 
                        ["Elimina articolo specifico", "Elimina intero veicolo (tutta la targa)"]
                    )
                    
                    if tipo_eliminazione == "Elimina articolo specifico":
                        opzioni_articoli = []
                        for idx, row in df_targa.iterrows():
                            art_nome = row.get("Articolo", "Sconosciuto")
                            art_cod = row.get("Codice", "")
                            art_qta = row.get(col_qta, 0)
                            data_mov = row.get("Data", "")
                            opzioni_articoli.append(f"ID {idx}: {art_nome} (Cod: {art_cod}) - Qta: {art_qta} - Data: {data_mov}")
                        
                        scelta_art = st.selectbox("Seleziona l'articolo da eliminare:", opzioni_articoli)
                        if st.button("Conferma Eliminazione Articolo"):
                            idx_da_eliminare = int(scelta_art.split("ID ")[1].split(":")[0])
                            df_updated = df.drop(index=idx_da_eliminare)
                            df_updated.to_csv("magazzino.csv", index=False)
                            st.success("Articolo eliminato con successo dallo storico del veicolo!")
                            st.rerun()
                    else:
                        if st.button("Conferma Eliminazione Intero Veicolo"):
                            df_updated = df[df["Targa"].astype(str).str.upper() != targa_query]
                            df_updated.to_csv("magazzino.csv", index=False)
                            st.success(f"Storico completo per la targa {targa_query} eliminato con successo!")
                            st.rerun()
            else:
                st.warning("Nessun movimento trovato per questa targa.")
        else:
            st.info("Il magazzino è vuoto o colonna Targa non trovata.")

elif menu == "Scansione Codice a Barre":
    st.title("Magazzino Officina")
    st.subheader("Scansione Rapida Codice a Barre")
    scanned = st.text_input("Usa lo scanner per leggere il codice:")
    if scanned:
        st.write(f"Hai scansionato il codice: {scanned}")
