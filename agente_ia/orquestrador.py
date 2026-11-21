
DIMENSOES = {
    "cultura",
    "historia",
    "gastronomia",
    "natureza",
    "compras",
    "vida_noturna",
}


def planejar_viagem(pedido, recomendar, otimizar):
    """
    Coordena a recomendacao e a otimizacao de um roteiro.

    recomendar: funcao que seleciona atracoes candidatas.
    otimizar: funcao que organiza o itinerario.
    """

    destino = pedido.get("destino")
    duracao = pedido.get("duracao_minutos")
    preferencias = pedido.get("preferencias")

    if not isinstance(destino, str) or not destino.strip():
        raise ValueError("Informe um destino valido.")

    if type(duracao) is not int or duracao <= 0:
        raise ValueError("A duracao deve ser positiva.")

    if not isinstance(preferencias, dict):
        raise ValueError("Informe as preferencias do viajante.")

    if set(preferencias) != DIMENSOES:
        raise ValueError("As seis dimensoes sao obrigatorias.")

    for valor in preferencias.values():
        if type(valor) not in (int, float) or not 0 <= valor <= 1:
            raise ValueError("As preferencias devem estar entre 0 e 1.")

    # Etapa 1: obter atracoes recomendadas
    candidatas = recomendar(destino, preferencias)

    # Etapa 2: organizar as atracoes no tempo disponivel
    roteiro = otimizar(candidatas, duracao)

    return {
        "destino": destino,
        "duracao_limite_minutos": duracao,
        "roteiro": roteiro,
    }



from math import isfinite

from agente_ia.recomendacao import (
    RepositorioPerfilEmMemoria,
    recomendar_atracoes,
)
from nextrip_arquitetura.servicos import (
    RecomendacaoIA,
    RoteiroService,
)
from nextrip_base import carregar_pontos, validar_matriz


def planejar_com_pocs(
    preferencias,
    catalogo_arquivo,
    matriz,
    limite_minutos=360,
    paradas=3,
    alpha=0.8,
    segundos=2,
):
    """
    Coordena recomendacao e otimizacao usando as POCs.

    Se nao encontrar uma rota com o numero solicitado
    de paradas, tenta novamente com menos paradas.
    """

    if type(limite_minutos) is not int or limite_minutos <= 0:
        raise ValueError("Limite de tempo invalido.")

    if type(paradas) is not int or paradas < 1:
        raise ValueError("Numero de paradas invalido.")

    if (
        type(alpha) not in (int, float)
        or not isfinite(alpha)
        or not 0 <= alpha <= 1
    ):
        raise ValueError("Alpha deve estar entre 0 e 1.")

    if type(segundos) is not int or segundos < 1:
        raise ValueError("Tempo do solver invalido.")

    # 1. Carregar e validar os pontos de interesse
    _, pontos = carregar_pontos(catalogo_arquivo)
    validar_matriz(matriz, len(pontos))

    if paradas >= len(pontos):
        raise ValueError("Paradas excedem o catalogo.")

    # 2. Executar a recomendacao personalizada
    recomendacoes = recomendar_atracoes(
        preferencias=preferencias,
        catalogo_arquivo=catalogo_arquivo,
        top=5,
    )

    # 3. Preparar o recomendador da POC
    repositorio = RepositorioPerfilEmMemoria({
        "nome": "Perfil dinamico",
        "vetor": dict(preferencias),
    })

    recomendador = RecomendacaoIA(
        repositorio=repositorio
    )

    servico = RoteiroService(
        recomendacao=recomendador
    )

    # 4. Tentar gerar um roteiro viavel
    for quantidade in range(paradas, 0, -1):
        try:
            resultado = servico.gerar_roteiro_otimizado(
                pontos=pontos,
                matriz=matriz,
                catalogo_arquivo=catalogo_arquivo,
                perfil_arquivo=None,
                paradas=quantidade,
                limite=limite_minutos,
                pesos=(alpha,),
                referencia=240,
                segundos=segundos,
            )

        except RuntimeError as erro:
            if "não encontrou solução viável" in str(erro):
                continue
            raise

        cenario = resultado["resultados"][0]

        if (
            not cenario["restricoes_validadas"]
            or cenario["total_min"] > limite_minutos
        ):
            raise AssertionError("Roteiro invalido.")

        return {
            "status": "ok",
            "paradas_solicitadas": paradas,
            "paradas_planejadas": quantidade,
            "ajuste_automatico": quantidade < paradas,
            "ranking": recomendacoes["ranking"],
            "roteiro": cenario,
        }

    return {
        "status": "sem_solucao_encontrada",
        "paradas_solicitadas": paradas,
        "ranking": recomendacoes["ranking"],
        "mensagem": (
            "Nenhuma solucao encontrada com os limites "
            "e o tempo de busca configurados."
        ),
    }
