
"""Teste de integracao entre horarios OSM e planejador."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from nextrip_base import carregar_pontos
from agente_ia.disponibilidade import (
    planejar_verificando_horarios,
)
from agente_ia.provedor_osm import ProvedorHorariosOSM


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

# Matriz simulada das etapas anteriores
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

# Primeiro usamos apenas os horarios cadastrados localmente
provedor = ProvedorHorariosOSM(
    pontos,
    fuso="America/Sao_Paulo",
)

inicio = datetime(
    2026, 11, 24, 9, 0,
    tzinfo=ZoneInfo("America/Sao_Paulo"),
)

resultado = planejar_verificando_horarios(
    preferencias=preferencias,
    catalogo_arquivo=CATALOGO,
    matriz=matriz,
    inicio_viagem=inicio,
    consultar_disponibilidade=provedor,
    limite_minutos=360,
    paradas=3,
)

print("\n=== INTEGRACAO DE HORARIOS NEXTRIP ===")
print("Status:", resultado["status"])
print("Fonte: catalogo OSM local")

roteiro = resultado["roteiro"]

if roteiro is not None:
    assert roteiro["restricoes_validadas"]
    assert roteiro["total_min"] <= 360

    print("\nRoteiro gerado:")

    for nome in roteiro["sequencia"]:
        print(" ->", nome)

    print("\nDisponibilidade das atracoes:")

    for verificacao in resultado["verificacoes"]:
        print(
            verificacao["nome"],
            "|", verificacao["status"],
            "|", verificacao["fonte"],
        )

        assert verificacao["status"] != "fechado"

    if resultado["status"] == "verificacao_pendente":
        print(
            "\nATENCAO: Existem horarios nao confirmados."
        )

    print("\nINTEGRACAO EXECUTADA: OK")

else:
    print(
        "\nNenhum roteiro encontrado dentro das "
        "restricoes deste teste."
    )
    print("INTEGRACAO: SEM ROTEIRO")


