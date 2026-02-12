# 🚀 Projeto Final: Análise de Cibersegurança com Machine Learning

[![en](https://img.shields.io/badge/lang-en-red.svg)](README.en.md)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/SciKit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

> Trabalho final desenvolvido para a disciplina de Tópicos Especiais em Software.
>
> O objetivo deste projeto é uma aplicação web completa, desenvolvida em Python com Streamlit, capaz de realizar a ingestão, processamento, análise exploratória e modelagem de Machine Learning sobre um conjunto de dados de incidentes de cibersegurança.
>
> A aplicação cumpre todos os requisitos do trabalho, incluindo o upload dinâmico de novas bases de dados, re-treinamento automático do modelo e um dashboard analítico interativo.

---

## 🌟 Recursos Principais

A aplicação é dividida em três páginas principais:

### 1. Atualizar Base de Dados (O "Motor")

Esta página é o ponto de entrada do sistema e cumpre o requisito de "flexibilidade" e "re-treinamento dinâmico".

* **Upload Flexível**: Permite o upload de um novo conjunto de dados no formato `.zip` (contendo múltiplos CSVs) ou um único arquivo `.csv`.
* **Detecção Inteligente**: Detecta automaticamente o separador do CSV (vírgula ou ponto-e-vírgula). (Esta funcionalidade estava no seu código original).
* **Processamento Robusto**: Executa todo o pipeline de ETL (definido no `backend_tasks.py`) para limpar, otimizar tipos e salvar os dados em um banco **SQLite** (`CyberSec.db`).
* **Re-treinamento Automático**: Após o processamento dos dados, o sistema automaticamente re-treina o modelo de Machine Learning (**Random Forest Classifier**) e o salva (`modelo_classificador.pkl`) para ser usado no simulador.

### 2. Análise Exploratória (O "Dashboard")

Um painel de BI (como o Power BI) construído diretamente em Python.

* **Visualizações Interativas**: Usa **Plotly** para gerar gráficos dinâmicos (mapa coroplético, barras, dispersão, histograma).
* **Métricas de KPI**: Apresenta um resumo com os principais indicadores (Total de Incidentes, Prejuízo Total, etc.).
* **Análise de Padrões**: Permite que o usuário estratégico (Gestor, CISO) identifique visualmente quais ataques são mais caros, mais frequentes e qual a eficiência da equipe de resposta.

### 3. Simulador de Predição (O "Modelo de ML")

Esta é a ferramenta preditiva do sistema, que usa o modelo treinado.

* **Inferência em Tempo Real**: O usuário (Tático/Operacional) insere as características de um incidente *em andamento*.
* **Previsão de Probabilidade**: O modelo **Random Forest** carregado (`.pkl`) prevê não apenas o tipo de ataque mais provável, mas a **distribuição de probabilidade** (ex: 40% SQL Injection, 21% Ransomware).
* **Apoio à Decisão**: Ajuda a equipe de resposta a incidentes a **priorizar ações** (mudando de uma postura Reativa para Proativa) e acionar a equipe correta.

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.10+**
* **Streamlit**: Para a construção da interface web (frontend).
* **Pandas**: Para manipulação e processamento de dados (ETL).
* **Scikit-learn**: Para todo o pipeline de Machine Learning (Engenharia de Features, Treinamento, `RandomForestClassifier`).
* **Plotly Express**: Para a criação dos gráficos interativos.
* **Joblib**: Para salvar e carregar o modelo de ML treinado (`.pkl`).
* **SQLite**: (Nativo do Python) Para armazenar os dados processados de forma otimizada.

---

## ⚙️ Como Executar o Projeto Localmente

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Crie um ambiente virtual (Recomendado):**
    ```bash
    python -m venv venv
    - No macOS/Linux: source venv/bin/activate  
    - No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute a aplicação Streamlit:**
    ```bash
    streamlit run app.py
    ```

5.  Acesse `http://localhost:8501` no seu navegador.

---

## 🚀 Como Usar a Aplicação (Workflow)

1.  **Primeira Execução:**
    * Ao iniciar a aplicação pela primeira vez, o sistema detectará que o banco de dados (`CyberSec.db`) e o modelo (`modelo_classificador.pkl`) não existem.

2.  **Upload:**
    * Você será direcionado automaticamente para a página "**Atualizar Base de Dados**".

3.  **Processamento:**
    * Faça o upload do arquivo de dados (ex: CyberSec.zip ou Brasil_Cybersecurity_Threats_2015-2024.csv).

4.  **Treinamento:**
    * Clique no botão "**Processar e Treinar Nova Base**". Aguarde alguns minutos enquanto o backend processa os dados e treina o modelo.

5.  **Recarregamento:**
    * A aplicação será recarregada automaticamente.

6.  **Explorar:**
    * Agora, com os dados e o modelo carregados, você pode navegar livremente entre as páginas "**Análise Exploratória**" e "**Simulador de Predição**".

---

## 📂 Estrutura do Projeto

```
A1_Project/
│
├── .streamlit/
│   └── config.toml         # (Configuração do tema escuro)
│
├── CyberSec/
│   ├── CyberSec.db         # (Criado pelo app - O banco otimizado)
│   └── modelo_classificador.pkl # (Criado pelo app - O modelo treinado)
│
├── app.py                  # (O código da interface web - Streamlit)
├── backend_tasks.py        # (O "motor" de processamento e ML - Pandas/Sklearn)
├── requirements.txt        # (Lista de dependências do Python)
├── README.md               # (Esta documentação)
├── README.en.md            # (Documentação em inglês)
└── CyberSec.zip            # (Exemplo de dados brutos para upload)
```

---

## 📊 Apresentação e Base de dados utilizada
- [Apresentação no Canvas](https://www.canva.com/design/DAG3kcG_G7A/KoHOwSSRpPu-q8qupP0cOg/edit?utm_content=DAG3kcG_G7A&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)
- [Base de dados Global Cybersecurity Threats (2015-2024)](https://www.kaggle.com/datasets/atharvasoundankar/global-cybersecurity-threats-2015-2024)
  
---

### 👥 Integrantes e Perfis no LinkedIn

- [CAIO HENRIQUE PORCEL](https://www.linkedin.com/in/caio-henrique-porcel-702340243/)
- [KAUAN ALEXANDRE MENDES DA SILVA](https://www.linkedin.com/in/mendeskauan/)
- [LUCAS ALBANO RIBAS SERENATO](https://www.linkedin.com/in/lucas-albano-serenato-345306200/)

