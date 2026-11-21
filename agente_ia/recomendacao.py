
"""Adaptador para usar a POC 1 com preferencias dinamicas."""

import math

from nextrip_base import DIMENSOES
from nextrip_arquitetura.repositorios import RepositorioJSON
from nextrip_arquitetura.servicos import RecomendacaoIA


class RepositorioPerfilEmMemoria(RepositorioJSON):
    """
    Permite fornecer um perfil diretamente em memoria,
    sem criar um arquivo JSON para cada usuario.
    """

    def __init__(self, perfil):
        self.perfil = perfil

    def carregar(self, caminho):
        if caminho is None:
            return self.perfil

        return super().carregar(caminho)


def recomendar_atracoes(preferencias, catalogo_arquivo, top=5):
    """
    Recomenda atracoes usando o algoritmo real da POC 1.

    preferencias: vetor de seis dimensoes do viajante.
    catalogo_arquivo: caminho do catalogo de atracoes.
    top: quantidade de atracoes retornadas.
    """

    if (
        not isinstance(preferencias, dict)
        or set(preferencias) != set(DIMENSOES)
    ):
        raise ValueError(
            f"Informe as seis dimensoes: {DIMENSOES}"
        )

    for dimensao, valor in preferencias.items():
        if (
            type(valor) not in (int, float)
            or not math.isfinite(valor)
            or not 0 <= valor <= 1
        ):
            raise ValueError(
                f"Preferencia invalida em {dimensao}: {valor}"
            )

    if not any(preferencias.values()):
        raise ValueError(
            "Informe ao menos um interesse maior que zero."
        )

    if type(top) is not int or top <= 0:
        raise ValueError(
            "top deve ser um numero inteiro positivo."
        )

    perfil = {
        "nome": "Perfil informado pelo usuario",
        "vetor": dict(preferencias),
    }

    repositorio = RepositorioPerfilEmMemoria(perfil)

    recomendador = RecomendacaoIA(
        repositorio=repositorio
    )

    resultado = recomendador.gerar_ranking(
        catalogo_arquivo=catalogo_arquivo,
        perfil_arquivo=None,
        metrica="cosseno",
    )

    resultado["ranking"] = resultado["ranking"][:top]

    return resultado
