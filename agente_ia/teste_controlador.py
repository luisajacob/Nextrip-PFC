
from pathlib import Path

from agente_ia.controlador import AgenteNexTrip
from nextrip_base import carregar_pontos


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

# Matriz simulada, como nos testes anteriores
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

# Criar o agente
agente = AgenteNexTrip(
    preferencias=preferencias,
    catalogo_arquivo=CATALOGO,
    matriz=matriz,
)

# Acao 1: gerar roteiro
inicial = agente.executar(
    "gerar_roteiro",
    limite_minutos=360,
    paradas=3,
)

assert inicial["resultado"]["status"] == "ok"

atracoes = inicial["resultado"]["roteiro"]["atracoes"]
primeira, segunda = atracoes[:2]

print("\n=== ROTEIRO INICIAL ===")
print([item["nome"] for item in atracoes])

# Acao 2: concluir primeira visita
# Os 60 minutos representam o tempo decorrido informado.
agente.executar(
    "concluir_visita",
    poi_id=primeira["id"],
    minutos_gastos=60,
)

# Acao 3: bloquear segunda atracao
agente.executar(
    "bloquear_atracao",
    poi_id=segunda["id"],
)

# Acao 4: replanejar o restante
resposta = agente.executar(
    "replanejar_roteiro",
    paradas=2,
)

assert resposta["resultado"]["status"] == "ok"

novo = resposta["resultado"]["roteiro"]
estado = resposta["estado"]

assert primeira["id"] in estado["ids_concluidos"]
assert segunda["id"] in estado["ids_indisponiveis"]
assert primeira["id"] not in novo["ids"][1:-1]
assert segunda["id"] not in novo["ids"]
assert novo["total_min"] <= estado["minutos_restantes"]

print("\n=== ROTEIRO REPLANEJADO ===")
for nome in novo["sequencia"]:
    print(" ->", nome)

print("\n=== ESTADO ATUAL ===")
print("Tempo restante:", estado["minutos_restantes"])
print("Visitas concluidas:", estado["ids_concluidos"])
print("Atracoes bloqueadas:", estado["ids_indisponiveis"])

# Testar a protecao contra acoes desconhecidas
try:
    agente.executar("acao_inexistente")
except ValueError:
    print("\nAcao desconhecida bloqueada corretamente.")
else:
    raise AssertionError("Acao desconhecida foi aceita.")

# Verificar historico de decisoes
assert len(agente.historico) == 4

print("\n=== HISTORICO DE ACOES ===")
for evento in agente.historico:
    print(evento)

print("\nTESTE DO CONTROLADOR: OK")
