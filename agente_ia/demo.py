
import json

from agente_ia.orquestrador import planejar_viagem


# Dados ficticios apenas para testar a comunicacao
def recomendar_teste(destino, preferencias):
    return [
        {"nome": "Museu ficticio", "duracao_minutos": 90},
        {"nome": "Parque ficticio", "duracao_minutos": 120},
        {"nome": "Centro cultural ficticio", "duracao_minutos": 60},
    ]


def otimizar_teste(atracoes, duracao_limite):
    roteiro = []
    tempo_usado = 0

    for atracao in atracoes:
        duracao = atracao["duracao_minutos"]

        if tempo_usado + duracao <= duracao_limite:
            roteiro.append(atracao)
            tempo_usado += duracao

    return roteiro


pedido = {
    "destino": "Sao Paulo",
    "duracao_minutos": 180,
    "preferencias": {
        "cultura": 0.9,
        "historia": 0.8,
        "gastronomia": 0.7,
        "natureza": 0.3,
        "compras": 0.2,
        "vida_noturna": 0.1,
    },
}

resultado = planejar_viagem(
    pedido,
    recomendar_teste,
    otimizar_teste,
)

print(json.dumps(resultado, indent=2, ensure_ascii=False))
