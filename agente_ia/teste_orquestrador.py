
from pathlib import Path

from agente_ia.orquestrador import planejar_com_pocs
from nextrip_base import carregar_pontos


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

# Matriz simulada, usada somente neste teste
n = len(pontos)

matriz = [
    [
        0 if i == j else 8 + abs(i - j) * 3
        for j in range(n)
    ]
    for i in range(n)
]

preferencias = {
    "cultura": 1.0,
    "historia": 1.0,
    "gastronomia": 0.2,
    "natureza": 0.0,
    "compras": 0.0,
    "vida_noturna": 0.0,
}


# Testar limites diferentes
for limite in [360, 100, 40]:
    print(f"\n=== CENARIO: {limite} MINUTOS ===")

    resposta = planejar_com_pocs(
        preferencias=preferencias,
        catalogo_arquivo=CATALOGO,
        matriz=matriz,
        limite_minutos=limite,
        paradas=3,
    )

    print("Status:", resposta["status"])

    if resposta["status"] == "ok":
        roteiro = resposta["roteiro"]

        assert roteiro["total_min"] <= limite
        assert roteiro["restricoes_validadas"]
        assert len(roteiro["atracoes"]) == resposta[
            "paradas_planejadas"
        ]

        print(
            "Paradas planejadas:",
            resposta["paradas_planejadas"]
        )
        print(
            "Ajuste automatico:",
            resposta["ajuste_automatico"]
        )
        print("Sequencia:", roteiro["sequencia"])
        print("Tempo total:", roteiro["total_min"])
    else:
        print(resposta["mensagem"])

print("\nTESTE DO ORQUESTRADOR FINALIZADO")
