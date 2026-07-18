import json
from pathlib import Path

# Carregamento Lazy da base de dados
_restaurantes_data = None

def get_restaurantes():
    global _restaurantes_data
    if _restaurantes_data is None:
        _restaurantes_data = []
        base_dir = Path(__file__).parent.parent
        
        # Carregar Belo Horizonte a partir da pasta data/
        bh_path = base_dir / "data" / "restaurantes_bh.json"
        try:
            if bh_path.exists():
                with open(bh_path, "r", encoding="utf-8") as f:
                    _restaurantes_data.extend(json.load(f))
        except Exception as e:
            print(f"Erro ao carregar {bh_path}: {e}")
            
        # Carregar São Paulo a partir da pasta data/
        sp_path = base_dir / "data" / "restaurantes_sp.json"
        try:
            if sp_path.exists():
                with open(sp_path, "r", encoding="utf-8") as f:
                    _restaurantes_data.extend(json.load(f))
        except Exception as e:
            print(f"Erro ao carregar {sp_path}: {e}")
            
    return _restaurantes_data
