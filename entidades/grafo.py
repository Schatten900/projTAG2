import networkx as nx
import matplotlib.pyplot as plt
import os
import re
from entidades.aluno import Aluno
from entidades.projeto import Projeto

class Grafo:

    def __init__(self):
        self.G = nx.Graph()
        self.alunos = []
        self.projetos = []

    # ---------------------------------------------------------
    # CRIAR GRAFO
    # ---------------------------------------------------------
    def iniciar(self):

        self.alunos.clear()
        self.projetos.clear()
        self.G.clear()

        if not os.path.exists("arquivos"):
            print("ERRO: Pasta 'arquivos' não encontrada!")
            return

        caminho_alunos = "arquivos/alunoEntradaProj2.25TAG"
        caminho_projetos = "arquivos/projetoEntradaProj2.25TAG"

        # fallback
        if not os.path.exists(caminho_alunos):
            caminho_alunos += ".txt"
        if not os.path.exists(caminho_projetos):
            caminho_projetos += ".txt"

        # ------------------ Ler ALUNOS ------------------
        try:
            with open(caminho_alunos, "r", encoding="utf-8") as arq:
                for linha in arq:
                    linha = linha.strip()
                    if not linha or linha.startswith("//"):
                        continue

                    match = re.match(r"\(([^)]+)\):\(([^)]+)\)\s+\((\d+)\)", linha)
                    if match:
                        cod = match.group(1)
                        prefs = [x.strip() for x in match.group(2).split(",")]
                        nota = int(match.group(3))
                        aluno = Aluno(cod, prefs, nota)
                        self.alunos.append(aluno)
        except Exception as e:
            print("Erro lendo alunos:", e)
            return

        # ------------------ Ler PROJETOS ------------------
        try:
            with open(caminho_projetos, "r", encoding="utf-8") as arq:
                for linha in arq:
                    linha = linha.strip()
                    if not linha or linha.startswith("//"):
                        continue

                    match = re.match(r"\(([^,]+),\s*(\d+),\s*(\d+)\)", linha)
                    if match:
                        cod = match.group(1)
                        vagas = int(match.group(2))
                        requisito = int(match.group(3))
                        projeto = Projeto(cod, vagas, requisito)
                        self.projetos.append(projeto)
        except Exception as e:
            print("Erro lendo projetos:", e)
            return

        # Criar grafo
        self._criar_grafo()

    def _criar_grafo(self):

        # adicionar alunos
        for aluno in self.alunos:
            self.G.add_node(
                aluno.getCodigo(),
                tipo="aluno",
                nota=aluno.getNota(),
                preferencias=aluno.getPreferenciasProjetos()
            )

        # adicionar projetos
        for projeto in self.projetos:
            self.G.add_node(
                projeto.getCodigo(),
                tipo="projeto",
                vagas=projeto.getNumeroVagas(),
                requisito=projeto.getRequisitoNotas()
            )

        # arestas aluno → projeto preferido
        for aluno in self.alunos:
            prefs = aluno.getPreferenciasProjetos()
            for i, projeto_pref in enumerate(prefs):
                if any(p.getCodigo() == projeto_pref for p in self.projetos):
                    peso = len(prefs) - i
                    self.G.add_edge(
                        aluno.getCodigo(),
                        projeto_pref,
                        peso=peso,
                        ordem=i+1,
                        cor="black"
                    )

    # ---------------------------------------------------------
    # ACESSO AOS NÓS
    # ---------------------------------------------------------
    def get_alunos(self):
        return [
            aluno for aluno in self.alunos
        ]

    def get_projetos(self):
        return [
            projeto for projeto in self.projetos
        ]

    def _busca_projeto(self, codigo):
        for p in self.projetos:
            if p.getCodigo() == codigo:
                return p
        return None

    # ---------------------------------------------------------
    # EMPARELHAMENTO (Gale–Shapley)
    # ---------------------------------------------------------
    def emparelhar(self):

        livres = self.get_alunos().copy()

        propostas = {
            aluno.getCodigo(): 0
            for aluno in self.alunos
        }

        matches = {
            projeto.getCodigo(): []
            for projeto in self.projetos
        }

        iteracao = 1

        while livres:

            # registrar visualização da iteração
            self.registrarVisualizacao(iteracao, matches)

            aluno = livres.pop(0)
            prefs = aluno.getPreferenciasProjetos()
            cod_aluno = aluno.getCodigo()

            # Se já propôs para todos os projetos, desiste
            if propostas[cod_aluno] >= len(prefs):
                continue

            projeto_cod = prefs[propostas[cod_aluno]]
            propostas[cod_aluno] += 1

            projeto = self._busca_projeto(projeto_cod)

            # se projeto não existe, volta para a fila e tenta próxima preferência
            if projeto is None:
                livres.append(aluno)
                continue

            # marca aresta como proposta (azul)
            self._marcar_aresta(cod_aluno, projeto_cod, "proposta")

            # rejeitar se nota < requisito
            if aluno.getNota() < projeto.getRequisitoNotas():
                self._marcar_aresta(cod_aluno, projeto_cod, "rejeicao")
                livres.append(aluno)  # volta para a fila e tenta próxima preferência
                continue

            alocados = matches[projeto_cod]

            # se há vaga, insere
            if len(alocados) < projeto.getNumeroVagas():
                alocados.append(aluno)
                self._marcar_aresta(cod_aluno, projeto_cod, "temporario")
            else:
                # projeto está cheio → substituir pior aluno
                pior = min(alocados, key=lambda a: a.getNota())

                # se aluno atual é melhor que o pior
                if aluno.getNota() > pior.getNota():
                    alocados.remove(pior)
                    alocados.append(aluno)
                    self._marcar_aresta(cod_aluno, projeto_cod, "temporario")
                    self._marcar_aresta(pior.getCodigo(), projeto_cod, "black")
                    livres.append(pior)  # pior volta a propor
                else:
                    # rejeitado
                    self._marcar_aresta(cod_aluno, projeto_cod, "rejeicao")
                    livres.append(aluno)  # volta para a fila e tenta próxima preferência

            iteracao += 1

            if iteracao > 10:  # proteção contra loop infinito
                print("AVISO: Limite de iterações atingido!")
                break

        # FASE 2: Garantir que cada projeto tenha pelo menos 1 aluno
        self._garantir_minimo_por_projeto(matches)

        # Marcar alocações finais com cor laranja
        for projeto_cod, alocados in matches.items():
            for aluno in alocados:
                self._marcar_aresta(aluno.getCodigo(), projeto_cod, "final")

        # visualização final
        self.registrarVisualizacao(iteracao, matches)

        # Calcular e imprimir estatísticas
        self._imprimir_estatisticas(matches)

        return matches

    def _garantir_minimo_por_projeto(self, matches):
        """
        Garante que cada projeto tenha pelo menos 1 aluno alocado.
        Move alunos de projetos com múltiplas vagas para projetos vazios quando possível.
        """
        print("\n🔧 FASE 2: Garantindo mínimo de 1 aluno por projeto...")
        
        projetos_vazios = [p_cod for p_cod, alocs in matches.items() if len(alocs) == 0]
        
        if not projetos_vazios:
            print("  ✓ Todos os projetos já têm pelo menos 1 aluno.")
            return
        
        for projeto_vazio_cod in projetos_vazios:
            projeto_vazio = self._busca_projeto(projeto_vazio_cod)
            
            # Buscar alunos qualificados que listaram este projeto
            candidatos = []
            for aluno in self.alunos:
                if projeto_vazio_cod in aluno.getPreferenciasProjetos():
                    if aluno.getNota() >= projeto_vazio.getRequisitoNotas():
                        candidatos.append(aluno)
            
            # Ordenar candidatos por nota (melhor primeiro)
            if candidatos:
                candidatos.sort(key=lambda a: a.getNota(), reverse=True)
            
            # Tentar realocar um candidato que já está em outro projeto
            realocado = False
            for candidato in candidatos:
                cod_candidato = candidato.getCodigo()
                
                # Verificar se o candidato já está alocado em outro projeto
                projeto_atual = None
                for p_cod, alocs in matches.items():
                    if any(a.getCodigo() == cod_candidato for a in alocs):
                        projeto_atual = p_cod
                        break
                
                if projeto_atual:
                    # Candidato já está alocado
                    # Só realoca se o projeto atual tiver mais de 1 aluno
                    if len(matches[projeto_atual]) > 1:
                        # Verificar se este projeto vazio está nas preferências do candidato
                        prefs = candidato.getPreferenciasProjetos()
                        pos_atual = prefs.index(projeto_atual) if projeto_atual in prefs else float('inf')
                        pos_vazio = prefs.index(projeto_vazio_cod) if projeto_vazio_cod in prefs else float('inf')
                        
                        # Realoca independente da preferência (obrigatório ter pelo menos 1)
                        # Remover do projeto atual
                        matches[projeto_atual] = [a for a in matches[projeto_atual] 
                                                 if a.getCodigo() != cod_candidato]
                        # Adicionar ao projeto vazio
                        matches[projeto_vazio_cod].append(candidato)
                        self._marcar_aresta(cod_candidato, projeto_atual, "black")
                        self._marcar_aresta(cod_candidato, projeto_vazio_cod, "temporario")
                        print(f"  ✓ {projeto_vazio_cod}: Realocado {cod_candidato} de {projeto_atual}")
                        realocado = True
                        break
                else:
                    # Candidato não está alocado, podemos alocar diretamente
                    matches[projeto_vazio_cod].append(candidato)
                    self._marcar_aresta(cod_candidato, projeto_vazio_cod, "temporario")
                    print(f"  ✓ {projeto_vazio_cod}: Alocado {cod_candidato} (não estava alocado)")
                    realocado = True
                    break
            
            if not realocado:
                # Última tentativa: pegar qualquer aluno não alocado que atenda requisitos
                alunos_nao_alocados = []
                for aluno in self.alunos:
                    cod = aluno.getCodigo()
                    alocado = any(cod == a.getCodigo() for alocs in matches.values() for a in alocs)
                    if not alocado and aluno.getNota() >= projeto_vazio.getRequisitoNotas():
                        alunos_nao_alocados.append(aluno)
                
                if alunos_nao_alocados:
                    # Pegar o melhor aluno não alocado
                    melhor = max(alunos_nao_alocados, key=lambda a: a.getNota())
                    matches[projeto_vazio_cod].append(melhor)
                    self._marcar_aresta(melhor.getCodigo(), projeto_vazio_cod, "temporario")
                    print(f"  ✓ {projeto_vazio_cod}: Alocado {melhor.getCodigo()} (forçado)")
                else:
                    # RELAXAMENTO: Se não há candidatos qualificados, pega o melhor não alocado
                    # mesmo que não atenda o requisito mínimo
                    todos_nao_alocados = []
                    for aluno in self.alunos:
                        cod = aluno.getCodigo()
                        alocado = any(cod == a.getCodigo() for alocs in matches.values() for a in alocs)
                        if not alocado:
                            todos_nao_alocados.append(aluno)
                    
                    if todos_nao_alocados:
                        melhor = max(todos_nao_alocados, key=lambda a: a.getNota())
                        matches[projeto_vazio_cod].append(melhor)
                        self._marcar_aresta(melhor.getCodigo(), projeto_vazio_cod, "temporario")
                        print(f"  ⚠ {projeto_vazio_cod}: Alocado {melhor.getCodigo()} (REQUISITO RELAXADO - nota {melhor.getNota()} < {projeto_vazio.getRequisitoNotas()})")
                    else:
                        print(f"  ✗ {projeto_vazio_cod}: Impossível alocar (sem candidatos viáveis)")

    def _imprimir_estatisticas(self, matches):
        """Imprime estatísticas detalhadas do emparelhamento"""
        
        # Alunos alocados
        alunos_alocados = set()
        for alocados in matches.values():
            for aluno in alocados:
                alunos_alocados.add(aluno.getCodigo())
        
        alunos_nao_alocados = [a for a in self.alunos if a.getCodigo() not in alunos_alocados]
        
        # Projetos com alocações
        projetos_preenchidos = [p for p, alocs in matches.items() if len(alocs) > 0]
        projetos_vazios = [p for p, alocs in matches.items() if len(alocs) == 0]
        
        # Total de vagas disponíveis e ocupadas
        total_vagas = sum(p.getNumeroVagas() for p in self.projetos)
        vagas_ocupadas = sum(len(alocs) for alocs in matches.values())
        
        # Análise de projetos vazios
        print("\n" + "="*60)
        print("ESTATÍSTICAS DO EMPARELHAMENTO")
        print("="*60)
        
        print(f"\n📊 RESUMO GERAL:")
        print(f"  • Total de alunos: {len(self.alunos)}")
        print(f"  • Alunos alocados: {len(alunos_alocados)} ({len(alunos_alocados)/len(self.alunos)*100:.1f}%)")
        print(f"  • Alunos não alocados: {len(alunos_nao_alocados)} ({len(alunos_nao_alocados)/len(self.alunos)*100:.1f}%)")
        
        print(f"\n  • Total de projetos: {len(self.projetos)}")
        print(f"  • Projetos preenchidos: {len(projetos_preenchidos)} ({len(projetos_preenchidos)/len(self.projetos)*100:.1f}%)")
        print(f"  • Projetos vazios: {len(projetos_vazios)} ({len(projetos_vazios)/len(self.projetos)*100:.1f}%)")
        
        print(f"\n  • Total de vagas: {total_vagas}")
        print(f"  • Vagas ocupadas: {vagas_ocupadas} ({vagas_ocupadas/total_vagas*100:.1f}%)")
        print(f"  • Vagas disponíveis: {total_vagas - vagas_ocupadas}")
        
        # Análise de alunos não alocados
        if alunos_nao_alocados:
            print(f"\nALUNOS NÃO ALOCADOS ({len(alunos_nao_alocados)}):")
            for aluno in alunos_nao_alocados[:10]:  # mostra até 10
                prefs = aluno.getPreferenciasProjetos()
                nota = aluno.getNota()
                print(f"  • {aluno.getCodigo()} (Nota: {nota}) - Preferências: {prefs[:3]}...")
            if len(alunos_nao_alocados) > 10:
                print(f"  ... e mais {len(alunos_nao_alocados) - 10} alunos")
        
        # Análise de projetos vazios
        if projetos_vazios:
            print(f"\nPROJETOS VAZIOS ({len(projetos_vazios)}):")
            for proj_cod in projetos_vazios[:10]:  # mostra até 10
                projeto = self._busca_projeto(proj_cod)
                # Contar quantos alunos tinham interesse
                interessados = sum(1 for a in self.alunos if proj_cod in a.getPreferenciasProjetos())
                qualificados = sum(1 for a in self.alunos 
                                 if proj_cod in a.getPreferenciasProjetos() 
                                 and a.getNota() >= projeto.getRequisitoNotas())
                
                print(f"  • {proj_cod} (Vagas: {projeto.getNumeroVagas()}, Req: {projeto.getRequisitoNotas()}) - "
                      f"Interessados: {interessados}, Qualificados: {qualificados}")
            if len(projetos_vazios) > 10:
                print(f"  ... e mais {len(projetos_vazios) - 10} projetos")
        
        # Distribuição de preferências
        print(f"\nQUALIDADE DAS ALOCAÇÕES:")
        preferencias_atendidas = {1: 0, 2: 0, 3: 0, '4+': 0}
        for aluno in self.alunos:
            if aluno.getCodigo() in alunos_alocados:
                # Encontrar qual projeto o aluno foi alocado
                for proj_cod, alocs in matches.items():
                    if any(a.getCodigo() == aluno.getCodigo() for a in alocs):
                        prefs = aluno.getPreferenciasProjetos()
                        if proj_cod in prefs:
                            pos = prefs.index(proj_cod) + 1
                            if pos <= 3:
                                preferencias_atendidas[pos] += 1
                            else:
                                preferencias_atendidas['4+'] += 1
                        break
        
        total_alocados = len(alunos_alocados)
        if total_alocados > 0:
            print(f"  • 1ª escolha: {preferencias_atendidas[1]} ({preferencias_atendidas[1]/total_alocados*100:.1f}%)")
            print(f"  • 2ª escolha: {preferencias_atendidas[2]} ({preferencias_atendidas[2]/total_alocados*100:.1f}%)")
            print(f"  • 3ª escolha: {preferencias_atendidas[3]} ({preferencias_atendidas[3]/total_alocados*100:.1f}%)")
            print(f"  • 4ª+ escolha: {preferencias_atendidas['4+']} ({preferencias_atendidas['4+']/total_alocados*100:.1f}%)")
        
        print("\n" + "="*60)
        
        # Imprimir resultado por projeto
        print("\n=== EMPARELHAMENTO FINAL ===")
        for projeto_cod, alocados in matches.items():
            if alocados:
                nomes_alunos = [a.getCodigo() for a in alocados]
                print(f"{projeto_cod}: {nomes_alunos}")
            else:
                print(f"{projeto_cod}: (vazio)")

        return matches

    # ---------------------------------------------------------
    # GERAR VISUALIZAÇÕES
    # ---------------------------------------------------------
    def registrarVisualizacao(self, iteracao, matches):
        """Salva visualizações do estado do grafo em cada iteração"""
        if iteracao not in [1, 3, 5, 7, 10]:  # Só salva em iterações específicas
            return
            
        import os
        if not os.path.exists("visualizacoes"):
            os.makedirs("visualizacoes")
        
        # Criar 4 visualizações separadas
        cores_grupos = {
            'propostas': (['blue'], 'Propostas (Azul)'),
            'rejeicoes': (['red'], 'Rejeições (Vermelho)'),
            'temporarios': (['green'], 'Alocações Temporárias (Verde)'),
            'todas': (['blue', 'green', 'red'], 'Estado Completo')
        }
        
        for nome, (cores, titulo) in cores_grupos.items():
            self._salvar_visualizacao_cores(iteracao, cores, f"{titulo} - Iteração {iteracao}", 
                                           f"visualizacoes/iter{iteracao:02d}_{nome}.png")
    
    def _salvar_visualizacao_cores(self, iteracao, mostrar_cores, titulo, arquivo):
        """Salva uma visualização mostrando apenas cores específicas"""
        fig = plt.figure(figsize=(16, 12))
        
        # Separar nós por tipo
        alunos_nodes = [n for n, d in self.G.nodes(data=True) if d.get('tipo') == 'aluno']
        projetos_nodes = [n for n, d in self.G.nodes(data=True) if d.get('tipo') == 'projeto']
        
        # Criar layout bipartido
        pos = {}
        y_spacing_alunos = 1.0 / (len(alunos_nodes) + 1) if alunos_nodes else 1
        for i, aluno in enumerate(alunos_nodes):
            pos[aluno] = (0, 1 - (i + 1) * y_spacing_alunos)
        
        y_spacing_projetos = 1.0 / (len(projetos_nodes) + 1) if projetos_nodes else 1
        for i, projeto in enumerate(projetos_nodes):
            pos[projeto] = (2, 1 - (i + 1) * y_spacing_projetos)
        
        # Desenhar nós
        nx.draw_networkx_nodes(self.G, pos, nodelist=alunos_nodes,
                              node_color='lightblue', node_shape='o', 
                              node_size=600, label='Alunos')
        nx.draw_networkx_nodes(self.G, pos, nodelist=projetos_nodes,
                              node_color='lightgreen', node_shape='s', 
                              node_size=600, label='Projetos')
        
        # Agrupar e desenhar arestas por cor
        cores_arestas = {}
        for u, v, data in self.G.edges(data=True):
            cor = data.get('cor', 'black')
            if cor not in cores_arestas:
                cores_arestas[cor] = []
            cores_arestas[cor].append((u, v))
        
        mapa_labels = {
            'black': 'Preferência',
            'blue': 'Proposta',
            'green': 'Temporário',
            'red': 'Rejeitado',
            'orange': 'Final'
        }
        
        contador = {}
        for cor, arestas in cores_arestas.items():
            if cor in mostrar_cores:
                contador[cor] = len(arestas)
                label = f"{mapa_labels.get(cor, cor)} ({len(arestas)})"
                nx.draw_networkx_edges(self.G, pos, edgelist=arestas,
                                      edge_color=cor, width=3, alpha=0.7, label=label)
        
        # Labels dos nós (só código)
        labels = {node: node for node in self.G.nodes()}
        nx.draw_networkx_labels(self.G, pos, labels, font_size=7)
        
        # Título e informações
        info_cores = " | ".join([f"{mapa_labels.get(c, c)}: {contador.get(c, 0)}" 
                                 for c in mostrar_cores if c in contador])
        plt.title(f"{titulo}\n{info_cores}", fontsize=14, fontweight='bold')
        plt.legend(loc='upper left', fontsize=10)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(arquivo, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  -> Salva: {arquivo}")

    # ---------------------------------------------------------
    # MARCAR CORES NAS ARESTAS
    # ---------------------------------------------------------
    def _marcar_aresta(self, aluno_cod, projeto_cod, status):

        # Se a aresta não existe, cria ela
        if not self.G.has_edge(aluno_cod, projeto_cod):
            self.G.add_edge(aluno_cod, projeto_cod, peso=0, ordem=0, cor="black")

        cor = {
            "proposta": "blue",
            "temporario": "green",
            "rejeicao": "red",
            "final": "orange"
        }.get(status, "black")

        self.G[aluno_cod][projeto_cod]["cor"] = cor

    # ---------------------------------------------------------
    # IMPRIMIR INFORMAÇÕES DO GRAFO
    # ---------------------------------------------------------
    def imprimir(self):
        """Imprime informações sobre os nós do grafo"""
        print("\n=== ALUNOS ===")
        for aluno in self.alunos:
            print(f"Código: {aluno.getCodigo()}, Nota: {aluno.getNota()}, Preferências: {aluno.getPreferenciasProjetos()}")
        
        print("\n=== PROJETOS ===")
        for projeto in self.projetos:
            print(f"Código: {projeto.getCodigo()}, Vagas: {projeto.getNumeroVagas()}, Requisito: {projeto.getRequisitoNotas()}")
        
        print(f"\nTotal de nós: {self.G.number_of_nodes()}")
        print(f"Total de arestas: {self.G.number_of_edges()}")

    def imprimir_arestas(self):
        """Imprime informações sobre as arestas do grafo"""
        print("\n=== ARESTAS ===")
        for u, v, data in self.G.edges(data=True):
            peso = data.get('peso', 'N/A')
            ordem = data.get('ordem', 'N/A')
            cor = data.get('cor', 'black')
            print(f"{u} -> {v} | Peso: {peso}, Ordem: {ordem}, Cor: {cor}")

    def visualizar(self, titulo="Grafo de Emparelhamento", mostrar_cores=None):
        """
        Plota uma visualização do grafo usando matplotlib
        
        Args:
            titulo: Título do gráfico
            mostrar_cores: Lista de cores a mostrar (ex: ['green'] para só alocados)
                          Se None, mostra todas as arestas
                          Cores disponíveis: 'black', 'blue', 'green', 'red', 'orange'
        """
        if self.G.number_of_nodes() == 0:
            print("Grafo vazio, nada para visualizar.")
            return

        plt.figure(figsize=(14, 10))
        
        # Separar nós por tipo
        alunos_nodes = [n for n, d in self.G.nodes(data=True) if d.get('tipo') == 'aluno']
        projetos_nodes = [n for n, d in self.G.nodes(data=True) if d.get('tipo') == 'projeto']
        
        # Criar layout bipartido
        pos = {}
        
        # Posicionar alunos à esquerda
        y_spacing_alunos = 1.0 / (len(alunos_nodes) + 1) if alunos_nodes else 1
        for i, aluno in enumerate(alunos_nodes):
            pos[aluno] = (0, 1 - (i + 1) * y_spacing_alunos)
        
        # Posicionar projetos à direita
        y_spacing_projetos = 1.0 / (len(projetos_nodes) + 1) if projetos_nodes else 1
        for i, projeto in enumerate(projetos_nodes):
            pos[projeto] = (2, 1 - (i + 1) * y_spacing_projetos)
        
        # Desenhar nós de alunos (círculos azuis)
        nx.draw_networkx_nodes(
            self.G, pos,
            nodelist=alunos_nodes,
            node_color='lightblue',
            node_shape='o',
            node_size=800,
            label='Alunos'
        )
        
        # Desenhar nós de projetos (quadrados verdes)
        nx.draw_networkx_nodes(
            self.G, pos,
            nodelist=projetos_nodes,
            node_color='lightgreen',
            node_shape='s',
            node_size=800,
            label='Projetos'
        )
        
        # Agrupar arestas por cor
        cores_arestas = {}
        for u, v, data in self.G.edges(data=True):
            cor = data.get('cor', 'black')
            if cor not in cores_arestas:
                cores_arestas[cor] = []
            cores_arestas[cor].append((u, v))
        
        # Desenhar arestas com suas respectivas cores
        mapa_labels_cores = {
            'black': 'Preferência',
            'blue': 'Proposta',
            'green': 'Alocado',
            'red': 'Rejeitado',
            'orange': 'Final'
        }
        
        for cor, arestas in cores_arestas.items():
            # Se mostrar_cores foi especificado, filtra apenas as cores desejadas
            if mostrar_cores is not None and cor not in mostrar_cores:
                continue
                
            label = mapa_labels_cores.get(cor, cor)
            nx.draw_networkx_edges(
                self.G, pos,
                edgelist=arestas,
                edge_color=cor,
                width=2,
                alpha=0.6,
                label=label
            )
        
        # Adicionar labels dos nós
        labels = {}
        for node in self.G.nodes():
            data = self.G.nodes[node]
            if data.get('tipo') == 'aluno':
                nota = data.get('nota', '?')
                labels[node] = f"{node}\n(Nota: {nota})"
            else:
                vagas = data.get('vagas', '?')
                req = data.get('requisito', '?')
                labels[node] = f"{node}\n(V:{vagas}, R:{req})"
        
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8)
        
        plt.title(titulo, fontsize=16, fontweight='bold')
        plt.legend(loc='upper left', fontsize=10)
        plt.axis('off')
        plt.tight_layout()
        plt.show()
