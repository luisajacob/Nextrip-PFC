from __future__ import annotations
import math
from nextrip_base import DIMENSOES, avaliar_rota, similaridade_cosseno, validar_rota, carregar_pontos
from .repositorios import RepositorioJSON


class RecomendacaoIA:
    def __init__(self, repositorio=None):
        self.repositorio = repositorio or RepositorioJSON()

    def gerar_embeddings(self, textos):
        raise NotImplementedError('A geração de embeddings por IA não foi implementada nesta POC.')

    @staticmethod
    def validar_vetor(vetor, dimensoes):
        valores = []
        for dimensao in dimensoes:
            valor = float(vetor[dimensao])
            if not math.isfinite(valor) or not 0 <= valor <= 1:
                raise ValueError(f'Valor inválido no vetor ({dimensao}): {valor}')
            valores.append(valor)
        return valores

    def carregar_entradas(self, catalogo_arquivo, perfil_arquivo):
        catalogo = self.repositorio.carregar_catalogo(catalogo_arquivo)
        perfil = self.repositorio.carregar(perfil_arquivo)
        dimensoes = catalogo.get('dimensoes', list(DIMENSOES))
        if not dimensoes or len(set(dimensoes)) != len(dimensoes):
            raise ValueError('Dimensões inválidas')
        locais = catalogo.get('atracoes', catalogo.get('locais', []))
        if not locais:
            raise ValueError('Catálogo sem atrações')
        self.validar_vetor(perfil['vetor'], dimensoes)
        ids = [p.get('id', p['nome']) for p in locais]
        if len(set(ids)) != len(ids):
            raise ValueError('IDs duplicados no catálogo')
        for ponto in locais:
            self.validar_vetor(ponto['vetor'], dimensoes)
        return catalogo, perfil, dimensoes, locais

    def decompor_pontuacao(self, usuario, local, dimensoes, peso_cosseno=0.7):
        if not 0 <= peso_cosseno <= 1:
            raise ValueError('Peso fora de 0 a 1')
        a = self.validar_vetor(usuario, dimensoes)
        b = self.validar_vetor(local, dimensoes)
        norma_a = math.sqrt(sum(x*x for x in a))
        norma_b = math.sqrt(sum(x*x for x in b))
        cosseno = similaridade_cosseno(usuario, local, dimensoes)
        magnitude = min(norma_a, norma_b) / max(norma_a, norma_b) if max(norma_a, norma_b) > 0 else 0.0
        return {'cosseno': cosseno, 'compatibilidade_magnitude': magnitude,
                'score_hibrido': peso_cosseno*cosseno + (1-peso_cosseno)*magnitude}

    def buscar_similares(self, catalogo_arquivo, perfil_arquivo, metrica='cosseno', peso_cosseno=0.7):
        if metrica not in ('cosseno', 'hibrido'):
            raise ValueError('Métrica inválida')
        _, perfil, dimensoes, locais = self.carregar_entradas(catalogo_arquivo, perfil_arquivo)
        chave = 'cosseno' if metrica == 'cosseno' else 'score_hibrido'
        return {p.get('id', p['nome']): self.decompor_pontuacao(perfil['vetor'], p['vetor'], dimensoes, peso_cosseno)[chave]
                for p in locais}

    def gerar_ranking(self, catalogo_arquivo, perfil_arquivo, metrica='cosseno', peso_cosseno=0.7):
        if metrica not in ('cosseno', 'hibrido'):
            raise ValueError('Métrica inválida')
        catalogo, perfil, dimensoes, locais = self.carregar_entradas(catalogo_arquivo, perfil_arquivo)
        chave = 'cosseno' if metrica == 'cosseno' else 'score_hibrido'
        ranking = []
        for ponto in locais:
            scores = self.decompor_pontuacao(perfil['vetor'], ponto['vetor'], dimensoes, peso_cosseno)
            ranking.append({'id': ponto.get('id', ponto['nome']), 'nome': ponto['nome'],
                            'score': round(scores[chave], 6),
                            'detalhes': {k: round(v, 6) for k, v in scores.items()}})
        ranking.sort(key=lambda item: (-item['score'], item['nome']))
        return {'poc': 1, 'metrica': metrica, 'origem_catalogo': catalogo.get('metadados', {}),
                'categorias': dimensoes, 'perfil': perfil.get('nome', 'usuario'), 'ranking': ranking,
                'observacao': 'Afinidades por categorias heurísticas; não são embeddings semânticos treinados.'}


