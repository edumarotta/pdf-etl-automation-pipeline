# ⚡ Pipeline ETL de Alta Performance para Relatórios Técnicos (PDF)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Concluído-success?style=for-the-badge)
![Performance](https://img.shields.io/badge/Performance-Multiprocessing-orange?style=for-the-badge)

## 🎯 O Desafio de Negócio

No setor de distribuição de energia, o processamento de ajustes de proteção (religadores) é uma tarefa crítica. O desafio consistia em extrair dados tabulares complexos de um volume massivo de documentos legados.

**O Cenário:**
* **Volume:** ~38.000 relatórios técnicos em PDF.
* **Complexidade:** Layouts não estruturados, tabelas desalinhadas e variações de formatação entre diferentes fabricantes/anos.
* **Gargalo Anterior:** O processo utilizando ferramentas de ETL tradicionais via rede levava cerca de **48 horas** para ser concluído.

## 🚀 A Solução

Desenvolvi uma arquitetura de Engenharia de Dados focada em performance "Bare Metal" utilizando Python puro e bibliotecas de processamento vetorial.

### Destaques Técnicos:
1.  **Extração Híbrida Inteligente:** O algoritmo utiliza `pdfplumber` para extração baseada em grades (tabelas), mas possui um sistema de *fallback* (Plano B) que utiliza processamento de texto bruto e Regex quando detecta anomalias visuais ou dados desalinhados (ex: "Grupo 4").
2.  **Multiprocessamento (Parallel Computing):** Implementação de `ProcessPoolExecutor` para distribuir a carga de trabalho entre todos os núcleos disponíveis da CPU, contornando o GIL (Global Interpreter Lock) do Python.
3.  **Mock Data Generator:** Para fins de conformidade e portfólio, desenvolvi um gerador de dados sintéticos (`utils/gerador_pdf.py`) que recria a estrutura complexa dos relatórios reais sem expor dados sensíveis da empresa.

## 📊 Resultados Alcançados

| Métrica | Solução Anterior (Legacy) | Nova Solução (Python) | Impacto |
| :--- | :--- | :--- | :--- |
| **Tempo de Execução** | ~48 Horas | ~30 Minutos | **99% de Redução** 📉 |
| **Custo Computacional** | Alto (Servidor ETL dedicado) | Baixo (Máquina Local) | Eficiência |
| **Qualidade dos Dados** | Falhas em layouts mistos | 100% de extração (Lógica Híbrida) | Confiabilidade |

## 🛠️ Stack Tecnológico

* **Linguagem:** Python 3.x
* **Extração:** `pdfplumber` (análise vetorial de PDFs)
* **Manipulação de Dados:** `pandas`
* **Paralelismo:** `concurrent.futures`, `multiprocessing`
* **UX/Logs:** `tqdm` (monitoramento de progresso em tempo real)
* **Mock Data:** `reportlab` (geração de PDFs programáticos)

## 📂 Estrutura do Projeto

```text
etl-pdf-multiprocessamento/
│
├── data/
│   ├── input_pdfs/       # PDFs de entrada (gerados pelo script de mock)
│   └── output/           # Resultado final (CSV consolidado)
│
├── src/
│   ├── extractor.py      # Core da lógica de extração (Parsers Híbridos)
│   └── main.py           # Orquestrador do multiprocessamento
│
├── utils/
│   └── gerador_pdf.py    # Script gerador de dados sintéticos (Mock)
│
├── requirements.txt      # Dependências do projeto
└── README.md             # Documentação
