
from pathlib import Path

from agente_ia.controlador import AgenteNexTrip
from agente_ia.ferramentas_llm import executar_chamada
from nextrip_base import carregar_pontos


BASE = Path(__file__).resolve().parents[1]
CATALOGO = BASE / "dados" / "catalogo_teste.json"

_, pontos = carregar_pontos(CATALOGO)

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

agente = AgenteNexTrip(
    preferencias=preferencias,
    catalogo_arquivo=CATALOGO,
    matriz=matriz,
)

# 1. Simular pedido de geracao de roteiro
resposta = executar_chamada(
    agente,
    {
        "name": "gerar_roteiro",
        "arguments": {
            "limite_minutos": 360,
            "paradas": 3,
        },
    },
)

assert resposta["resultado"]["status"] == "ok"

atracoes = resposta["resultado"]["roteiro"]["atracoes"]
primeira, segunda = atracoes[:2]

print("Roteiro inicial gerado: OK")

# 2. Simular conclusao de uma visita
chamada = {
    "name": "concluir_visita",
    "arguments": {
        "poi_id": primeira["id"],
        "minutos_gastos": 60,
    },
}

# A chamada nao deve executar sem confirmacao
pendente = executar_chamada(agente, chamada)

assert pendente["status"] == "confirmacao_pendente"
assert agente.estado.ids_concluidos == []

print("Confirmacao solicitada: OK")

# Simular confirmacao feita pelo usuario
executar_chamada(
    agente,
    chamada,
    confirmado_pelo_usuario=True,
)

assert primeira["id"] in agente.estado.ids_concluidos

print("Visita confirmada: OK")

# 3. Bloquear uma atracao com confirmacao
executar_chamada(
    agente,
    {
        "name": "bloquear_atracao",
        "arguments": {
            "poi_id": segunda["id"],
        },
    },
    confirmado_pelo_usuario=True,
)

# 4. Replanejar
replanejado = executar_chamada(
    agente,
    {
        "name": "replanejar_roteiro",
        "arguments": {
            "paradas": 2,
        },
    },
    confirmado_pelo_usuario=True,
)

assert replanejado["resultado"]["status"] == "ok"

novo = replanejado["resultado"]["roteiro"]

assert primeira["id"] not in novo["ids"][1:-1]
assert segunda["id"] not in novo["ids"]

print("Replanejamento validado: OK")

# 5. Testar uma ferramenta nao autorizada
try:
    executar_chamada(
        agente,
        {
            "name": "executar_codigo",
            "arguments": {},
        },
    )
except ValueError:
    print("Ferramenta desconhecida bloqueada: OK")
else:
    raise AssertionError("Ferramenta indevida aceita.")

# 6. Testar parametros invalidos
try:
    executar_chamada(
        agente,
        {
            "name": "replanejar_roteiro",
            "arguments": {
                "paradas": "cinco",
            },
        },
    )
except ValueError:
    print("Parametros invalidos bloqueados: OK")
else:
    raise AssertionError("Parametros invalidos aceitos.")

assert len(agente.historico) == 4

print("\nTESTE DAS FERRAMENTAS LLM: OK")
