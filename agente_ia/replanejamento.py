
"""Replanejamento quando uma atracao fica indisponivel."""

from math import isfinite

from agente_ia.recomendacao import recomendar_atracoes
from nextrip_base import carregar_pontos, validar_matriz
from nextrip_arquitetura.servicos import RoteiroService


def replanejar_por_indisponibilidade(
    preferencias,
    catalogo_arquivo,
    matriz,
    ids_indisponiveis,
    limite_minutos=360,
    paradas=3,
    alpha=0.8,
    segundos=2,
):
    """Recalcula o roteiro removendo atracoes indisponiveis."""

    # 1. Validar os parametros recebidos
    if type(limite_minutos) is not int or limite_minutos <= 0:
        raise ValueError("Limite de tempo invalido.")

    if type(paradas) is not int or paradas <= 0:
        raise ValueError("Numero de paradas invalido.")

    if type(segundos) is not int or segundos <= 0:
        raise ValueError("Tempo de busca invalido.")

    if (
        type(alpha) not in (int, float)
        or not isfinite(alpha)
        or not 0 <= alpha <= 1
    ):
        raise ValueError("Alpha deve estar entre 0 e 1.")

    if (
        not isinstance(ids_indisponiveis, (list, tuple, set))
        or any(
            not isinstance(item, str) or not item.strip()
            for item in ids_indisponiveis
        )
    ):
        raise ValueError("Informe uma lista de IDs validos.")

    # 2. Carregar o catalogo e validar a matriz original
    _, pontos = carregar_pontos(catalogo_arquivo)
    validar_matriz(matriz, len(pontos))

    bloqueados = set(ids_indisponiveis)

    ids_validos = {p["id"] for p in pontos[1:]}
    desconhecidos = bloqueados - ids_validos

    if desconhecidos:
        raise ValueError(
            f"IDs nao encontrados: {sorted(desconhecidos)}"
        )

    # 3. Recalcular as afinidades com o perfil informado
    ranking = recomendar_atracoes(
        preferencias=preferencias,
        catalogo_arquivo=catalogo_arquivo,
        top=len(pontos) - 1,
    )["ranking"]

    afinidades_por_id = {
        item["id"]: item["score"]
        for item in ranking
    }

    # 4. Remover as atracoes indisponiveis
    # O indice zero representa o ponto de partida
    indices = [0] + [
        i for i in range(1, len(pontos))
        if pontos[i]["id"] not in bloqueados
    ]

    pontos_disponiveis = [pontos[i] for i in indices]

    # Filtrar linhas e colunas usando os mesmos indices
    matriz_disponivel = [
        [matriz[i][j] for j in indices]
        for i in indices
    ]

    if len(pontos_disponiveis) == 1:
        return {
            "status": "sem_atracoes_disponiveis",
            "ids_indisponiveis": sorted(bloqueados),
            "paradas_solicitadas": paradas,
            "roteiro": None,
        }

    # 5. Utilizar o otimizador existente da POC 3
    servico = RoteiroService()

    def afinidades_catalogo(
        _arquivo, _perfil, metrica="cosseno"
    ):
        if metrica != "cosseno":
            raise ValueError("Metrica nao suportada.")

        return afinidades_por_id

    # 6. Tentar o numero solicitado de paradas
    # e diminuir se nenhuma solucao for encontrada
    max_paradas = min(
        paradas,
        len(pontos_disponiveis) - 1,
    )

    for quantidade in range(max_paradas, 0, -1):
        try:
            resultado = servico.gerar_roteiro_otimizado(
                pontos=pontos_disponiveis,
                matriz=matriz_disponivel,
                catalogo_arquivo=catalogo_arquivo,
                perfil_arquivo=None,
                paradas=quantidade,
                limite=limite_minutos,
                pesos=(alpha,),
                referencia=240,
                segundos=segundos,
                afinidades=afinidades_catalogo,
            )

        except RuntimeError as erro:
            if "não encontrou solução viável" in str(erro):
                continue
            raise

        roteiro = resultado["resultados"][0]

        # 7. Verificar a validade do novo roteiro
        if (
            not roteiro["restricoes_validadas"]
            or roteiro["total_min"] > limite_minutos
            or bloqueados.intersection(roteiro["ids"])
        ):
            raise AssertionError(
                "Replanejamento produziu roteiro invalido."
            )

        return {
            "status": "ok",
            "ids_indisponiveis": sorted(bloqueados),
            "paradas_solicitadas": paradas,
            "paradas_planejadas": quantidade,
            "ajuste_automatico": quantidade < paradas,
            "roteiro": roteiro,
        }

    return {
        "status": "sem_solucao_encontrada",
        "ids_indisponiveis": sorted(bloqueados),
        "paradas_solicitadas": paradas,
        "roteiro": None,
        "mensagem": (
            "Nenhuma solucao encontrada dentro dos limites "
            "e do tempo de busca."
        ),
    }
