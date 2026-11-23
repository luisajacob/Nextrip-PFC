
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agente_ia.disponibilidade import (
    planejar_verificando_horarios,
)
from nextrip_base import carregar_pontos


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

# Matriz experimental dos testes anteriores
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

# Atracao original Abertura, identificada pelo catalogo
id_bloqueado = pontos[1]["id"]

# Funcao que simula a resposta de uma API externa
def consultar_disponibilidade_teste(ponto, chegada, saida):
    if ponto["id"] == id_bloqueado:
        return {
            "status": "fechado",
            "fonte": "simulacao",
        }

    return {
        "status": "aberto",
        "fonte": "simulacao",
    }


inicio = datetime(
    2026, 11, 24, 9, 0,
    tzinfo=timezone(timedelta(hours=-3)),
)

print("\n=== VERIFICACAO AUTOMATICA ===")

resultado = planejar_verificando_horarios(
    preferencias=preferencias,
    catalogo_arquivo=CATALOGO,
    matriz=matriz,
    inicio_viagem=inicio,
    consultar_disponibilidade=consultar_disponibilidade_teste,
    limite_minutos=360,
    paradas=3,
)

print("Status:", resultado["status"])
print("Atracoes excluidas:", resultado["ids_excluidos"])

assert resultado["status"] == "ok"
assert id_bloqueado in resultado["ids_excluidos"]

roteiro = resultado["roteiro"]

assert id_bloqueado not in roteiro["ids"][1:-1]
assert roteiro["total_min"] <= 360
assert roteiro["restricoes_validadas"]

print("\nRoteiro recalculado automaticamente:")

for nome in roteiro["sequencia"]:
    print(" ->", nome)

print("\nVerificacoes realizadas:")

for item in resultado["verificacoes"]:
    print(
        item["nome"],
        "|", item["status"],
        "|", item["fonte"],
        "| chegada:", item["chegada_prevista"],
    )

# Verificar que disponibilidade desconhecida
# nao sera interpretada como local aberto
def consultar_desconhecido(ponto, chegada, saida):
    return {
        "status": "desconhecido",
        "fonte": "simulacao",
    }


pendente = planejar_verificando_horarios(
    preferencias=preferencias,
    catalogo_arquivo=CATALOGO,
    matriz=matriz,
    inicio_viagem=inicio,
    consultar_disponibilidade=consultar_desconhecido,
)

assert pendente["status"] == "verificacao_pendente"

print("\nDisponibilidade desconhecida tratada: OK")
print("TESTE DE DISPONIBILIDADE: OK")
