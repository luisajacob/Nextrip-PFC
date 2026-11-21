                                                                     
from __future__ import annotations

def verificar_ortools():
    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError as e:
        raise RuntimeError('OR-Tools não instalado. Execute: python -m pip install -r requirements.txt') from e
    return pywrapcp, routing_enums_pb2

def _extrair(routing, manager, solucao, ids):
    rota=[]
    idx=routing.Start(0)
    while not routing.IsEnd(idx):
        rota.append(ids[manager.IndexToNode(idx)])
        idx=solucao.Value(routing.NextVar(idx))
    rota.append(0)
    return rota

def tsp_ortools(matriz, visitas, segundos=5):
    pywrapcp, enums=verificar_ortools()
    ids=[0,*visitas]
    manager=pywrapcp.RoutingIndexManager(len(ids),1,0)
    routing=pywrapcp.RoutingModel(manager)
    def custo(i,j):
        return int(matriz[ids[manager.IndexToNode(i)]][ids[manager.IndexToNode(j)]])
    cb=routing.RegisterTransitCallback(custo)
    routing.SetArcCostEvaluatorOfAllVehicles(cb)
    busca=pywrapcp.DefaultRoutingSearchParameters()
    busca.first_solution_strategy=enums.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    busca.local_search_metaheuristic=enums.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    busca.time_limit.seconds=max(1,segundos)
    solucao=routing.SolveWithParameters(busca)
    if solucao is None:raise RuntimeError('OR-Tools não encontrou uma rota.')
    return _extrair(routing,manager,solucao,ids)

def pontuacao_rota(rota,matriz,afinidades,alpha,referencia_min):
    d=sum(matriz[i][j] for i,j in zip(rota,rota[1:]))
    media=sum(afinidades[i] for i in rota[1:-1])/(len(rota)-2)
    return alpha*media-(1-alpha)*d/referencia_min, d, media

def multiobjetivo_ortools(matriz,duracoes,afinidades,paradas,limite_min,alpha,referencia_min,segundos=10):
    pywrapcp,enums=verificar_ortools()
    n=len(matriz)
    if not (1<=paradas<n) or limite_min<=0 or referencia_min<=0 or not 0<=alpha<=1:
        raise ValueError('Parâmetros do roteiro multiobjetivo inválidos.')
    escala=1_000_000
    manager=pywrapcp.RoutingIndexManager(n,1,0)
    routing=pywrapcp.RoutingModel(manager)
    no=lambda i:manager.IndexToNode(i)
    def custo(i,j):
        return round(escala*(1-alpha)*matriz[no(i)][no(j)]/referencia_min)
    cid=routing.RegisterTransitCallback(custo)
    routing.SetArcCostEvaluatorOfAllVehicles(cid)
    def tempo(i,j):
        return int(matriz[no(i)][no(j)]+duracoes[no(i)])
    tid=routing.RegisterTransitCallback(tempo)
    routing.AddDimension(tid,0,int(limite_min),True,'TempoTotal')
    def conta(i,j):
        return int(no(i)!=0)
    vid=routing.RegisterTransitCallback(conta)
    routing.AddDimension(vid,0,paradas,True,'NumeroVisitas')
    routing.GetDimensionOrDie('NumeroVisitas').CumulVar(routing.End(0)).SetValue(paradas)
                                                                              
                                                                          
                                                            
    for i in range(1,n):
        penalidade=2*escala+round(escala*alpha*afinidades[i]/paradas)
        routing.AddDisjunction([manager.NodeToIndex(i)],penalidade)
    busca=pywrapcp.DefaultRoutingSearchParameters()
    busca.first_solution_strategy=enums.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    busca.local_search_metaheuristic=enums.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    busca.time_limit.seconds=max(1,segundos)
    solucao=routing.SolveWithParameters(busca)
    if solucao is None:
        raise RuntimeError('OR-Tools não encontrou solução viável com esse limite. Reduza paradas ou amplie minutos.')
    return _extrair(routing,manager,solucao,list(range(n)))
