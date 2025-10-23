import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
from streamlit import secrets

# ======== ESTILO VISUAL ========
st.markdown("<h1 style='text-align: center; color: orange;'>🗳️ Sistema de Votação</h1>", unsafe_allow_html=True)
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #FF6600;
        color: white;
        font-size: 18px;
        border-radius: 8px;
        height: 50px;
        width: 200px;
    }
    </style>
""", unsafe_allow_html=True)

# ======== AUTENTICAÇÃO GOOGLE SHEETS ========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Nome da planilha
sheet = client.open("vota-o-phayton@firm-mariner-397622.iam.gserviceaccount.com")
candidatos_sheet = sheet.worksheet("Candidatos")
votos_sheet = sheet.worksheet("Votos")

# Ler candidatos
candidatos = candidatos_sheet.col_values(1)

# ======== FORMULÁRIO ========
matricula = st.text_input("Digite sua matrícula:")
escolha = st.radio("Escolha seu candidato:", candidatos)

if st.button("Votar"):
    if not matricula.strip():
        st.error("Por favor, informe sua matrícula.")
    else:
        # 🔄 Recarregar votos atuais da planilha para garantir dados atualizados
        votos = votos_sheet.get_all_records()
        if votos:
            df_votos = pd.DataFrame(votos)
        else:
            df_votos = pd.DataFrame(columns=["Matricula", "Candidato"])

        # Verifica se já votou
        if matricula in df_votos["Matricula"].values:
            st.warning("⚠️ Você já votou! Cada matrícula só pode votar uma vez.")
        else:
            # Adiciona voto
            novo_voto = pd.DataFrame([{"Matricula": matricula, "Candidato": escolha}])
            df_votos = pd.concat([df_votos, novo_voto], ignore_index=True)

            # Tratar NaN
            df_votos = df_votos.replace(np.nan, '')

            # Atualiza planilha
            try:
                votos_sheet.clear()
                votos_sheet.update([df_votos.columns.values.tolist()] + df_votos.values.tolist())
                st.success("✅ Voto registrado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao atualizar a planilha: {e}")

# ======== RESULTADOS ========
st.subheader("📊 Resultados parciais")
votos = votos_sheet.get_all_records()
if votos:
    df_votos = pd.DataFrame(votos)
    contagem = df_votos["Candidato"].value_counts().reset_index()
    contagem.columns = ["Candidato", "Votos"]
    st.dataframe(contagem)
else:
    st.write("Nenhum voto registrado ainda.")
