import streamlit as st
import datetime
from agent.agent import DuoConciergeAgent

# ── Configuração da página ──────────────────────────────────
st.set_page_config(
    page_title="Duo Concierge",
    page_icon="🍽️",
    layout="wide"
)

# ── Inicialização do estado ──────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "steps" not in st.session_state:
    st.session_state.steps = {}

# ── Custom CSS para alinhar tipografia e marca com DuoList ───
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"], .stApp {
            font-family: 'Outfit', sans-serif !important;
        }
        /* Ajustar borda dos inputs */
        .stTextInput input, .stChatInput textarea {
            border-color: rgba(255, 255, 255, 0.08) !important;
        }
        .stTextInput input:focus, .stChatInput textarea:focus {
            border-color: #fbcd4b !important;
            box-shadow: 0 0 0 3px rgba(251, 205, 75, 0.15) !important;
        }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────
api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")

if not api_key:
    st.sidebar.info("""
    💡 **O que é a API do Gemini?**
    É a interface que conecta este assistente à IA do Google, permitindo analisar restaurantes de forma personalizada.
    
    🔑 **Como conseguir sua chave (API Key)?**
    1. Acesse o **[Google AI Studio](https://aistudio.google.com/)**.
    2. Clique em **"Get API Key"**.
    3. Crie uma chave gratuita.
    
    👉 Veja mais no **[Guia do Gemini API](https://ai.google.dev/gemini-api/docs/quickstart?hl=pt-br)**.
    """)

st.sidebar.markdown("---")
st.sidebar.title("🧪 Simulação de Contexto")

# Permite simular diferentes dias e horários para fins de teste do schedule do Duo Gourmet
usar_data_atual = st.sidebar.checkbox("Usar data/hora atual", value=True)

if not usar_data_atual:
    dia_simulado = st.sidebar.selectbox(
        "Dia da Semana",
        ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    )
    hora_simulada = st.sidebar.time_input("Horário da visita", datetime.time(20, 0))
    periodo_simulado = st.sidebar.selectbox("Refeição", ["almoco", "jantar"])
    
    contexto_tempo = f"Hoje é {dia_simulado}, às {hora_simulada.strftime('%H:%M')}. Período: {periodo_simulado}."
else:
    # Mapeamento do dia da semana em português
    dias_semana_pt = {
        0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
        3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
    }
    agora = datetime.datetime.now()
    dia_pt = dias_semana_pt[agora.weekday()]
    hora_str = agora.strftime("%H:%M")
    periodo = "almoco" if agora.hour < 17 else "jantar"
    
    contexto_tempo = f"Hoje é {dia_pt}, às {hora_str}. Período: {periodo}."

# Simulação de localização do usuário
st.sidebar.markdown("---")
st.sidebar.title("📍 Localização Simulada")
usa_localizacao = st.sidebar.checkbox("Simular Localização (GPS)", value=False)
lat_usuario = None
lon_usuario = None

opcao_bairro = None
if usa_localizacao:
    opcao_bairro = st.sidebar.selectbox(
        "Selecione um ponto de referência em BH",
        [
            "Savassi (Praça Diogo de Vasconcelos)",
            "Lourdes (Praça Marília de Dirceu)",
            "Centro (Praça da Estação)",
            "Buritis (Parque Aggeo Pio Sobrinho)",
            "Pampulha (Igrejinha)"
        ]
    )
    
    coords = {
        "Savassi (Praça Diogo de Vasconcelos)": (-19.9386, -43.9359),
        "Lourdes (Praça Marília de Dirceu)": (-19.9348, -43.9455),
        "Centro (Praça da Estação)": (-19.9169, -43.9346),
        "Buritis (Parque Aggeo Pio Sobrinho)": (-19.9723, -43.9686),
        "Pampulha (Igrejinha)": (-19.8519, -43.9793)
    }
    lat_usuario, lon_usuario = coords[opcao_bairro]
    st.sidebar.caption(f"Lat: {lat_usuario} / Lon: {lon_usuario}")

st.sidebar.markdown("---")
st.sidebar.title("ℹ️ Sobre o Duo Gourmet")
st.sidebar.markdown("""
O **Duo Gourmet** é um benefício que permite pedir um prato
principal e ganhar outro de igual ou menor valor.

Use este assistente para encontrar o restaurante ideal.
""")

if st.sidebar.button("🔄 Nova Conversa"):
    st.session_state.messages = []
    st.session_state.steps = {}
    st.rerun()

# ── Cabeçalho principal com Branding do DuoList ──────────────
st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-top: -20px; margin-bottom: 5px;">
        <span style="font-size: 28px; color: #fbcd4b;">🍽️</span>
        <h1 style="font-size: 26px; font-weight: 700; margin: 0; color: #f8fafc; font-family: 'Outfit', sans-serif;">
            Duo<span style="color: #fbcd4b;">Concierge</span>
        </h1>
    </div>
    <p style="font-size: 13px; color: #94a3b8; margin-top: -6px; margin-bottom: 20px; font-weight: 300;">
        Seu assistente inteligente de gastronomia integrado com o mapa DuoList BH
    </p>
""", unsafe_allow_html=True)

# Exibe contexto de simulação ativo
st.info(f"⚙️ **Contexto Ativo:** {contexto_tempo}" + (f" | 📍 Proximidade ligada: {opcao_bairro}" if usa_localizacao else ""))

# ── Exibe histórico de mensagens ─────────────────────────────
avatars = {"human": "user", "ai": "assistant"}

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(avatars[msg["role"]]):
        # Expanders para cada tool chamada (transparência do agente)
        for step in st.session_state.steps.get(str(idx), []):
            with st.expander(f"⚙️ **Ferramenta executada:** `{step['tool']}`"):
                st.write("**Parâmetros:**", step['args'])
                st.write("**Resultado retornado:**", step['result'])
        st.markdown(msg["content"])

# ── Input do usuário ─────────────────────────────────────────
if user_input := st.chat_input("Ex: Quero comer comida italiana hoje à noite 🍝"):

    if not api_key:
        st.warning("⚠️ Adicione sua Gemini API Key na barra lateral.")
        st.stop()

    # Exibe mensagem do usuário
    st.session_state.messages.append({"role": "human", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Executa o agente e captura steps intermediários
    with st.chat_message("assistant"):
        with st.spinner("🤖 Procurando o melhor restaurante para você..."):
            agent = DuoConciergeAgent(api_key=api_key)
            
            # Incorpora as coordenadas de localização se ativado
            prompt_completo = user_input
            if lat_usuario and lon_usuario:
                prompt_completo += f" (Minhas coordenadas base de cálculo: lat={lat_usuario}, lon={lon_usuario})"
                
            response, intermediate_steps = agent.run(prompt_completo, contexto_tempo)

        # Expanders dos passos intermediários
        for step in intermediate_steps:
            with st.expander(f"⚙️ **Ferramenta executada:** `{step['tool']}`"):
                st.write("**Parâmetros:**", step['args'])
                st.write("**Resultado retornado:**", step['result'])

        st.markdown(response)

    # Salva no histórico
    idx = len(st.session_state.messages) - 1
    st.session_state.messages.append({"role": "ai", "content": response})
    st.session_state.steps[str(idx + 1)] = intermediate_steps