class IntegracaoExterna:
    def buscar_matriz_distancias(self, pontos, provedor='osrm', autorizar_google=False, sessao=None):
        from providers import matriz_osrm, matriz_google
        if provedor == 'osrm':
            return matriz_osrm(pontos, sessao)
        if provedor == 'google':
            return matriz_google(pontos, autorizar_google, sessao)
        raise ValueError('Provedor permitido: osrm ou google.')

    def buscar_detalhes_poi(self, poi_id, catalogo_arquivo):
        for ponto in RepositorioJSON().carregar_catalogo(catalogo_arquivo)['atracoes']:
            if ponto['id'] == poi_id:
                return ponto
        raise KeyError(f'Ponto de interesse não encontrado: {poi_id}')


class OtimizadorRotas:
    def calcular_melhor_rota(self, pontos, matriz, quantidade=6, segundos=5, solver=None):
        from solvers import tsp_ortools
        solver = solver or tsp_ortools
        numero = len(pontos) - 1
        if not 2 <= quantidade <= numero:
            raise ValueError(f'Informe de 2 a {numero} atrações.')
        visitas = list(range(1, quantidade+1))
        referencia = [0, *visitas, 0]
        otimizada = solver(matriz, visitas, segundos)
        validar_rota(otimizada, quantidade, len(pontos))
        base = avaliar_rota(referencia, matriz, pontos)
        resultado = avaliar_rota(otimizada, matriz, pontos)
        reducao = round(100*(base['deslocamento_min'] - resultado['deslocamento_min']) / base['deslocamento_min'], 2) if base['deslocamento_min'] else 0
        return {'poc': 2, 'metodo': 'Google OR-Tools / Routing', 'quantidade_atracoes': quantidade,
                'referencia': base, 'otimizada': resultado, 'reducao_percentual': reducao,
                'nota': 'Sem comparação com ótimo exato; OR-Tools não garante globalmente a melhor rota.'}


