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
        st.warning("⚠️ Arquivo 'polimeros.png' não encontrado! Usando estilo padrão.")

# ======== FUNÇÃO PARA INICIALIZAR ABAS ========
def inicializar_abas(sheet):
    """Garante que as abas necessárias existam com cabeçalhos corretos"""
    try:
        # Usa aba Votos (já existe)
        try:
            votos_sheet = sheet.worksheet("Votos")
            # Verifica se tem cabeçalho
            if not votos_sheet.row_values(1):
                votos_sheet.append_row(["Matricula", "Candidato", "Data/Hora"])
        except gspread.WorksheetNotFound:
            votos_sheet = sheet.add_worksheet(title="Votos", rows="1000", cols="3")
            votos_sheet.append_row(["Matricula", "Candidato", "Data/Hora"])
        
        # Verifica/cria aba Totalização
        try:
            totalizacao_sheet = sheet.worksheet("Totalizacao")
            # Verifica se tem cabeçalho
            if not totalizacao_sheet.row_values(1):
                totalizacao_sheet.append_row(["Candidato", "Total de Votos"])
        except gspread.WorksheetNotFound:
            totalizacao_sheet = sheet.add_worksheet(title="Totalizacao", rows="100", cols="2")
            totalizacao_sheet.append_row(["Candidato", "Total de Votos"])
        
        return votos_sheet, totalizacao_sheet
    except Exception as e:
        st.error(f"Erro ao inicializar abas: {e}")
        return None, None

# ======== FUNÇÃO PARA ATUALIZAR TOTALIZAÇÃO ========
def atualizar_totalizacao(votos_sheet, totalizacao_sheet, candidatos):
    """Atualiza a aba de totalização com a contagem de votos"""
    try:
        # Lê todos os votos (exceto cabeçalho)
        votos = votos_sheet.get_all_records()
        
        if votos:
            df_votos = pd.DataFrame(votos)
            # Conta votos por candidato
            contagem = df_votos["Candidato"].value_counts().to_dict()
        else:
            contagem = {}
        
        # Limpa a aba de totalização (mantém cabeçalho)
        totalizacao_sheet.clear()
        totalizacao_sheet.append_row(["Candidato", "Total de Votos"])
        
        # Adiciona todos os candidatos com suas contagens
        dados_totalizacao = []
        for candidato in candidatos:
            if candidato.strip():  # Ignora linhas vazias
                total = contagem.get(candidato, 0)
                dados_totalizacao.append([candidato, total])
        
        # Ordena por total de votos (decrescente)
        dados_totalizacao.sort(key=lambda x: x[1], reverse=True)
        
        # Insere os dados
        if dados_totalizacao:
            totalizacao_sheet.append_rows(dados_totalizacao)
        
        return dados_totalizacao
    except Exception as e:
        st.error(f"Erro ao atualizar totalização: {e}")
        return []

# ======== CHAMA O FUNDO ========
set_background("polimeros.png")

# ======== TÍTULO ========
st.markdown("<h1 style='text-align: center; color: #FF6900; font-size: 40px;'>SISTEMA DE VOTAÇÃO</h1>", 
            unsafe_allow_html=True)

# ======== INTRODUÇÃO ========
st.markdown("""
<div style='text-align: center; font-size: 20px; color: #333; margin-top: 10px;'>
    Bem-vindo ao Sistema de Votação - Café com Gestor.
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ======== AUTENTICAÇÃO GOOGLE SHEETS ========
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = secrets["google"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Abre a planilha
    sheet = client.open("vota-o-phayton@firm-mariner-397622.iam.gserviceaccount.com")
    
    # Inicializa as abas
    votos_sheet, totalizacao_sheet = inicializar_abas(sheet)
    
    if votos_sheet is None or totalizacao_sheet is None:
        st.error("Erro ao inicializar planilhas. Verifique as permissões.")
        st.stop()
    
    # Carrega lista de candidatos
    candidatos_sheet = sheet.worksheet("Candidatos")
    candidatos = [c for c in candidatos_sheet.col_values(1) if c.strip()]
    
except Exception as e:
    st.error(f"Erro ao conectar com Google Sheets: {e}")
    st.stop()

# ======== FORMULÁRIO DE VOTAÇÃO ========
matricula = st.text_input("Digite sua matrícula:")
escolha = st.radio("Escolha seu candidato:", candidatos)

if st.button("Votar"):
    if not matricula.strip():
        st.error("⚠️ Por favor, informe sua matrícula.")
    else:
        try:
            # Verifica se a matrícula já votou
            votos = votos_sheet.get_all_records()
            df_votos = pd.DataFrame(votos) if votos else pd.DataFrame(columns=["Matricula", "Candidato", "Data/Hora"])
            
            if matricula in df_votos["Matricula"].astype(str).values:
                st.warning("⚠️ Você já votou! Cada matrícula só pode votar uma vez.")
            else:
                # Registra o voto na aba Votos
                from datetime import datetime
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                votos_sheet.append_row([matricula, escolha, data_hora])
                
                # Atualiza a totalização
                totalizacao = atualizar_totalizacao(votos_sheet, totalizacao_sheet, candidatos)
                
                st.success(f"✅ Voto registrado com sucesso para **{escolha}**!")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Erro ao registrar voto: {e}")

# A totalização é atualizada automaticamente na planilha após cada voto
# mas não é exibida no app para manter o sigilo até o encerramento da votação
