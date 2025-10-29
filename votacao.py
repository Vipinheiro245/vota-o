import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from streamlit import secrets
import base64

# ======== FUNÇÃO PARA DEFINIR FUNDO ========
def set_background(image_file):
    try:
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
        /* ======== AUMENTAR TAMANHO DOS LABELS ======== */
        div[data-testid="stTextInput"] label {{
            font-size: 40px !important;  /* MUITO MAIOR */
            font-weight: bold;
            color: #333;
        }}
        div[data-testid="stRadio"] label {{
            font-size: 40px !important;  /* MUITO MAIOR */
            font-weight: bold;
            color: #333;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("⚠️ Arquivo 'polimeros.png' não encontrado!")

# ======== CHAMA O FUNDO ========
set_background("polimeros.png")

# ======== TÍTULO ========
st.markdown("<h1 style='text-align: center; color: #FF6900; font-size: 40px;'>SISTEMA DE VOTAÇÃO</h1>", unsafe_allow_html=True)

# ======== INTRODUÇÃO ========
st.markdown("""
<div style='text-align: center; font-size: 20px; color: #333; margin-top: 10px;'>
Bem-vindo ao Sistema de Votação - Café com Gestor.
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ======== AUTENTICAÇÃO GOOGLE SHEETS ========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("vota-o-phayton@firm-mariner-397622.iam.gserviceaccount.com")
candidatos_sheet = sheet.worksheet("Candidatos")
votos_sheet = sheet.worksheet("Votos")
candidatos = candidatos_sheet.col_values(1)

# ======== FORMULÁRIO ========
matricula = st.text_input("Digite sua matrícula:")
escolha = st.radio("Escolha seu candidato:", candidatos)

if st.button("Votar"):
    if not matricula.strip():
        st.error("Por favor, informe sua matrícula.")
    else:
        votos = votos_sheet.get_all_records()
        df_votos = pd.DataFrame(votos) if votos else pd.DataFrame(columns=["Matricula", "Candidato"])
        
        if matricula in df_votos["Matricula"].astype(str).values:
            st.warning("⚠️ Você já votou! Cada matrícula só pode votar uma vez.")
        else:
            try:
                votos_sheet.append_row([matricula, escolha])
                st.success(f"✅ Voto registrado com sucesso para {escolha}!")
            except Exception as e:
                st.error(f"Erro ao registrar voto: {e}")
