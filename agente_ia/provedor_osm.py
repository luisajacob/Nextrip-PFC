
"""Consulta horarios de funcionamento no OpenStreetMap."""

import re
from zoneinfo import ZoneInfo

import requests
from opening_hours import OpeningHours


URL_OVERPASS = "https://overpass-api.de/api/interpreter"


class ProvedorHorariosOSM:
    def __init__(self, pontos, fuso="America/Sao_Paulo"):
        self.fuso = ZoneInfo(fuso)

        # Tags ja existentes nos catalogos das POCs
        self.tags_por_id = {
            p["id"]: dict(p.get("tags_osm") or {})
            for p in pontos
        }

        self.fonte = "catalogo_osm"

    def atualizar_pela_api(self):
        """Busca tags OSM em uma unica consulta Overpass."""

        grupos = {"node": [], "way": [], "relation": []}

        for poi_id in self.tags_por_id:
            match = re.fullmatch(
                r"osm:(node|way|relation):([1-9][0-9]*)",
                poi_id,
            )
            if match:
                grupos[match.group(1)].append(match.group(2))

        partes = [
            f"{tipo}(id:{','.join(ids)});"
            for tipo, ids in grupos.items()
            if ids
        ]

        if not partes:
            return False

        consulta = (
            "[out:json][timeout:20];"
            "(" + "".join(partes) + ");out tags;"
        )

        try:
            resposta = requests.post(
                URL_OVERPASS,
                data={"data": consulta},
                headers={
                    "User-Agent": (
                        "NexTrip-TCC/0.1 "
                        "(https://github.com/brumenezes/Nextrip-PFC)"
                    ),
                },
                timeout=25,
            )
            resposta.raise_for_status()

            elementos = resposta.json()["elements"]
            if not isinstance(elementos, list):
                raise ValueError("Resposta Overpass invalida.")

            encontrados = {}

            for elemento in elementos:
                chave = (
                    f"osm:{elemento['type']}:{elemento['id']}"
                )

                if chave in self.tags_por_id:
                    encontrados[chave] = (
                        elemento.get("tags") or {}
                    )

            # Sem tag de horario significa desconhecido
            self.tags_por_id = {
                poi_id: encontrados.get(poi_id, {})
                for poi_id in self.tags_por_id
            }

            self.fonte = "overpass_api"
            return True

        
        except (requests.RequestException, ValueError, KeyError) as erro:
            self.ultimo_erro = (
                f"{type(erro).__name__}: {erro}"
            )

            self.fonte = "catalogo_osm_fallback"

            return False


    def __call__(self, ponto, chegada, saida):
        """Verifica toda a janela prevista da visita."""

        if (
            chegada.tzinfo is None
            or saida.tzinfo is None
            or saida <= chegada
        ):
            return {
                "status": "desconhecido",
                "fonte": self.fonte,
            }

        regra = self.tags_por_id.get(
            ponto["id"], {}
        ).get("opening_hours")

        if not regra:
            return {
                "status": "desconhecido",
                "fonte": self.fonte,
                "motivo": "horario_nao_cadastrado",
            }

        try:
            horario = OpeningHours(
                regra,
                timezone=self.fuso,
                country="BR",
            )

            chegada = chegada.astimezone(self.fuso)
            saida = saida.astimezone(self.fuso)

            if horario.is_unknown(chegada):
                status = "desconhecido"

            elif not horario.is_open(chegada):
                status = "fechado"

            else:
                proxima_mudanca = horario.next_change(
                    chegada
                )

                if (
                    proxima_mudanca is None
                    or proxima_mudanca >= saida
                ):
                    status = "aberto"

                elif horario.is_closed(proxima_mudanca):
                    status = "fechado"

                else:
                    status = "desconhecido"

        except Exception:
            status = "desconhecido"

        return {
            "status": status,
            "fonte": self.fonte,
            "opening_hours": regra,
        }
