
"""Controlador de acoes do agente NexTrip."""

from agente_ia.orquestrador import planejar_com_pocs
from agente_ia.estado_viagem import (
    EstadoViagem,
    replanejar_restante,
)


class AgenteNexTrip:
    """
    Executa somente acoes autorizadas e acompanha
    o estado da viagem em memoria.
    """

    ACOES_PERMITIDAS = {
        "gerar_roteiro": {"limite_minutos", "paradas"},
        "concluir_visita": {"poi_id", "minutos_gastos"},
        "bloquear_atracao": {"poi_id"},
        "replanejar_roteiro": {"paradas"},
    }

    def __init__(self, preferencias, catalogo_arquivo, matriz):
        self.preferencias = preferencias
        self.catalogo_arquivo = catalogo_arquivo
        self.matriz = matriz
        self.estado = None
        self.historico = []

    def resumo_estado(self):
        """Devolve o estado atual sem expor o objeto interno."""

        if self.estado is None:
            return None

        return {
            "local_atual_id": self.estado.local_atual_id,
            "minutos_restantes": self.estado.minutos_restantes,
            "ids_planejados": list(self.estado.ids_planejados),
            "ids_concluidos": list(self.estado.ids_concluidos),
            "ids_indisponiveis": list(
                self.estado.ids_indisponiveis
            ),
        }

    def executar(self, acao, **parametros):
        """Seleciona e executa uma ferramenta autorizada."""

        # 1. Validar qual acao foi solicitada
        if acao not in self.ACOES_PERMITIDAS:
            raise ValueError(f"Acao nao autorizada: {acao}")

        extras = (
            set(parametros)
            - self.ACOES_PERMITIDAS[acao]
        )

        if extras:
            raise ValueError(
                f"Parametros nao permitidos: {sorted(extras)}"
            )

        # 2. Geracao inicial do roteiro
        if acao == "gerar_roteiro":
            if self.estado is not None:
                raise ValueError(
                    "A viagem ja foi iniciada neste controlador."
                )

            limite = parametros.get("limite_minutos", 360)
            paradas = parametros.get("paradas", 3)

            resultado = planejar_com_pocs(
                preferencias=self.preferencias,
                catalogo_arquivo=self.catalogo_arquivo,
                matriz=self.matriz,
                limite_minutos=limite,
                paradas=paradas,
            )

            if resultado["status"] == "ok":
                roteiro = resultado["roteiro"]

                self.estado = EstadoViagem(
                    local_atual_id=roteiro["ids"][0],
                    minutos_restantes=limite,
                    ids_planejados=[
                        item["id"]
                        for item in roteiro["atracoes"]
                    ],
                )

            status = resultado["status"]

        else:
            # As demais acoes exigem uma viagem existente
            if self.estado is None:
                raise ValueError(
                    "Gere um roteiro antes de executar esta acao."
                )

            # 3. Registrar uma visita concluida
            if acao == "concluir_visita":
                self.estado.concluir_visita(
                    poi_id=parametros["poi_id"],
                    minutos_gastos=parametros["minutos_gastos"],
                )

                resultado = {
                    "visita_concluida": parametros["poi_id"]
                }
                status = "ok"

            # 4. Registrar uma atracao indisponivel
            elif acao == "bloquear_atracao":
                self.estado.bloquear_atracao(
                    parametros["poi_id"]
                )

                resultado = {
                    "atracao_bloqueada": parametros["poi_id"]
                }
                status = "ok"

            # 5. Replanejar com o estado atualizado
            elif acao == "replanejar_roteiro":
                resultado = replanejar_restante(
                    estado=self.estado,
                    preferencias=self.preferencias,
                    catalogo_arquivo=self.catalogo_arquivo,
                    matriz=self.matriz,
                    paradas=parametros.get("paradas", 2),
                )

                status = resultado["status"]

        # 6. Registrar o resultado da acao
        self.historico.append({
            "acao": acao,
            "status": status,
        })

        return {
            "acao_executada": acao,
            "resultado": resultado,
            "estado": self.resumo_estado(),
        }
