import sys
import os
import re
import json
import datetime
from zoneinfo import ZoneInfo
import gradio as gr
from smolagents.agents import ActionStep, MultiStepAgent
from smolagents.memory import MemoryStep
from smolagents.agent_types import AgentText, handle_agent_output_types

# Adiciona o diretório próprio ao PATH para garantir a importação das ferramentas locais do DuoSmolAgent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools as agent_tools

# Coordenadas pré-definidas para simulação de pontos de referência
coords_bh = {
    "Savassi (Praça Diogo de Vasconcelos)": (-19.9386, -43.9359),
    "Lourdes (Praça Marília de Dirceu)": (-19.9348, -43.9455),
    "Centro (Praça da Estação)": (-19.9169, -43.9346),
    "Buritis (Parque Aggeo Pio Sobrinho)": (-19.9723, -43.9686),
    "Pampulha (Igrejinha)": (-19.8519, -43.9793)
}
coords_sp = {
    "Pinheiros (Estação Pinheiros)": (-23.5663, -46.7029),
    "Jardins (Oscar Freire)": (-23.5616, -46.6660),
    "Itaim Bibi (Parque do Povo)": (-23.5852, -46.6853),
    "Vila Madalena (Beco do Batman)": (-23.5539, -46.6966),
    "Centro (Praça da Sé)": (-23.5505, -46.6333)
}

# Códigos JavaScript para serem executados no navegador do usuário
js_gps = """
() => {
    return new Promise((resolve) => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve(JSON.stringify({
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        success: true
                    }));
                },
                (error) => {
                    resolve(JSON.stringify({
                        lat: -19.9191,
                        lon: -43.9386,
                        success: false,
                        error: error.message
                    }));
                },
                { enableHighAccuracy: true, timeout: 6000, maximumAge: 0 }
            );
        } else {
            resolve(JSON.stringify({
                lat: -19.9191,
                lon: -43.9386,
                success: false,
                error: "Geolocation not supported"
            }));
        }
    });
}
"""

js_tz = "() => Intl.DateTimeFormat().resolvedOptions().timeZone"