class RoteiroService:
    def __init__(self, recomendacao=None, otimizador=None, integracao=None):
        self.recomendacao = recomendacao or RecomendacaoIA()
        self.otimizador = otimizador or OtimizadorRotas()
        self.integracao = integracao or IntegracaoExterna()

    def gerar_roteiro_otimizado(self, pontos, matriz, catalogo_arquivo, perfil_arquivo, paradas=4,
                               limite=480, pesos=(0., .5, .8, 1.), referencia=240, segundos=10,
                               solver=None, pontuador=None, afinidades=None):
        from solvers import multiobjetivo_ortools, pontuacao_rota
        solver = solver or multiobjetivo_ortools
        pontuador = pontuador or pontuacao_rota
        afinidades = afinidades or self.recomendacao.buscar_similares
        if not (1 <= paradas < len(pontos)):
            raise ValueError('Quantidade de paradas inválida.')
        scores_por_id = afinidades(catalogo_arquivo, perfil_arquivo, metrica='cosseno')
        ids = {p['id'] for p in pontos[1:]}
        if ids - set(scores_por_id):
            raise ValueError('IDs de locais ausentes no recomendador.')
        duracoes = [int(p.get('duracao_min', 0)) for p in pontos]
        scores = [0.0, *[scores_por_id[p['id']] for p in pontos[1:]]]
        resultados = []
        for alpha in pesos:
            rota = solver(matriz, duracoes, scores, paradas, limite, alpha, referencia, segundos)
            validar_rota(rota, paradas, len(pontos))
            metrica = avaliar_rota(rota, matriz, pontos)
            if metrica['total_min'] > limite:
                raise AssertionError('Limite de tempo excedido.')
            score, deslocamento, media = pontuador(rota, matriz, scores, alpha, referencia)
            if deslocamento != metrica['deslocamento_min']:
                raise AssertionError('Deslocamento inconsistente.')
            resultados.append({'alpha_preferencias': alpha, 'peso_deslocamento': round(1-alpha, 3),
                               'afinidade_media_cosseno': round(media, 6), 'score_objetivo': round(score, 6),
                               **metrica, 'atracoes': [{'id': pontos[i]['id'], 'nome': pontos[i]['nome'],
                               'afinidade': round(scores[i], 6), 'duracao_min': duracoes[i]} for i in rota[1:-1]],
                               'restricoes_validadas': True})
        return {'poc': 3, 'metodo': 'Google OR-Tools',
                'objetivo': 'max alpha*afinidade_media - (1-alpha)*deslocamento/referencia',
                'paradas': paradas, 'limite_min': limite, 'referencia_min': referencia,
                'afinidade_origem': 'POC 1 - cosseno, por ID', 'resultados': resultados,
                'nota': 'Sem garantia de ótimo global; duração das visitas estimada.'}

    def executar_pocs(self, catalogo_arquivo, perfil_arquivo, matriz, quantidade=6, paradas=4,
                      limite=480, pesos=(0, .5, .8, 1), referencia=240, segundos=10,
                      executor_poc1=None, executor_poc2=None, executor_poc3=None, calculador_afinidades=None):
        _, pontos = carregar_pontos(catalogo_arquivo)
        executor_poc1 = executor_poc1 or self.recomendacao.gerar_ranking
        executor_poc2 = executor_poc2 or self.otimizador.calcular_melhor_rota
        executor_poc3 = executor_poc3 or self.gerar_roteiro_otimizado
        calculador_afinidades = calculador_afinidades or self.recomendacao.buscar_similares
        c = executor_poc1(catalogo_arquivo, perfil_arquivo, 'cosseno')
        h = executor_poc1(catalogo_arquivo, perfil_arquivo, 'hibrido')
        r2 = executor_poc2(pontos, matriz, quantidade, segundos)
        r3 = executor_poc3(pontos, matriz, catalogo_arquivo, perfil_arquivo, paradas, limite, pesos, referencia, segundos)
        afinidades = calculador_afinidades(catalogo_arquivo, perfil_arquivo)
        conferencias = 0
        for cenario in r3['resultados']:
            for local in cenario['atracoes']:
                if abs(afinidades[local['id']] - local['afinidade']) > 1e-6:
                    raise AssertionError('Integração falhou: POC 3 usa afinidade diferente da POC 1.')
                conferencias += 1
        return {'poc1_cosseno': c, 'poc1_hibrido': h, 'poc2': r2, 'poc3': r3,
                'integracao': {'ok': True, 'afinidades_conferidas': conferencias,
                              'unica_matriz_para_poc2_e_poc3': True,
                              'modelo': 'atracoes com IDs geográficos estáveis'}}

    def gerar_roteiro(self, catalogo_arquivo, perfil_arquivo, provedor='osrm',
                      autorizar_google=False, quantidade=6, paradas=4, limite=480,
                      pesos=(0, .5, .8, 1), referencia=240, segundos=10):
        _, pontos = carregar_pontos(catalogo_arquivo)
        matriz = self.integracao.buscar_matriz_distancias(pontos, provedor, autorizar_google)
        return self.executar_pocs(catalogo_arquivo, perfil_arquivo, matriz, quantidade,
                                  paradas, limite, pesos, referencia, segundos)

    def editar_roteiro_manual(self, roteiro: dict, indice: int, id_poi: str):
        raise NotImplementedError('Edição manual do roteiro ainda não foi implementada nas POCs.')


class ReplanejamentoService:
    def __init__(self, roteiro_service=None):
        self.roteiro_service = roteiro_service or RoteiroService()

    def recalcular_rota(self, catalogo_arquivo, perfil_arquivo, matriz,
                        paradas=4, limite=480, pesos=(0.8,), referencia=240, segundos=10):
        _, pontos = carregar_pontos(catalogo_arquivo)
        return self.roteiro_service.gerar_roteiro_otimizado(pontos, matriz, catalogo_arquivo,
                                                            perfil_arquivo, paradas, limite, pesos,
                                                            referencia, segundos)
