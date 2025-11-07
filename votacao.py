import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from streamlit import secrets
import base64
from datetime import datetime
import time

# ======== FUNÇÕES AUXILIARES ========
def backup_sheet(sheet, name_hint="Votos"):
    """Cria uma aba de backup com timestamp contendo todos os valores atuais do spreadsheet."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_title = f"Backup_{name_hint}_{ts}"
    try:
        values = sheet.get_all_values()
    except Exception:
        values = []
    # cria worksheet com número suficiente de linhas/cols
    backup_ws = sheet.add_worksheet(title=backup_title, rows=str(max(100, len(values)+5)), cols="10")
    if values:
        for r in values:
            backup_ws.append_row(r)
    return backup_title

def ensure_sheet_by_title(sheet, title, cols=10, rows=1000, header=None):
    """Retorna worksheet com título; cria se não existir."""
    try:
        ws = sheet.worksheet(title)
    except Exception:
        ws = sheet.add_worksheet(title=title, rows=str(rows), cols=str(cols))
        if header:
            ws.append_row(header)
    return ws

def migrate_rows_if_needed(src_ws, dest_ws):
    """Se src_ws contém linhas de dados (além do cabeçalho) e dest_ws está vazio (apenas cabeçalho), migra os registros."""
    src_vals = src_ws.get_all_values()
    if not src_vals or len(src_vals) <= 1:
        return 0
    dest_vals = dest_ws.get_all_values()
    # assumindo primeira linha cabeçalho
    migrated = 0
    for row in src_vals[1:]:
        # evita duplicar cabeçalho vazio
        if any(cell.strip() for cell in row):
            dest_ws.append_row(row)
            migrated += 1
    return migrated

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

# ======== CHAMA O FUNDO E HEADER ========
set_background("polimeros.png")
st.markdown("<h1 style='text-align: center; color: #FF6900; font-size: 40px;'>SISTEMA DE VOTAÇÃO</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size: 20px; color: #333; margin-top: 10px;'>Bem-vindo ao Sistema de Votação - Café com Gestor.</div>", unsafe_allow_html=True)
st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ======== AUTENTICAÇÃO GOOGLE SHEETS ========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# abrir spreadsheet
sheet = client.open("vota-o-phayton@firm-mariner-397622.iam.gserviceaccount.com")
candidatos_sheet = sheet.worksheet("Candidatos")

# ======== BACKUP AUTOMÁTICO (antes de qualquer mudança) ========
backup_title = backup_sheet(sheet, name_hint="Votos")
st.info(f"Backup automático criado: {backup_title}")

# ======== GARANTIR EXISTÊNCIA DAS ABAS (Votos Brutos e Votos de Resumo) ========
votos_brutos_sheet = ensure_sheet_by_title(sheet, "Votos Brutos", cols=2, rows=2000, header=["Matricula", "Candidato"])
votos_sheet = ensure_sheet_by_title(sheet, "Votos", cols=3, rows=2000, header=["Matriculas", "Candidato", "Total de Votos"])

# Caso os dados originais estivessem apenas na aba 'Votos' (antes de termos 'Votos Brutos'),
# migramos as linhas não-header para 'Votos Brutos' — isso protege histórico.
migrated = migrate_rows_if_needed(votos_sheet, votos_brutos_sheet)
if migrated > 0:
    st.info(f"Migrei {migrated} linhas da aba 'Votos' para 'Votos Brutos' para preservar histórico.")

# Lista de candidatos
candidatos = candidatos_sheet.col_values(1)

# ======== FORMULÁRIO ========
matricula = st.text_input("Digite sua matrícula:")
escolha = st.radio("Escolha seu candidato:", candidatos)

# ======== LÓGICA DE VOTO (SEGURA) ========
if st.button("Votar"):
    if not matricula.strip():
        st.error("⚠️ Por favor, informe sua matrícula antes de votar.")
    else:
        # Lê votos brutos (histórico)
        votos_existentes = votos_brutos_sheet.get_all_records()
        df_votos = pd.DataFrame(votos_existentes) if votos_existentes else pd.DataFrame(columns=["Matricula", "Candidato"])

        # Verifica se matrícula já votou
        if matricula in df_votos["Matricula"].astype(str).values:
            st.warning("⚠️ Você já votou! Cada matrícula só pode votar uma vez.")
        else:
            try:
                # adiciona o voto ao histórico (sempre preservado)
                votos_brutos_sheet.append_row([matricula, escolha])

                # re-calcula a consolidação a partir do histórico (fonte única de verdade)
                votos_atualizados = votos_brutos_sheet.get_all_records()
                df_atualizado = pd.DataFrame(votos_atualizados)

                if df_atualizado.empty:
                    contagem_df = pd.DataFrame(columns=["Candidato", "Matriculas_str", "Total de Votos"])
                else:
                    grouped = df_atualizado.groupby("Candidato")["Matricula"].apply(list).reset_index()
                    grouped["Total de Votos"] = grouped["Matricula"].apply(len)
                    grouped["Matriculas_str"] = grouped["Matricula"].apply(lambda l: ";".join(map(str, l)))
                    contagem_df = grouped[["Candidato", "Matriculas_str", "Total de Votos"]]

                # Atualiza a aba 'Votos' (resumo) com os dados consolidados, sem tocar 'Votos Brutos'
                votos_sheet.clear()
                votos_sheet.append_row(["Matriculas", "Candidato", "Total de Votos"])
                if not contagem_df.empty:
                    for _, row in contagem_df.iterrows():
                        votos_sheet.append_row([row["Matriculas_str"], row["Candidato"], int(row["Total de Votos"])])

                st.success(f"✅ Voto registrado com sucesso para {escolha}!")
            except Exception as e:
                st.error(f"❌ Erro ao registrar voto: {e}")

# ======== Exibição opcional do resumo no app ========
try:
    resumo = votos_sheet.get_all_records()
    if resumo:
        df_resumo = pd.DataFrame(resumo)
        st.markdown("### Resumo de Votos")
        st.dataframe(df_resumo)
except Exception:
    pass
