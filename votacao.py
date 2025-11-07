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
        div[data-testid="stTextInput"] label p,
        div[data-testid="stRadio"] > label p {{
            font-size: 22px !important;
            font-weight: normal !important;
            color: #333 !important;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("⚠️ Arquivo 'polimeros.png' não encontrado!")

# ======== CHAMA O FUNDO ========
set_background("polimeros.png")

# ======== TÍTULO ========
st.markdown(
    "<h1 style='text-align: center; color: #FF6900; font-size: 40px;'>SISTEMA DE VOTAÇÃO</h1>",
    unsafe_allow_html=True,
)

# ======== INTRODUÇÃO ========
st.markdown(
    """
<div style='text-align: center; font-size: 20px; color: #333; margin-top: 10px;'>
Bem-vindo ao Sistema de Votação - Café com Gestor.
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ======== AUTENTICAÇÃO GOOGLE SHEETS ========
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds_dict = secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Nome do arquivo e abas
sheet = client.open("vota-o-phayton@firm-mariner-397622.iam.gserviceaccount.com")
candidatos_sheet = sheet.worksheet("Candidatos")

# tenta obter a aba "Votos Brutos" (histórico), se não existir cria
try:
    votos_brutos_sheet = sheet.worksheet("Votos Brutos")
except Exception:
    votos_brutos_sheet = sheet.add_worksheet(title="Votos Brutos", rows="1000", cols="2")
    votos_brutos_sheet.append_row(["Matricula", "Candidato"])

# aba de resumo consolidado
try:
    votos_sheet = sheet.worksheet("Votos")
except Exception:
    votos_sheet = sheet.add_worksheet(title="Votos", rows="1000", cols="3")
    votos_sheet.append_row(["Matriculas", "Candidato", "Total de Votos"])

# Lista de candidatos
candidatos = candidatos_sheet.col_values(1)

# ======== FORMULÁRIO ========
matricula = st.text_input("Digite sua matrícula:")
escolha = st.radio("Escolha seu candidato:", candidatos)

# ======== LÓGICA DE VOTO ========
if st.button("Votar"):
    if not matricula.strip():
        st.error("Por favor, informe sua matrícula.")
    else:
        votos_brutos = votos_brutos_sheet.get_all_records()
        df_brutos = pd.DataFrame(votos_brutos) if votos_brutos else pd.DataFrame(columns=["Matricula", "Candidato"])

        if matricula in df_brutos["Matricula"].astype(str).values:
            st.warning("⚠️ Você já votou! Cada matrícula só pode votar uma vez.")
        else:
            try:
                votos_brutos_sheet.append_row([matricula, escolha])
                st.success(f"✅ Voto registrado com sucesso para {escolha}!")
            except Exception as e:
                st.error(f"Erro ao registrar voto: {e}")

# ======== MOSTRAR RESUMO NA TELA ========
votos_brutos = votos_brutos_sheet.get_all_records()
df_brutos = pd.DataFrame(votos_brutos)
if not df_brutos.empty:
    contagem = df_brutos["Candidato"].value_counts().reset_index()
    contagem.columns = ["Candidato", "Total de Votos"]
    st.subheader("📊 Resultado Parcial")
    st.table(contagem)

# ======== BOTÃO PARA ATUALIZAR PLANILHA DE RESUMO ========
if st.button("Atualizar aba Votos"):
    try:
        dados_votos = [["Matriculas", "Candidato", "Total de Votos"]]
        for candidato in candidatos:
            total = contagem.loc[contagem["Candidato"] == candidato, "Total de Votos"]
            dados_votos.append(["", candidato, int(total.values[0]) if not total.empty else 0])
        votos_sheet.update(f"A1:C{len(dados_votos)}", dados_votos)
        st.success("✅ Aba 'Votos' atualizada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao atualizar aba Votos: {e}")
