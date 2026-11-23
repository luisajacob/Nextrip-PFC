
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agente_ia.controlador import AgenteNexTrip
from agente_ia.monitoramento import verificar_proxima_visita
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


def criar_agente():
    agente = AgenteNexTrip(
        preferencias=preferencias,
        catalogo_arquivo=CATALOGO,
        matriz=matriz,
    )

    resposta = agente.executar(
        "gerar_roteiro",
        limite_minutos=360,
        paradas=3,
    )

    assert resposta["resultado"]["status"] == "ok"

    return agente


inicio = datetime(
    2026, 11, 24, 9, 0,
    tzinfo=timezone(timedelta(hours=-3)),
)

# CENARIO 1: detectar fechamento automaticamente
agente = criar_agente()

id_bloqueado = agente.estado.ids_planejados[0]


def provedor_teste(ponto, chegada, saida):
    if ponto["id"] == id_bloqueado:
        return {
            "status": "fechado",
            "fonte": "simulacao",
        }

    return {
        "status": "aberto",
        "fonte": "simulacao",
    }


resultado = verificar_proxima_visita(
    agente=agente,
    momento_atual=inicio,
    consultar_disponibilidade=provedor_teste,
)

assert resultado["status"] == "replanejado"
assert id_bloqueado in agente.estado.ids_indisponiveis
assert id_bloqueado not in agente.estado.ids_planejados

print("\n=== REPLANEJAMENTO AUTOMATICO ===")
print("Status:", resultado["status"])
print("Proxima atracao:", resultado["proxima_atracao"])
print("Atracao bloqueada:", id_bloqueado)

for item in resultado["verificacoes"]:
    print(item["nome"], "|", item["status"])

# CENARIO 2: nenhuma informacao disponivel
agente_desconhecido = criar_agente()


def provedor_desconhecido(ponto, chegada, saida):
    return {
        "status": "desconhecido",
        "fonte": "simulacao",
    }


pendente = verificar_proxima_visita(
    agente=agente_desconhecido,
    momento_atual=inicio,
    consultar_disponibilidade=provedor_desconhecido,
)

assert pendente["status"] == "verificacao_pendente"
assert agente_desconhecido.estado.ids_indisponiveis == []

print("\n=== DISPONIBILIDADE DESCONHECIDA ===")
print("Status:", pendente["status"])
print("Nenhuma atracao bloqueada: OK")

print("\nTESTE DE MONITORAMENTO: OK")
