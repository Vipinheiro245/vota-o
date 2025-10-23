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

# Abrir a planilha (mantendo o nome que você indicou)
sheet = client.open("vota-o-phayton@firm-mariner-397622.iam.gserviceaccount.com")
candidatos_sheet = sheet.worksheet("Candidatos")
votos_sheet = sheet.worksheet("Votos")

# Ler candidatos
candidatos = candidatos_sheet.col_values(1)

st.title("🗳️ Sistema de Votação Online")

# Carregar votos existentes
votos = votos_sheet.get_all_records()
if votos:
    df_votos = pd.DataFrame(votos)
else:
    df_votos = pd.DataFrame(columns=["Candidato", "Quantidade"])

# Formulário de votação
escolha = st.radio("Escolha seu candidato:", candidatos)

if st.button("Votar"):
    if "Candidato" not in df_votos.columns:
        df_votos = pd.DataFrame(columns=["Candidatos", "Quantidade"])

    if escolha in df_votos["Candidatos"].values:
        idx = df_votos[df_votos["Candidatos"] == escolha].index[0]
        df_votos.at[idx, "Quantidade"] = int(df_votos.at[idx, "Quantidade"]) + 1
    else:
        df_votos = pd.concat([df_votos, pd.DataFrame([{"Candidato": escolha, "Quantidade": 1}])], ignore_index=True)

    # Atualizar planilha
    votos_sheet.clear()
    votos_sheet.update([df_votos.columns.values.tolist()] + df_votos.values.tolist())

    st.success("✅ Voto registrado com sucesso!")

# Mostrar resultados
st.subheader("📊 Resultados parciais")
if not df_votos.empty:
    st.dataframe(df_votos)
else:
    st.write("Nenhum voto registrado ainda.")
