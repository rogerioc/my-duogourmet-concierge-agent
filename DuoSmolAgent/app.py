import sys
import os
import yaml
from dotenv import load_dotenv
from smolagents import CodeAgent, HfApiModel

# Garante que a raiz do MyDuoConcierge está no PYTHONPATH para as importações das ferramentas originais
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar as ferramentas encapsuladas para o smolagents e variáveis de contexto
import tools as agent_tools
from Gradio_UI import GradioUI

# Carregar variáveis de ambiente a partir do .env local
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

api_key = os.getenv("HF_TOKEN")

# Carregar templates de prompt
prompts_path = os.path.join(os.path.dirname(__file__), "prompts.yaml")
with open(prompts_path, 'r', encoding='utf-8') as stream:
    prompt_templates = yaml.safe_load(stream)

# Configurar o modelo Qwen no Hugging Face Hub
model = HfApiModel(
    max_tokens=2096,
    temperature=0.4,
    model_id='Qwen/Qwen2.5-Coder-32B-Instruct',
    token=api_key,
    custom_role_conversions=None,
)

# Inicializar o CodeAgent com todas as ferramentas necessárias do DuoConcierge
agent = CodeAgent(
    model=model,
    tools=[
        agent_tools.buscar_restaurantes,
        agent_tools.verificar_disponibilidade_duo,
        agent_tools.obter_detalhes_restaurante,
        agent_tools.listar_cozinhas_disponiveis,
        agent_tools.obter_contexto_usuario,
    ],
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name="DuoConcierge",
    description="Um concierge de restaurantes integrado com o benefício do Duo Gourmet.",
    prompt_templates=prompt_templates
)

if __name__ == "__main__":
    GradioUI(agent).launch()
