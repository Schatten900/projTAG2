from entidades.grafo import Grafo

def main():
    grafo = Grafo()
    grafo.iniciar()
    grafo.imprimir()
    grafo.imprimir_arestas()
    
    grafo.emparelhar()

if __name__ == "__main__":
    main()