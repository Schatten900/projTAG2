import networkx as nx
import matplotlib.pyplot as plt
import os
import re

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

        # registra propostas já feitas
        propostas = {
            aluno.getCodigo(): set()
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

            novos_livres = []

            for aluno in livres:

                prefs = aluno.getPreferenciasProjetos()
                cod_aluno = aluno.getCodigo()

                # percorre as preferências em ordem
                for projeto_cod in prefs:

                    # se já propôs, pula
                    if projeto_cod in propostas[cod_aluno]:
                        continue

                    propostas[cod_aluno].add(projeto_cod)
                    projeto = self._busca_projeto(projeto_cod)

                    # marca aresta como proposta (azul)
                    self._marcar_aresta(cod_aluno, projeto_cod, "proposta")

                    # rejeitar se nota < requisito
                    if aluno.getNota() < projeto.getRequisitoNotas():
                        self._marcar_aresta(cod_aluno, projeto_cod, "rejeicao")
                        break

                    alocados = matches[projeto_cod]

                    # se há vaga, insere
                    if len(alocados) < projeto.getNumeroVagas():
                        alocados.append(aluno)
                        self._marcar_aresta(cod_aluno, projeto_cod, "temporario")
                        break

                    # senão, o projeto está cheio → substituir pior aluno
                    pior = min(alocados, key=lambda a: a.getNota())

                    # se aluno atual é melhor que o pior
                    if aluno.getNota() > pior.getNota():
                        alocados.remove(pior)
                        alocados.append(aluno)

                        novos_livres.append(pior)
                        break
                    else:
                        # rejeitado
                        self._marcar_aresta(cod_aluno, projeto_cod, "rejeicao")
                        break

            livres = novos_livres
            iteracao += 1

            if iteracao > 10:
                break

        # visualização final
        self.registrarVisualizacao(iteracao, matches)

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
