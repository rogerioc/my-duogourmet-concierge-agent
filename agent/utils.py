import datetime
import unicodedata

def remover_acentos(texto: str) -> str:
    """
    Remove acentos de uma string e converte para minúsculas.
    Útil para normalização de buscas de bairros e culinárias.
    """
    if not texto:
        return ""
    texto_norm = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto_norm.lower().strip()

def normalizar_bairro(bairro: str) -> str:
    """
    Tratamentos específicos adicionais para bairros.
    """
    bairro = remover_acentos(bairro)
    # Substituições comuns (ex: Savassi x Funcionarios, Vila da Serra x Nova Lima)
    return bairro

def parse_time(time_str: str) -> datetime.time:
    """
    Converte uma string 'HH:MM' num objeto datetime.time.
    """
    try:
        hora, minuto = map(int, time_str.split(':'))
        return datetime.time(hora, minuto)
    except ValueError:
        return None

def is_time_in_range(time_to_check: datetime.time, start_time: datetime.time, end_time: datetime.time) -> bool:
    """
    Verifica se um horário está dentro de um intervalo,
    tratando corretamente casos onde o intervalo passa da meia-noite (ex: 18:00 às 02:00).
    """
    if start_time < end_time:
        return start_time <= time_to_check <= end_time
    else: # O intervalo cruza a meia-noite
        return time_to_check >= start_time or time_to_check <= end_time
