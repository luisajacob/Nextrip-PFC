
from pathlib import Path

from agente_ia.replanejamento import (
    replanejar_por_indisponibilidade,
)
from nextrip_base import carregar_pontos


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

# Mesma matriz simulada dos testes anteriores
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

# Simular indisponibilidade da primeira atracao
atracao_bloqueada = pontos[1]
id_bloqueado = atracao_bloqueada["id"]

print("\n=== IMPREVISTO IDENTIFICADO ===")
print("Atracao indisponivel:", atracao_bloqueada["nome"])
print("ID:", id_bloqueado)

for limite in [360, 100, 40]:
    print(f"\n=== REPLANEJAMENTO: {limite} MINUTOS ===")

    resultado = replanejar_por_indisponibilidade(
        preferencias=preferencias,
        catalogo_arquivo=CATALOGO,
        matriz=matriz,
        ids_indisponiveis=[id_bloqueado],
        limite_minutos=limite,
        paradas=3,
    )

    print("Status:", resultado["status"])

    if resultado["status"] == "ok":
        roteiro = resultado["roteiro"]

        # Garantir que a atracao bloqueada nao foi usada
        assert id_bloqueado not in roteiro["ids"]

        # Garantir que o tempo disponivel foi respeitado
        assert roteiro["total_min"] <= limite
        assert roteiro["restricoes_validadas"]

        assert len(roteiro["atracoes"]) == resultado[
            "paradas_planejadas"
        ]

        print("Nova sequencia:")

        for nome in roteiro["sequencia"]:
            print(" ->", nome)

        print(
            "Paradas planejadas:",
            resultado["paradas_planejadas"],
        )
        print(
            "Tempo total:",
            roteiro["total_min"],
        )

        print("Atracao bloqueada foi excluida: SIM")

    else:
        print(resultado.get(
            "mensagem",
            "Nao existem atracoes disponiveis.",
        ))

print("\nTESTE DE REPLANEJAMENTO FINALIZADO")
