from entidades.grafo import Grafo

def main():
    grafo = Grafo()
    grafo.iniciar()
    grafo.imprimir()
    grafo.imprimir_arestas()
    
    grafo.emparelhar()
    
    # Visualizar alocação final (arestas laranja)
    grafo.visualizar("Alocação Final", mostrar_cores=['orange'])
    
    # Ou para ver tudo, use:
    # grafo.visualizar("Grafo Completo")

if __name__ == "__main__":
    main()