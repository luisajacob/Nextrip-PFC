from __future__ import annotations
from .repositorios import RepositorioJSON
from .servicos import ReplanejamentoService, RoteiroService


class OfflineCacheManager:
    def __init__(self, repositorio=None):
        self.repositorio = repositorio or RepositorioJSON()

    def salvar_roteiro_local(self, roteiro, caminho):
        self.repositorio.salvar(caminho, roteiro)

    def carregar_roteiro_local(self, caminho):
        return self.repositorio.carregar(caminho)

    def verificar_sincronizacao(self):
        return {'sincronizacao_remota_implementada': False}


class MapaInterativoView:
    def renderizar_marcadores(self, pontos):
        return [{'id': p['id'], 'nome': p['nome'], 'latitude': float(p['lat']),
                 'longitude': float(p['lon'])} for p in pontos]

    def desenhar_rota_sequencial(self, rota, pontos):
        return [self.renderizar_marcadores([pontos[indice]])[0] for indice in rota]


class AppMobileController:
    def __init__(self, roteiro_service=None, replanejamento=None):
        self.roteiro_service = roteiro_service or RoteiroService()
        self.replanejamento = replanejamento or ReplanejamentoService(self.roteiro_service)

    def coletar_parametros_usuario(self, catalogo, perfil, limite=480, paradas=4):
        return {'catalogo': str(catalogo), 'perfil': str(perfil),
                'limite': int(limite), 'paradas': int(paradas)}

    def renderizar_roteiro(self, resultado):
        return resultado['poc3']['resultados'] if 'poc3' in resultado else resultado['resultados']

    def acionar_rota_replanejamento(self, catalogo, perfil, matriz, paradas=4, limite=480,
                                   pesos=(0.8,), referencia=240, segundos=10):
        return self.replanejamento.recalcular_rota(catalogo, perfil, matriz, paradas,
                                                    limite, pesos, referencia, segundos)
