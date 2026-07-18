import json
import os
import math
from pathlib import Path
from common.utils import remover_acentos, parse_time, is_time_in_range
from common.database import get_restaurantes
from common.geo import calcular_distancia_haversine

def buscar_restaurantes(bairro: str = None, cozinha: str = None, lat_usuario: float = None, lon_usuario: float = None, cidade: str = None):
    """
    Busca restaurantes ativos no Duo Gourmet aplicando filtros e retornando os melhores.
    """
    db = get_restaurantes()
    resultados = []
    
    bairro_norm = remover_acentos(bairro) if bairro else None
    cozinha_norm = remover_acentos(cozinha) if cozinha else None
    
    cidade_norm = remover_acentos(cidade).lower().strip() if cidade else None
    if cidade_norm == "bh":
        cidade_norm = "belo-horizonte"
    elif cidade_norm == "sp":
        cidade_norm = "sao-paulo"
    if cidade_norm:
        cidade_norm = cidade_norm.replace(" ", "-")
    
    for r in db:
        status = r.get("google_business_status")
        if status and status not in ("OPERATIONAL", "UNKNOWN"):
            continue
            
        r_bairro = remover_acentos(r.get("neighborhood", ""))
        r_cozinha = remover_acentos(r.get("cuisine", ""))
        r_cidade = remover_acentos(r.get("city", "")).lower().replace(" ", "-")
        
        # Filtro de Cidade
        if cidade_norm and cidade_norm not in r_cidade:
            continue
            
        # Filtro de Bairro (busca parcial)
        if bairro_norm and bairro_norm not in r_bairro:
            continue
            
        # Filtro de Cozinha (busca parcial)
        if cozinha_norm and cozinha_norm not in r_cozinha:
            continue
            
        # Calcular distância se GPS fornecido
        r_lat = r.get("lat") or r.get("google_lat")
        r_lon = r.get("lon") or r.get("google_lng")
        
        distancia = float('inf')
        if lat_usuario and lon_usuario and r_lat and r_lon:
            distancia = calcular_distancia_haversine(lat_usuario, lon_usuario, r_lat, r_lon)
            
        # Extrair o slug correto
        r_url = r.get("url") or ""
        url_parts = [p for p in r_url.split("/") if p]
        slug = url_parts[-1] if url_parts else ""

        # Formatando retorno reduzido para economizar tokens
        resultados.append({
            "name": r.get("name"),
            "neighborhood": r.get("neighborhood"),
            "cuisine": r.get("cuisine"),
            "rating": r.get("google_rating"),
            "distance_km": round(distancia, 2) if distancia != float('inf') else None,
            "url": r_url,
            "slug": slug
        })
        
    # Ordenação: Prioridade para distância (se existir), depois por rating
    if lat_usuario and lon_usuario:
        resultados.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 9999, -(x["rating"] or 0)))
    else:
        resultados.sort(key=lambda x: -(x["rating"] or 0))
        
    return resultados[:5]

def verificar_disponibilidade_duo(restaurant_name: str, dia_semana: str, refeicao: str, hora_usuario: str = None):
    """
    Verifica se o benefício do Duo Gourmet é válido para um dia, período e (opcionalmente) horário específico.
    """
    db = get_restaurantes()
    name_norm = remover_acentos(restaurant_name)
    
    # Busca o restaurante exato ou aproximado
    restaurante_alvo = None
    for r in db:
        if remover_acentos(r.get("name", "")) == name_norm:
            restaurante_alvo = r
            break
            
    if not restaurante_alvo:
        return {"disponivel": False, "horario_validacao": None, "mensagem": f"Restaurante '{restaurant_name}' não encontrado."}
        
    schedule = restaurante_alvo.get("schedule", {})
    dia_info = schedule.get(dia_semana, {})
    if not isinstance(dia_info, dict):
         return {"disponivel": False, "horario_validacao": None, "mensagem": "Informação de horário não encontrada."}
         
    horario_faixa = dia_info.get(refeicao)
    
    if horario_faixa is None:
        return {"disponivel": False, "horario_validacao": None, "mensagem": f"Benefício não disponível no {refeicao} de {dia_semana}."}
        
    # Se houver hora do usuário, valida a faixa
    if hora_usuario and isinstance(horario_faixa, str) and "-" in horario_faixa:
        try:
            start_str, end_str = [x.strip() for x in horario_faixa.split("-")]
            start_time = parse_time(start_str)
            end_time = parse_time(end_str)
            check_time = parse_time(hora_usuario)
            
            if start_time and end_time and check_time:
                is_valid = is_time_in_range(check_time, start_time, end_time)
                if not is_valid:
                    return {
                        "disponivel": False, 
                        "horario_validacao": horario_faixa, 
                        "mensagem": f"Benefício disponível de {horario_faixa}, mas você quer ir às {hora_usuario}."
                    }
        except Exception:
            pass # Ignora erros de parse e prossegue confiando na string geral
            
    return {
        "disponivel": True, 
        "horario_validacao": horario_faixa,
        "mensagem": f"Benefício confirmado para {refeicao} de {dia_semana} ({horario_faixa})."
    }

def obter_detalhes_restaurante(restaurant_name: str):
    """
    Retorna os detalhes completos de um restaurante específico.
    """
    db = get_restaurantes()
    name_norm = remover_acentos(restaurant_name)
    
    for r in db:
        if remover_acentos(r.get("name", "")) == name_norm:
            r_url = r.get("url") or ""
            url_parts = [p for p in r_url.split("/") if p]
            slug = url_parts[-1] if url_parts else ""
            return {
                "name": r.get("name"),
                "cuisine": r.get("cuisine"),
                "neighborhood": r.get("neighborhood"),
                "address": r.get("address"),
                "description": r.get("description"),
                "google_rating": r.get("google_rating"),
                "google_reviews_count": r.get("google_reviews_count"),
                "google_price_level": r.get("google_price_level"),
                "google_maps_url": r.get("google_maps_url"),
                "phone": r.get("phone"),
                "website": r.get("website"),
                "schedule": r.get("schedule"),
                "url": r_url,
                "slug": slug
            }
    return {"erro": "Restaurante não encontrado."}

def listar_cozinhas_disponiveis():
    """
    Retorna uma lista com todas as culinárias disponíveis.
    """
    db = get_restaurantes()
    cozinhas = set()
    for r in db:
        c = r.get("cuisine")
        if c:
            cozinhas.add(c.strip())
    return sorted(list(cozinhas))
