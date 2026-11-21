from __future__ import annotations
import json, math
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIMENSOES = ('cultura', 'historia', 'gastronomia', 'natureza', 'compras', 'vida_noturna')

def carregar_json(caminho):
    from nextrip_arquitetura.repositorios import RepositorioJSON
    return RepositorioJSON().carregar(caminho)


def salvar_json(caminho, conteudo):
    from nextrip_arquitetura.repositorios import RepositorioJSON
    return RepositorioJSON().salvar(caminho, conteudo)


def similaridade_cosseno(a: dict, b: dict, dimensoes: list[str]) -> float:
    v = [float(a[x]) for x in dimensoes]
    w = [float(b[x]) for x in dimensoes]
    num = sum(x*y for x,y in zip(v,w))
    den = math.sqrt(sum(x*x for x in v)*sum(y*y for y in w))
    return max(0., min(1., num/den)) if den else 0.

def carregar_pontos(caminho):
    catalogo = carregar_json(caminho)
    pontos = [catalogo['origem'], *catalogo['atracoes']]
    if len(pontos) < 3:
        raise ValueError('São necessários uma origem e pelo menos duas atrações.')
    ids = [x['id'] for x in pontos]
    if len(ids) != len(set(ids)):
        raise ValueError('IDs de atrações repetidos.')
    for p in pontos:
        lat, lon = float(p['lat']), float(p['lon'])
        if not (-90<=lat<=90 and -180<=lon<=180):
            raise ValueError(f'Latitude/longitude inválidas: {p["id"]}')
        if not p.get('nome'):
            raise ValueError('Nome de local vazio.')
        if int(p.get('duracao_min', 0))<0:
            raise ValueError('Duração negativa.')
    return catalogo, pontos

def validar_matriz(matriz, n):
    if len(matriz)!=n or any(len(row)!=n for row in matriz):
        raise ValueError('Matriz viária não corresponde à lista de locais.')
    for i in range(n):
        for j in range(n):
            val = matriz[i][j]
            if not isinstance(val,(int,float)) or not math.isfinite(val) or val<0:
                raise ValueError('Matriz contém percurso indisponível ou valor inválido.')

def avaliar_rota(rota, matriz, pontos):
    deslocamento = sum(matriz[a][b] for a,b in zip(rota,rota[1:]))
    visitas = sum(int(pontos[i].get('duracao_min',0)) for i in rota[1:-1])
    return {'indices':rota, 'ids':[pontos[i]['id'] for i in rota],
            'sequencia':[pontos[i]['nome'] for i in rota],
            'deslocamento_min':deslocamento, 'visitas_min':visitas,
            'total_min':deslocamento+visitas}

def validar_rota(rota, paradas, n):
    if len(rota)!=paradas+2 or rota[0]!=0 or rota[-1]!=0:
        raise ValueError('Rota deve começar e terminar na origem e ter exatamente K visitas.')
    meio=rota[1:-1]
    if len(set(meio))!=paradas or any(i<1 or i>=n for i in meio):
        raise ValueError('Rota contém índices inválidos ou atrações repetidas.')
