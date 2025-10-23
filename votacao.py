import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from streamlit import secrets

# Autenticação com Google Sheets usando Secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Abrir a planilha
sheet = client.open("votacao_candidatos")  # Nome exato da planilha
candidatos_sheet = sheet.worksheet("Candidatos")
votos_sheet = sheet.worksheet("Votos")

# Ler candidatos
candidatos = candidatos_sheet.col_values(1)

st.title("🗳️ Sistema de Votação Online")

# Formulário de votação
escolha = st.radio("Escolha seu candidato:", candidatos)

if st.button("Votar"):
    votos = votos_sheet.get_all_records()
    df_votos = pd.DataFrame(votos)

    if escolha in df_votos["Candidato"].values:
        idx = df_votos[df_votos["Candidato"] == escolha].index[0]
        df_votos.at[idx, "Quantidade"] += 1
    else:
        df_votos = df_votos.append({"Candidato": escolha, "Quantidade": 1}, ignore_index=True)

    votos_sheet.clear()
    votos_sheet.update([df_votos.columns.values.tolist()] + df_votos.values.tolist())

    st.success("✅ Voto registrado com sucesso!")

# Mostrar resultados (carregar sempre)
votos = votos_sheet.get_all_records()
df_votos = pd.DataFrame(votos)

st.subheader("📊 Resultados parciais")
if not df_votos.empty:
    st.dataframe(df_votos)
else:
    st.write("Nenhum voto registrado ainda.")
