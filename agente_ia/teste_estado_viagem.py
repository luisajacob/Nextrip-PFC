
from pathlib import Path

from agente_ia.estado_viagem import (
    EstadoViagem,
    replanejar_restante,
)
from agente_ia.orquestrador import planejar_com_pocs
from nextrip_base import carregar_pontos


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

# Matriz simulada usada nos testes anteriores
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

# 1. Gerar o roteiro original
primeiro_roteiro = planejar_com_pocs(
    preferencias=preferencias,
    catalogo_arquivo=CATALOGO,
    matriz=matriz,
    limite_minutos=360,
    paradas=3,
)

assert primeiro_roteiro["status"] == "ok"

roteiro = primeiro_roteiro["roteiro"]

primeira, segunda = roteiro["atracoes"][:2]

# 2. Inicializar o estado da viagem
estado = EstadoViagem(
    local_atual_id=roteiro["ids"][0],
    minutos_restantes=360,
    ids_planejados=[
        item["id"] for item in roteiro["atracoes"]
    ],
)

# 3. Simular a primeira visita concluida
# Consideramos 60 minutos consumidos neste exemplo.
estado.concluir_visita(
    poi_id=primeira["id"],
    minutos_gastos=60,
)

# 4. Simular indisponibilidade da segunda visita
estado.bloquear_atracao(segunda["id"])

# 5. Replanejar somente o restante
resposta = replanejar_restante(
    estado=estado,
    preferencias=preferencias,
    catalogo_arquivo=CATALOGO,
    matriz=matriz,
    paradas=2,
)

print("\n=== ESTADO DA VIAGEM NEXTRIP ===")
print("Visita concluida:", primeira["nome"])
print("Atracao indisponivel:", segunda["nome"])
print("Tempo restante:", estado.minutos_restantes)
print("Status:", resposta["status"])

assert resposta["status"] == "ok"

novo = resposta["roteiro"]

# 6. Validar o replanejamento
assert novo["ids"][0] == primeira["id"]
assert novo["ids"][-1] == primeira["id"]
assert primeira["id"] not in novo["ids"][1:-1]
assert segunda["id"] not in novo["ids"]
assert novo["total_min"] <= estado.minutos_restantes
assert estado.ids_concluidos == [primeira["id"]]

print("\nNova sequencia:")

for nome in novo["sequencia"]:
    print(" ->", nome)

print("\nTempo do novo roteiro:", novo["total_min"])
print("Visitas concluidas:", estado.ids_concluidos)
print("Atracoes bloqueadas:", estado.ids_indisponiveis)

print("\nTESTE DE ESTADO DA VIAGEM: OK")
