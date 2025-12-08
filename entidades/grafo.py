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

        # registra índice da próxima preferência a propor
        propostas = {
            aluno.getCodigo(): 0
            for aluno in self.alunos
        }

        # lista de alocações
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

            if iteracao > 1000:  # proteção contra loop infinito
                print("AVISO: Limite de iterações atingido!")
                break

        # Marcar alocações finais com cor laranja
        for projeto_cod, alocados in matches.items():
            for aluno in alocados:
                self._marcar_aresta(aluno.getCodigo(), projeto_cod, "final")

        # visualização final
        self.registrarVisualizacao(iteracao, matches)

        # Imprimir resultado
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
        pass

    # ---------------------------------------------------------
    # MARCAR CORES NAS ARESTAS
    # ---------------------------------------------------------
    def _marcar_aresta(self, aluno_cod, projeto_cod, status):

        if not self.G.has_edge(aluno_cod, projeto_cod):
            return

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
