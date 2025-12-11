from entidades.grafo import Grafo

def main():
    grafo = Grafo()
    grafo.iniciar()
    grafo.imprimir()
    grafo.imprimir_arestas()
    
    grafo.emparelhar()

    # Visualizar alocação final (arestas laranja)
    grafo.visualizar("Emparelhamento final", mostrar_cores=['orange'])
    
    # para ver tudo:
    # grafo.visualizar("Grafo Completo")

if __name__ == "__main__":
    main()