
"""Estado e replanejamento de uma viagem em andamento."""

from dataclasses import dataclass, field
from math import isfinite

from agente_ia.recomendacao import recomendar_atracoes
from nextrip_base import carregar_pontos, validar_matriz
from nextrip_arquitetura.servicos import RoteiroService


@dataclass
class EstadoViagem:
    local_atual_id: str
    minutos_restantes: int
    ids_planejados: list[str]
    ids_concluidos: list[str] = field(default_factory=list)
    ids_indisponiveis: list[str] = field(default_factory=list)

    def concluir_visita(self, poi_id: str, minutos_gastos: int):
        if poi_id not in self.ids_planejados:
            raise ValueError("A atracao nao esta no roteiro atual.")

        if poi_id in self.ids_concluidos:
            raise ValueError("Atracao ja concluida.")

        if poi_id in self.ids_indisponiveis:
            raise ValueError("Atracao indisponivel.")

        if (
            type(minutos_gastos) is not int
            or not 0 <= minutos_gastos <= self.minutos_restantes
        ):
            raise ValueError("Tempo gasto invalido.")

        self.ids_concluidos.append(poi_id)
        self.local_atual_id = poi_id
        self.minutos_restantes -= minutos_gastos

    def bloquear_atracao(self, poi_id: str):
        if poi_id not in self.ids_planejados:
            raise ValueError("A atracao nao esta no roteiro atual.")

        if poi_id in self.ids_concluidos:
            raise ValueError("Visita ja concluida.")

        if poi_id not in self.ids_indisponiveis:
            self.ids_indisponiveis.append(poi_id)


def replanejar_restante(
    estado: EstadoViagem,
    preferencias: dict,
    catalogo_arquivo,
    matriz,
    paradas: int = 2,
    alpha: float = 0.8,
    segundos: int = 2,
):
    """Recalcula apenas as visitas ainda elegiveis."""

    if type(paradas) is not int or paradas <= 0:
        raise ValueError("Numero de paradas invalido.")

    if type(segundos) is not int or segundos <= 0:
        raise ValueError("Tempo de busca invalido.")

    if (
        type(alpha) not in (int, float)
        or not isfinite(alpha)
        or not 0 <= alpha <= 1
    ):
        raise ValueError("Alpha invalido.")

    if (
        type(estado.minutos_restantes) is not int
        or estado.minutos_restantes < 0
    ):
        raise ValueError("Tempo restante invalido.")

    # 1. Consultar os pontos originais das POCs
    _, pontos = carregar_pontos(catalogo_arquivo)
    validar_matriz(matriz, len(pontos))

    indice_por_id = {
        ponto["id"]: i
        for i, ponto in enumerate(pontos)
    }

    excluidos = set(
        estado.ids_concluidos + estado.ids_indisponiveis
    )
    excluidos.add(estado.local_atual_id)

    if not excluidos.issubset(indice_por_id):
        raise ValueError("IDs inexistentes no catalogo.")

    if (
        set(estado.ids_concluidos)
        & set(estado.ids_indisponiveis)
    ):
        raise ValueError("Visita concluida e indisponivel.")

    if estado.local_atual_id in estado.ids_indisponiveis:
        raise ValueError("Local atual indisponivel.")

    # 2. Local atual passa a ser a origem da nova rota
    indices = [indice_por_id[estado.local_atual_id]] + [
        i for i in range(1, len(pontos))
        if pontos[i]["id"] not in excluidos
    ]

    if len(indices) == 1 or estado.minutos_restantes == 0:
        return {"status": "sem_opcoes", "roteiro": None}

    origem = dict(pontos[indices[0]])
    origem["duracao_min"] = 0

    pontos_restantes = [origem] + [
        pontos[i] for i in indices[1:]
    ]

    # 3. Redimensionar a matriz de deslocamento
    matriz_restante = [
        [matriz[i][j] for j in indices]
        for i in indices
    ]

    # 4. Recalcular afinidades com a POC 1
    ranking = recomendar_atracoes(
        preferencias=preferencias,
        catalogo_arquivo=catalogo_arquivo,
        top=len(pontos) - 1,
    )["ranking"]

    scores_por_id = {
        item["id"]: item["score"]
        for item in ranking
    }

    def buscar_afinidades(
        _catalogo, _perfil, metrica="cosseno"
    ):
        if metrica != "cosseno":
            raise ValueError("Metrica nao suportada.")
        return scores_por_id

    # 5. Reutilizar o otimizador da POC 3
    servico = RoteiroService()

    max_paradas = min(paradas, len(indices) - 1)

    for quantidade in range(max_paradas, 0, -1):
        try:
            resultado = servico.gerar_roteiro_otimizado(
                pontos=pontos_restantes,
                matriz=matriz_restante,
                catalogo_arquivo=catalogo_arquivo,
                perfil_arquivo=None,
                paradas=quantidade,
                limite=estado.minutos_restantes,
                pesos=(alpha,),
                referencia=240,
                segundos=segundos,
                afinidades=buscar_afinidades,
            )

        except RuntimeError as erro:
            if "não encontrou solução viável" in str(erro):
                continue
            raise

        roteiro = resultado["resultados"][0]

        escolhidos = {
            atracao["id"]
            for atracao in roteiro["atracoes"]
        }

        # 6. Validar a nova rota
        if (
            not roteiro["restricoes_validadas"]
            or roteiro["total_min"] > estado.minutos_restantes
            or escolhidos & excluidos
            or roteiro["ids"][0] != estado.local_atual_id
            or roteiro["ids"][-1] != estado.local_atual_id
        ):
            raise AssertionError(
                "Roteiro replanejado invalido."
            )

        # Atualizar apenas as atividades futuras
        estado.ids_planejados = [
            item["id"]
            for item in roteiro["atracoes"]
        ]

        return {
            "status": "ok",
            "paradas_planejadas": quantidade,
            "ids_concluidos_preservados": list(
                estado.ids_concluidos
            ),
            "roteiro": roteiro,
        }

    return {
        "status": "sem_solucao_encontrada",
        "roteiro": None,
    }
