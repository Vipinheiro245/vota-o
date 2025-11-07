import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import base64
from streamlit import secrets

# ======== FUNÇÃO DE FUNDO ========
def set_background(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: contain;
        background-position: center top;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-color: #f0f0f0;
        min-height: 100vh;
    }}
    [data-testid="stHeader"] {{
        background: rgba(0, 0, 0, 0);
    }}
    .block-container {{
        max-width: 900px;
        margin: auto;
        padding: 40px;
        margin-top: 100px;
        background-color: rgba(255, 255, 255, 0.92);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    div.stButton > button:first-child {{
        background-color: #FF6600;
        color: white;
        font-size: 18px;
        border-radius: 8px;
        height: 50px;
        width: 200px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    div.stButton > button:first-child:hover {{
        background-color: #FF7700;
        transform: scale(1.05);
    }}
    div[data-testid="stTextInput"] label p,
    div[data-testid="stRadio"] > label p {{
        font-size: 22px !important;
        font-weight: normal !important;
        color: #333 !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ======== TELA ========
set_background("polimeros.png")
st.markdown("<h1 style='text-align: center; color: #FF6900; font-size: 40px;'>SISTEMA DE VOTAÇÃO</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size: 20px; color: #333; margin-top: 10px;'>Bem-vindo ao Sistema de Votação - Café com Gestor.</div>", unsafe_allow_html=True)
st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ======== CONEXÃO COM GOOGLE SHEETS ========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Nome do arquivo (ajuste se necessário)
sheet = client.open("vota-o-phayton@firm-mariner-397622.iam.gserviceaccount.com")

# Abas
candidatos_sheet = sheet.worksheet("Candidatos")
votos_sheet = sheet.worksheet("Votos")

# ======== INTERFACE ========
candidatos = candidatos_sheet.col_values(1)
matricula = st.text_input("Digite sua matrícula:")
escolha = st.radio("Escolha seu candidato:", candidatos)

# ======== LÓGICA DE VOTO ========
if st.button("Votar"):
    if not matricula.strip():
        st.error("⚠️ Por favor, informe sua matrícula antes de votar.")
    else:
        # Lê todos os votos
        votos_existentes = votos_sheet.get_all_records()
        df_votos = pd.DataFrame(votos_existentes) if votos_existentes else pd.DataFrame(columns=["Matriculas", "Candidato", "Total de Votos"])

        # Verifica se a matrícula já votou
        ja_votou = df_votos["Matriculas"].astype(str).apply(lambda x: matricula in x.split(";")).any()

        if ja_votou:
            st.warning("⚠️ Você já votou! Cada matrícula só pode votar uma vez.")
        else:
            # Se o candidato já existe, soma 1 e adiciona matrícula à lista
            if escolha in df_votos["Candidato"].values:
                idx = df_votos.index[df_votos["Candidato"] == escolha][0]
                matriculas_antigas = df_votos.at[idx, "Matriculas"]
                novas_matriculas = matriculas_antigas + ";" + matricula if matriculas_antigas else matricula
                df_votos.at[idx, "Matriculas"] = novas_matriculas
                df_votos.at[idx, "Total de Votos"] = int(df_votos.at[idx, "Total de Votos"]) + 1
            else:
                novo = pd.DataFrame({"Matriculas": [matricula], "Candidato": [escolha], "Total de Votos": [1]})
                df_votos = pd.concat([df_votos, novo], ignore_index=True)

            # Limpa e atualiza a planilha
            votos_sheet.clear()
            votos_sheet.append_row(["Matriculas", "Candidato", "Total de Votos"])
            for _, row in df_votos.iterrows():
                votos_sheet.append_row([row["Matriculas"], row["Candidato"], int(row["Total de Votos"])])

            st.success(f"✅ Voto registrado com sucesso para {escolha}!")
