import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from streamlit import secrets

# ======== ESTILO VISUAL ========
st.markdown("""
    <style>
    body {
        background-color: #E6E6E6;
    }
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

st.markdown("<h1 style='text-align: center; color: orange;'>🗳️ Sistema de Votação</h1>", unsafe_allow_html=True)

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
        # Recarregar votos atuais
        votos = votos_sheet.get_all_records()
        df_votos = pd.DataFrame(votos) if votos else pd.DataFrame(columns=["Matricula", "Candidato"])

        # Verifica se já votou
        if matricula in df_votos["Matricula"].astype(str).values:
            st.warning("⚠️ Você já votou! Cada matrícula só pode votar uma vez.")
        else:
            try:
                votos_sheet.append_row([matricula, escolha])
                st.success(f"✅ Voto registrado com sucesso para {escolha}!")
            except Exception as e:
                st.error(f"Erro ao registrar voto: {e}")

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
