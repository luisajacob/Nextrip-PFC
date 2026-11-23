
"""Verificacao automatica da proxima atracao do NexTrip."""

from datetime import datetime, timedelta

from agente_ia.controlador import AgenteNexTrip
from nextrip_base import carregar_pontos, validar_matriz


def verificar_proxima_visita(
    agente: AgenteNexTrip,
    momento_atual: datetime,
    consultar_disponibilidade,
):
    """
    Verifica a proxima visita antes do deslocamento.

    Caso a atracao esteja fechada, bloqueia e
    recalcula o restante do roteiro automaticamente.
    """

    if agente.estado is None:
        raise ValueError("Nenhuma viagem foi planejada.")

    if (
        not isinstance(momento_atual, datetime)
        or momento_atual.tzinfo is None
        or momento_atual.utcoffset() is None
    ):
        raise ValueError("Informe data e hora com fuso.")

    if not callable(consultar_disponibilidade):
        raise TypeError("Provedor de horarios invalido.")

    _, pontos = carregar_pontos(agente.catalogo_arquivo)
    validar_matriz(agente.matriz, len(pontos))

    indice_por_id = {
        ponto["id"]: i
        for i, ponto in enumerate(pontos)
    }

    verificacoes = []
    houve_replanejamento = False

    # O limite impede repeticoes infinitas
    for _ in range(len(pontos)):

        estado = agente.estado

        concluidos = set(estado.ids_concluidos)
        bloqueados = set(estado.ids_indisponiveis)

        pendentes = [
            poi_id
            for poi_id in estado.ids_planejados
            if poi_id not in concluidos
            and poi_id not in bloqueados
        ]

        if not pendentes:
            return {
                "status": "sem_visitas_pendentes",
                "replanejado": houve_replanejamento,
                "verificacoes": verificacoes,
            }

        proximo_id = pendentes[0]
        atual_id = estado.local_atual_id

        if (
            atual_id not in indice_por_id
            or proximo_id not in indice_por_id
        ):
            raise ValueError("POI nao encontrado no catalogo.")

        i = indice_por_id[atual_id]
        j = indice_por_id[proximo_id]

        ponto = pontos[j]

        # Estimar a chegada a partir da posicao atual
        deslocamento = agente.matriz[i][j]

        chegada = momento_atual + timedelta(
            minutes=deslocamento
        )

        saida = chegada + timedelta(
            minutes=ponto["duracao_min"]
        )

        # Consultar a disponibilidade prevista
        try:
            resposta = consultar_disponibilidade(
                ponto, chegada, saida
            )

            if not isinstance(resposta, dict):
                raise ValueError("Resposta invalida.")

            status = resposta.get(
                "status", "desconhecido"
            )

            if status not in {
                "aberto", "fechado", "desconhecido"
            }:
                raise ValueError("Status invalido.")

            fonte = resposta.get(
                "fonte", "nao_informada"
            )

        except Exception:
            status = "desconhecido"
            fonte = "falha_na_consulta"

        verificacoes.append({
            "poi_id": proximo_id,
            "nome": ponto["nome"],
            "status": status,
            "fonte": fonte,
            "chegada_prevista": chegada.isoformat(),
            "saida_prevista": saida.isoformat(),
        })

        # Caso esteja previsto como aberto
        if status == "aberto":
            return {
                "status": (
                    "replanejado"
                    if houve_replanejamento
                    else "seguir_roteiro"
                ),
                "proxima_atracao": ponto["nome"],
                "replanejado": houve_replanejamento,
                "verificacoes": verificacoes,
            }

        # Consulta inconclusiva: nao bloquear
        if status == "desconhecido":
            return {
                "status": "verificacao_pendente",
                "proxima_atracao": ponto["nome"],
                "replanejado": houve_replanejamento,
                "verificacoes": verificacoes,
                "aviso": (
                    "Nao foi possivel confirmar o horario."
                ),
            }

        # Fechamento identificado por fonte de horarios
        agente.executar(
            "bloquear_atracao",
            poi_id=proximo_id,
        )

        # Replanejar somente as visitas pendentes
        novo = agente.executar(
            "replanejar_roteiro",
            paradas=len(pendentes),
        )

        houve_replanejamento = True

        if novo["resultado"]["status"] != "ok":
            return {
                "status": "sem_solucao_encontrada",
                "replanejado": True,
                "verificacoes": verificacoes,
                "aviso": (
                    "Nao foi encontrado um roteiro "
                    "alternativo dentro das restricoes."
                ),
            }

        # Continua o loop e verifica a nova proxima visita

    return {
        "status": "limite_verificacoes",
        "replanejado": houve_replanejamento,
        "verificacoes": verificacoes,
    }