class GradioUI:
    def __init__(self, agent: MultiStepAgent):
        self.agent = agent

    def pull_messages_from_step(self, step_log: MemoryStep):
        """Extrai mensagens do log de passos do smolagents formatando-as no padrão Gradio ChatMessage"""
        if isinstance(step_log, ActionStep):
            step_number = f"Passo {step_log.step_number}" if step_log.step_number is not None else ""
            yield gr.ChatMessage(role="assistant", content=f"🔍 **{step_number}**")

            if hasattr(step_log, "model_output") and step_log.model_output is not None:
                model_output = step_log.model_output.strip()
                model_output = re.sub(r"```\s*<end_code>", "```", model_output)
                model_output = re.sub(r"<end_code>\s*```", "```", model_output)
                model_output = re.sub(r"```\s*\n\s*<end_code>", "```", model_output)
                model_output = model_output.strip()
                yield gr.ChatMessage(role="assistant", content=model_output)

            if hasattr(step_log, "tool_calls") and step_log.tool_calls is not None:
                first_tool_call = step_log.tool_calls[0]
                used_code = first_tool_call.name == "python_interpreter"
                parent_id = f"call_{len(step_log.tool_calls)}"

                args = first_tool_call.arguments
                content = str(args.get("answer", str(args))) if isinstance(args, dict) else str(args).strip()

                if used_code:
                    content = re.sub(r"```.*?\n", "", content)
                    content = re.sub(r"\s*<end_code>\s*", "", content)
                    content = content.strip()
                    if not content.startswith("```python"):
                        content = f"```python\n{content}\n```"

                parent_message_tool = gr.ChatMessage(
                    role="assistant",
                    content=content,
                    metadata={
                        "title": f"🛠️ Ferramenta Executada: {first_tool_call.name}",
                        "id": parent_id,
                        "status": "pending",
                    },
                )
                yield parent_message_tool

                if hasattr(step_log, "observations") and step_log.observations is not None and step_log.observations.strip():
                    log_content = step_log.observations.strip()
                    log_content = re.sub(r"^Execution logs:\s*", "", log_content)
                    yield gr.ChatMessage(
                        role="assistant",
                        content=f"{log_content}",
                        metadata={"title": "📝 Logs de Observação", "parent_id": parent_id, "status": "done"},
                    )

                if hasattr(step_log, "error") and step_log.error is not None:
                    yield gr.ChatMessage(
                        role="assistant",
                        content=str(step_log.error),
                        metadata={"title": "💥 Erro na Execução", "parent_id": parent_id, "status": "done"},
                    )

                parent_message_tool.metadata["status"] = "done"

            elif hasattr(step_log, "error") and step_log.error is not None:
                yield gr.ChatMessage(role="assistant", content=str(step_log.error), metadata={"title": "💥 Erro"})

            step_footnote = f"{step_number}"
            if hasattr(step_log, "duration"):
                step_duration = f" | Duração: {round(float(step_log.duration), 2)}s" if step_log.duration else None
                step_footnote += step_duration
            step_footnote = f"""<span style="color: #64748b; font-size: 11px;">{step_footnote}</span>"""
            yield gr.ChatMessage(role="assistant", content=f"{step_footnote}")
            yield gr.ChatMessage(role="assistant", content="---")

    def stream_to_gradio(self, task: str):
        """Executa o agente e envia em tempo real os passos de raciocínio para o Gradio"""
        for step_log in self.agent.run(task, stream=True, reset=True):
            for message in self.pull_messages_from_step(step_log):
                yield message

        final_answer = step_log
        final_answer = handle_agent_output_types(final_answer)

        if isinstance(final_answer, AgentText):
            yield gr.ChatMessage(role="assistant", content=f"### 🍽️ Resposta Final:\n{final_answer.to_string()}\n")
        else:
            yield gr.ChatMessage(role="assistant", content=f"### 🍽️ Resposta Final: {str(final_answer)}")

    def process_chat(
        self,
        prompt,
        messages,
        modo_loc,
        gps_lat,
        gps_lon,
        sim_lat,
        sim_lon,
        usar_atual,
        dia_sim,
        hora_sim,
        periodo_sim,
        browser_tz
    ):
        # 1. Definir coordenadas ativas com base no modo de localização
        if modo_loc == "Usar GPS do Navegador":
            active_lat, active_lon = gps_lat, gps_lon
        elif modo_loc == "Simular Ponto de Referência":
            active_lat, active_lon = sim_lat, sim_lon
        else:
            active_lat, active_lon = None, None

        # 2. Definir fuso horário e contexto de tempo
        if usar_atual:
            dias_semana_pt = {
                0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
                3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
            }
            try:
                zone = ZoneInfo(browser_tz)
            except Exception:
                zone = ZoneInfo("America/Sao_Paulo")
            agora = datetime.datetime.now(zone)
            dia_pt = dias_semana_pt[agora.weekday()]
            hora_str = agora.strftime("%H:%M")
            periodo = "almoco" if agora.hour < 17 else "jantar"
            active_time = f"Hoje é {dia_pt}, às {hora_str}. Período: {periodo}."
        else:
            active_time = f"Hoje é {dia_sim}, às {hora_sim}. Período: {periodo_sim}."

        # 3. Atualizar o estado global de contexto nas ferramentas do smolagents
        agent_tools.user_location["lat"] = active_lat
        agent_tools.user_location["lon"] = active_lon
        agent_tools.time_context = active_time

        # 4. Adicionar mensagem do usuário no chatbot
        messages.append(gr.ChatMessage(role="user", content=prompt))
        yield messages

        # 5. Executar o loop do agente enviando atualizações parciais
        for msg in self.stream_to_gradio(task=prompt):
            messages.append(msg)
            yield messages

    def launch(self, **kwargs):
        # CSS customizado para aplicar o Outfit e estilizar o design de forma premium
        custom_css = """
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        body, .gradio-container {
            font-family: 'Outfit', sans-serif !important;
        }
        .sidebar {
            background-color: #1e293b !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        .chat-title {
            font-weight: 700;
            color: #f8fafc;
        }
        .chat-subtitle {
            color: #94a3b8;
            margin-top: -8px;
            margin-bottom: 20px;
        }
        """

        with gr.Blocks() as demo:
            
            # Inputs ocultos para GPS e Timezone detectados via JavaScript
            gps_hidden = gr.Textbox(visible=False)
            tz_hidden = gr.Textbox(visible=False)
            
            # Estados de dados reais de GPS e Timezone do navegador
            gps_lat = gr.State(-19.9191)
            gps_lon = gr.State(-43.9386)
            browser_timezone = gr.State("America/Sao_Paulo")
            
            with gr.Row():
                # Barra lateral de configurações
                with gr.Sidebar(elem_classes="sidebar"):
                    gr.Markdown("### 📍 Localização do Usuário")
                    modo_localizacao = gr.Radio(
                        label="Como definir sua posição?",
                        choices=["Desativada", "Usar GPS do Navegador", "Simular Ponto de Referência"],
                        value="Desativada"
                    )
                    
                    cidade_simulacao = gr.Dropdown(
                        label="Cidade de Simulação",
                        choices=["Belo Horizonte (BH)", "São Paulo (SP)"],
                        value="Belo Horizonte (BH)",
                        visible=False
                    )
                    
                    ponto_simulacao = gr.Dropdown(
                        label="Selecione um ponto de referência",
                        choices=list(coords_bh.keys()),
                        value=list(coords_bh.keys())[0],
                        visible=False
                    )
                    
                    # Coordenadas ativas simuladas
                    sim_lat = gr.State(coords_bh[list(coords_bh.keys())[0]][0])
                    sim_lon = gr.State(coords_bh[list(coords_bh.keys())[0]][1])
                    
                    # Caixa informativa para status da geolocalização
                    info_localizacao = gr.Markdown("📍 Localização: Desativada")
                    
                    gr.Markdown("---")
                    gr.Markdown("### 🧪 Simulação de Contexto de Tempo")
                    usar_data_atual = gr.Checkbox(label="Usar data/hora atual", value=True)
                    
                    with gr.Column(visible=False) as sim_time_panel:
                        dia_simulado = gr.Dropdown(
                            label="Dia da Semana",
                            choices=["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"],
                            value="Sexta-feira"
                        )
                        hora_simulada = gr.Textbox(label="Horário (HH:MM)", value="20:00")
                        periodo_simulado = gr.Radio(label="Refeição", choices=["almoco", "jantar"], value="jantar")
                    
                    gr.Markdown("---")
                    gr.Markdown("💡 *O Duo Concierge utiliza sua localização para indicar a distância física dos restaurantes parceiros e o contexto temporal para checar a validade do benefício.*")

                # Tela principal do chat
                with gr.Column(scale=4):
                    gr.HTML("""
                        <div style="display: flex; align-items: center; gap: 12px; margin-top: 10px;">
                            <span style="font-size: 32px;">🍽️</span>
                            <h1 class='chat-title' style='margin: 0;'>Duo<span style='color: #fbcd4b;'>Concierge</span></h1>
                        </div>
                        <p class='chat-subtitle'>Seu assistente inteligente de gastronomia integrado com o DuoList BH & SP</p>
                    """)
                    
                    chatbot = gr.Chatbot(
                        label="Duo Concierge",
                        avatar_images=(
                            None,
                            "https://huggingface.co/datasets/agents-course/course-images/resolve/main/en/communication/Alfred.png",
                        ),
                        resizable=True,
                        scale=1
                    )
                    
                    text_input = gr.Textbox(lines=1, placeholder="Ex: Quero comer comida italiana hoje à noite 🍝", label="Mensagem")
                    
                    text_input.submit(
                        self.process_chat,
                        inputs=[
                            text_input, chatbot,
                            modo_localizacao, gps_lat, gps_lon, sim_lat, sim_lon,
                            usar_data_atual, dia_simulado, hora_simulada, periodo_simulado, browser_timezone
                        ],
                        outputs=[chatbot]
                    ).then(
                        fn=lambda: "",
                        outputs=[text_input]
                    )

            # ── Interações de Reatividade da UI ─────────────────────────────
            
            # Ao alterar o modo de localização
            def on_loc_mode_change(mode, gps_status_text, s_lat, s_lon):
                if mode == "Usar GPS do Navegador":
                    return gr.update(visible=False), gr.update(visible=False), gps_status_text
                elif mode == "Simular Ponto de Referência":
                    return gr.update(visible=True), gr.update(visible=True), f"📍 Ponto Simulado: {s_lat}, {s_lon}"
                else:
                    return gr.update(visible=False), gr.update(visible=False), "📍 Localização: Desativada"

            modo_localizacao.change(
                on_loc_mode_change,
                inputs=[modo_localizacao, info_localizacao, sim_lat, sim_lon],
                outputs=[cidade_simulacao, ponto_simulacao, info_localizacao]
            )

            # Ao alterar a cidade de simulação
            def on_cidade_change(cidade):
                if "BH" in cidade:
                    choices = list(coords_bh.keys())
                else:
                    choices = list(coords_sp.keys())
                return gr.update(choices=choices, value=choices[0])

            cidade_simulacao.change(
                on_cidade_change,
                inputs=[cidade_simulacao],
                outputs=[ponto_simulacao]
            )

            # Ao alterar o ponto de simulação
            def on_ponto_change(ponto, cidade):
                if "BH" in cidade:
                    lat, lon = coords_bh.get(ponto, (None, None))
                else:
                    lat, lon = coords_sp.get(ponto, (None, None))
                return lat, lon, f"📍 Ponto Simulado: {lat:.4f}, {lon:.4f}"

            ponto_simulacao.change(
                on_ponto_change,
                inputs=[ponto_simulacao, cidade_simulacao],
                outputs=[sim_lat, sim_lon, info_localizacao]
            )

            # Ao alterar o uso do tempo simulado vs atual
            usar_data_atual.change(
                fn=lambda val: gr.update(visible=not val),
                inputs=[usar_data_atual],
                outputs=[sim_time_panel]
            )

            # ── Scripts JS carregados na inicialização da página ─────────────
            
            # 1. Obter GPS do Navegador
            def handle_gps_payload(gps_str, mode):
                try:
                    data = json.loads(gps_str)
                    if data.get("success"):
                        lat, lon = data["lat"], data["lon"]
                        status_text = f"✅ GPS Ativo: {lat:.4f}, {lon:.4f}"
                        if mode == "Usar GPS do Navegador":
                            return lat, lon, status_text
                        return lat, lon, info_localizacao.value
                except Exception:
                    pass
                fallback_msg = "⚠️ GPS Indisponível (Usando BH Centro)"
                if mode == "Usar GPS do Navegador":
                    return -19.9191, -43.9386, fallback_msg
                return -19.9191, -43.9386, info_localizacao.value

            gps_hidden.change(
                handle_gps_payload,
                inputs=[gps_hidden, modo_localizacao],
                outputs=[gps_lat, gps_lon, info_localizacao]
            )

            # 2. Obter Fuso Horário do Navegador
            tz_hidden.change(
                fn=lambda tz: tz or "America/Sao_Paulo",
                inputs=[tz_hidden],
                outputs=[browser_timezone]
            )

            # Carrega os scripts do navegador assim que o bloco Blocks é carregado
            demo.load(fn=None, outputs=[gps_hidden], js=js_gps)
            demo.load(fn=None, outputs=[tz_hidden], js=js_tz)

        demo.launch(css=custom_css, theme=gr.themes.Soft(primary_hue="amber", neutral_hue="slate"), **kwargs)
