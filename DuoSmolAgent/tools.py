import sys
import os
from smolagents import tool

# Adiciona o diretório principal ao PATH para importar o módulo original
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.tools import (
    buscar_restaurantes as _buscar_restaurantes,
    verificar_disponibilidade_duo as _verificar_disponibilidade_duo,
    obter_detalhes_restaurante as _obter_detalhes_restaurante,
    listar_cozinhas_disponiveis as _listar_cozinhas_disponiveis
)

# Estado global para a geolocalização e contexto de tempo atualizados via Gradio
user_location = {"lat": None, "lon": None}
time_context = ""

@tool
def obter_contexto_usuario() -> dict:
    """Retorna o contexto atual do usuário, incluindo sua localização GPS e data/hora atual.
    Use esta ferramenta no início de qualquer raciocínio para saber a localização do usuário e o dia/hora de hoje.
    
    Returns:
        Um dicionário com as chaves 'latitude', 'longitude' e 'tempo_contexto'.
    """
    return {
        "latitude": user_location["lat"],
        "longitude": user_location["lon"],
        "tempo_contexto": time_context
    }

@tool
def buscar_restaurantes(bairro: str = None, cozinha: str = None, lat_usuario: float = None, lon_usuario: float = None, cidade: str = None) -> list:
    """Busca restaurantes ativos no Duo Gourmet filtrando por bairro, tipo de cozinha/culinária, cidade, e calcula a distância física se as coordenadas do usuário forem fornecidas.
    
    Args:
        bairro: Nome do bairro para filtrar (ex: "Savassi", "Pinheiros"). Opcional.
        cozinha: Tipo de culinária para filtrar (ex: "Italiana", "Japonesa"). Opcional.
        lat_usuario: Latitude GPS do usuário. Opcional.
        lon_usuario: Longitude GPS do usuário. Opcional.
        cidade: Nome da cidade ("Belo Horizonte" ou "São Paulo"). Opcional.
        
    Returns:
        Uma lista contendo até 5 restaurantes ordenados por relevância ou distância.
    """
    return _buscar_restaurantes(bairro=bairro, cozinha=cozinha, lat_usuario=lat_usuario, lon_usuario=lon_usuario, cidade=cidade)

@tool
def verificar_disponibilidade_duo(restaurant_name: str, dia_semana: str, refeicao: str, hora_usuario: str = None) -> dict:
    """Verifica se o benefício do Duo Gourmet é válido para um restaurante específico em um determinado dia da semana, período (almoço ou jantar) e horário opcional.
    
    Args:
        restaurant_name: Nome exato ou aproximado do restaurante.
        dia_semana: Dia da semana em português (ex: "Segunda-feira", "Sexta-feira", "Sábado").
        refeicao: Período da refeição, deve ser 'almoco' ou 'jantar'.
        hora_usuario: Horário opcional no formato 'HH:MM' para validar contra a faixa horária específica.
        
    Returns:
        Um dicionário com informações de disponibilidade ("disponivel", "horario_validacao", "mensagem").
    """
    return _verificar_disponibilidade_duo(restaurant_name=restaurant_name, dia_semana=dia_semana, refeicao=refeicao, hora_usuario=hora_usuario)

@tool
def obter_detalhes_restaurante(restaurant_name: str) -> dict:
    """Retorna os detalhes completos de um restaurante específico, como endereço, telefone, preço, nota e horário de funcionamento geral.
    
    Args:
        restaurant_name: Nome exato ou aproximado do restaurante.
        
    Returns:
        Um dicionário com as informações detalhadas do restaurante ou mensagem de erro.
    """
    return _obter_detalhes_restaurante(restaurant_name=restaurant_name)

@tool
def listar_cozinhas_disponiveis() -> list:
    """Lista todos os tipos de culinária/cozinha disponíveis na base de dados dos restaurantes parceiros.
    
    Returns:
        Uma lista de strings com os nomes das cozinhas em ordem alfabética.
    """
    return _listar_cozinhas_disponiveis()
