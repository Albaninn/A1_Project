🚀 Projeto Final: Análise de Cibersegurança com Machine Learning

Trabalho final desenvolvido para a disciplina de Tópicos Especiais em Software.

O objetivo deste projeto é uma aplicação web completa, desenvolvida em Python com Streamlit, capaz de realizar a ingestão, processamento, análise exploratória e modelagem de Machine Learning sobre um conjunto de dados de incidentes de cibersegurança.

A aplicação cumpre todos os requisitos do trabalho, incluindo o upload dinâmico de novas bases de dados, re-treinamento automático do modelo e um dashboard analítico interativo.

🌟 Recursos Principais

A aplicação é dividida em três páginas principais:

1. Atualizar Base de Dados (O "Motor")

Esta página é o ponto de entrada do sistema e cumpre o requisito de "flexibilidade" e "re-treinamento dinâmico".

Upload Flexível: Permite o upload de um novo conjunto de dados no formato .zip (contendo múltiplos CSVs) ou um único arquivo .csv.

Detecção Inteligente: Detecta automaticamente o separador do CSV (vírgula ou ponto-e-vírgula).

Processamento Robusto: Executa todo o pipeline de ETL (detalhado em etapas_tratamento.md) para limpar, otimizar tipos e salvar os dados em um banco SQLite (CyberSec.db).

Re-treinamento Automático: Após o processamento dos dados, o sistema automaticamente re-treina o modelo de Machine Learning (Random Forest Classifier) e o salva (modelo_classificador.pkl) para ser usado no simulador.

2. Análise Exploratória (O "Dashboard")

Um painel de BI (como o Power BI) construído em cima da base de dados carregada.

Resumo Executivo: Métricas principais (Total de Incidentes, Prejuízo Total) e KPIs interativos (Tipos de Ataque Únicos, Países Únicos) com tooltips.

Análise Geográfica: Um mapa-múndi coroplético (usando Plotly) que traduz os códigos de país (ex: 'UK') para seus códigos ISO (ex: 'GBR') e colore o mapa com base na frequência de incidentes.

Distribuição de Frequência: Tabelas que detalham a contagem e o percentual de Tipos de Ataque, Indústrias Alvo e Mecanismos de Defesa.

Gráficos Interativos: Todos os gráficos são feitos com Plotly Express, permitindo que o usuário passe o mouse para ver valores exatos.

Gerador de Gráfico Dinâmico: Uma ferramenta que permite ao usuário criar seu próprio gráfico de barras, escolhendo a categoria (Eixo X), o valor (Eixo Y) e a agregação (Soma ou Média).

3. Simulador de Predição (O "Modelo de ML")

Uma interface que permite ao usuário interagir diretamente com o modelo de Machine Learning treinado.

Formulário de Input: O usuário pode preencher as características de um incidente (Prejuízo, País, Indústria Alvo, etc.).

Inputs Opcionais: O usuário pode deixar campos em branco. O sistema trata essa "informação nula" preenchendo-a com o valor estatisticamente mais neutro (mediana ou moda) antes de consultar o modelo.

Predição em Tempo Real: O sistema usa o modelo RandomForestClassifier para prever o Attack Type (Tipo de Ataque) mais provável.

Análise de Probabilidade: Além da previsão final, o app exibe uma tabela com a pontuação de probabilidade para cada tipo de ataque possível, mostrando a "confiança" do modelo.

🛠️ Instalação e Execução

Siga os passos abaixo para configurar e executar o projeto em sua máquina local.

Pré-requisitos

Python (versão 3.8 ou superior)

Git (para clonar o repositório)

1. Clonar o Repositório

Abra seu terminal e clone o projeto:

git clone https://[URL-DO-SEU-REPOSITORIO-GIT].git
cd A1_Project


2. Criar um Ambiente Virtual (Recomendado)

É uma boa prática isolar as dependências do projeto:

# Criar o ambiente
python -m venv venv

# Ativar no Windows
.\venv\Scripts\activate

# Ativar no macOS/Linux
source venv/bin/activate


3. Instalar as Dependências

Este projeto usa um arquivo requirements.txt para gerenciar todas as bibliotecas. Instale todas de uma vez executando:

pip install -r requirements.txt


4. Executar a Aplicação

Com as dependências instaladas, inicie o servidor do Streamlit:

streamlit run app.py


O Streamlit irá abrir o seu navegador padrão automaticamente, apontando para http://localhost:8501.

🚀 Como Usar a Aplicação (Workflow)

Primeira Execução: Ao iniciar a aplicação pela primeira vez, o sistema detectará que o banco de dados (CyberSec.db) e o modelo (modelo_classificador.pkl) não existem.

Upload: Você será direcionado automaticamente para a página "Atualizar Base de Dados".

Processamento: Faça o upload do arquivo de dados (ex: CyberSec.zip ou Brasil_Cybersecurity_Threats_2015-2024.csv).

Treinamento: Clique no botão "Processar e Treinar Nova Base". Aguarde alguns minutos enquanto o backend processa os dados e treina o modelo.

Recarregamento: A aplicação será recarregada automaticamente.

Explorar: Agora, com os dados e o modelo carregados, você pode navegar livremente entre as páginas "Análise Exploratória" e "Simulador de Predição".

📂 Estrutura do Projeto

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
└── CyberSec.zip            # (Exemplo de dados brutos para upload)


👥 Integrantes do Grupo

CAIO HENRIQUE PORCEL
KAUAN ALEXANDRE MENDES DA SILVA
LUCAS ALBANO RIBAS SERENATO