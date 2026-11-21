
from pathlib import Path

from agente_ia.recomendacao import recomendar_atracoes


BASE = Path(__file__).resolve().parents[1]

CATALOGO = BASE / "dados" / "catalogo_teste.json"


# Dois perfis diferentes para testar a personalizacao
perfis = {
    "Cultura e historia": {
        "cultura": 1.0,
        "historia": 1.0,
        "gastronomia": 0.2,
        "natureza": 0.0,
        "compras": 0.0,
        "vida_noturna": 0.0,
    },

    "Natureza": {
        "cultura": 0.0,
        "historia": 0.0,
        "gastronomia": 0.0,
        "natureza": 1.0,
        "compras": 0.0,
        "vida_noturna": 0.0,
    },
}


for nome, preferencias in perfis.items():

    resultado = recomendar_atracoes(
        preferencias=preferencias,
        catalogo_arquivo=CATALOGO,
        top=5,
    )

    print(f"\nPerfil: {nome}")

    for item in resultado["ranking"]:
        print(
            f"{item['score']:.4f} | "
            f"{item['nome']} | "
            f"{item['id']}"
        )
