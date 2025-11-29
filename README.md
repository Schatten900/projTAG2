# 🎓 Projeto TAG – Emparelhamento Estável Máximo entre Alunos e Projetos

Este projeto implementa um sistema completo de **emparelhamento estável máximo** entre **alunos** e **projetos**, seguindo uma adaptação do algoritmo **Gale-Shapley (GS)**, inspirado no problema de *College Admissions*, permitindo que **cada projeto tenha múltiplas vagas**.

Além do emparelhamento, o sistema realiza:

- ✔️ Leitura dos arquivos de entrada de alunos e projetos  
- ✔️ Construção automática de um grafo bipartido  
- ✔️ Aplicação do algoritmo de emparelhamento por preferências  
- ✔️ Geração de 10 visualizações gráficas do processo  
- ✔️ Salvamento das imagens da evolução do emparelhamento  
- ✔️ Destacando arestas por cor (proposta, rejeição, temporário, final)

---

# ▶️ Como Executar

## 1️⃣ Criar o ambiente
```bash
python -m venv venv
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python main.py
