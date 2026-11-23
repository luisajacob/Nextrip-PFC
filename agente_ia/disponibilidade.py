
"""Verificacao automatica da disponibilidade de atracoes."""

from datetime import datetime, timedelta

from nextrip_base import carregar_pontos, validar_matriz
from agente_ia.replanejamento import (
    replanejar_por_indisponibilidade,
)


STATUS_VALIDOS = {
    "aberto",
    "fechado",
    "desconhecido",
}


def planejar_verificando_horarios(
    preferencias,
    catalogo_arquivo,
    matriz,
    inicio_viagem,
    consultar_disponibilidade,
    limite_minutos=360,
    paradas=3,
):
    """
    Gera um roteiro, verifica o horario previsto
    de cada visita e recalcula se houver fechamentos.

    consultar_disponibilidade deve receber:
       (ponto, chegada_prevista, saida_prevista)

    E retornar:
       {"status": "aberto|fechado|desconhecido",
        "fonte": "nome_do_provedor"}
    """

    if (
        not isinstance(inicio_viagem, datetime)
        or inicio_viagem.tzinfo is None
        or inicio_viagem.utcoffset() is None
    ):
        raise ValueError(
            "Informe data e hora com fuso horario."
        )

    if not callable(consultar_disponibilidade):
        raise TypeError(
            "Informe um consultor de disponibilidade."
        )

    # 1. Carregar os pontos originais das POCs
    _, pontos = carregar_pontos(catalogo_arquivo)
    validar_matriz(matriz, len(pontos))

    indices_por_id = {
        ponto["id"]: i
        for i, ponto in enumerate(pontos)
    }

    indisponiveis = set()

    # Cada nova tentativa deve excluir ao menos um POI
    for _ in range(len(pontos)):

        # 2. Gerar o roteiro com as POCs existentes
        resposta = replanejar_por_indisponibilidade(
            preferencias=preferencias,
            catalogo_arquivo=catalogo_arquivo,
            matriz=matriz,
            ids_indisponiveis=sorted(indisponiveis),
            limite_minutos=limite_minutos,
            paradas=paradas,
        )

        if resposta["status"] != "ok":
            return {
                "status": resposta["status"],
                "roteiro": None,
                "ids_excluidos": sorted(indisponiveis),
                "verificacoes": [],
            }

        roteiro = resposta["roteiro"]
        ids_rota = roteiro["ids"]

        tempo = inicio_viagem
        verificacoes = []
        novos_bloqueios = set()

        # 3. Examinar cada atracao do roteiro
        for posicao in range(1, len(ids_rota) - 1):

            id_anterior = ids_rota[posicao - 1]
            id_atual = ids_rota[posicao]

            i = indices_por_id[id_anterior]
            j = indices_por_id[id_atual]

            # Horario previsto de chegada
            tempo += timedelta(
                minutes=matriz[i][j]
            )

            chegada = tempo
            ponto = pontos[j]

            # Horario previsto do fim da visita
            fim = chegada + timedelta(
                minutes=ponto["duracao_min"]
            )

            tempo = fim

            # 4. Consultar a fonte de disponibilidade
            try:
                consulta = consultar_disponibilidade(
                    ponto,
                    chegada,
                    fim,
                )

                if not isinstance(consulta, dict):
                    raise ValueError("Resposta invalida.")

                situacao = consulta.get(
                    "status", "desconhecido"
                )

                fonte = consulta.get(
                    "fonte", "nao_informada"
                )

                if situacao not in STATUS_VALIDOS:
                    raise ValueError("Status invalido.")

            except Exception:
                # Falha na consulta nao significa aberto
                situacao = "desconhecido"
                fonte = "falha_na_consulta"

            verificacoes.append({
                "id": id_atual,
                "nome": ponto["nome"],
                "chegada_prevista": chegada.isoformat(),
                "saida_prevista": fim.isoformat(),
                "status": situacao,
                "fonte": fonte,
            })

            if situacao == "fechado":
                novos_bloqueios.add(id_atual)

        # 5. Se encontrou fechamento, recalcular
        if novos_bloqueios:
            indisponiveis.update(novos_bloqueios)
            continue

        # 6. Identificar informacoes nao confirmadas
        pendentes = [
            item for item in verificacoes
            if item["status"] == "desconhecido"
        ]

        return {
            "status": (
                "verificacao_pendente"
                if pendentes else "ok"
            ),
            "roteiro": roteiro,
            "ids_excluidos": sorted(indisponiveis),
            "verificacoes": verificacoes,
            "aviso": (
                "Algumas atracoes nao possuem "
                "disponibilidade confirmada."
                if pendentes else None
            ),
        }

    return {
        "status": "sem_solucao_encontrada",
        "roteiro": None,
        "ids_excluidos": sorted(indisponiveis),
        "verificacoes": [],
    }
