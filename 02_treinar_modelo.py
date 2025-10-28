import sqlite3
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split # Para dividir os dados
from sklearn.linear_model import LinearRegression    # Modelo 1: Regressão Linear
from sklearn.ensemble import RandomForestRegressor   # Modelo 2: Random Forest
from sklearn.metrics import mean_squared_error, r2_score # Para avaliar os modelos
import numpy as np

# ==============================================================================
# DEFINIÇÃO DE CAMINHOS
# ==============================================================================
caminho_projeto = Path(".") 
caminho_pasta_csv = caminho_projeto / "CyberSec"
caminho_db = caminho_pasta_csv / "CyberSec.db" 
NOME_TABELA = 'CyberSec_data'

# ==============================================================================
# ETAPA 1: CARREGAR E PRÉ-PROCESSAR OS DADOS
# ==============================================================================
print("--- Iniciando o script de treinamento de modelo ---")
print("Passo 1: Carregando dados do banco de dados...")
try:
    conn = sqlite3.connect(caminho_db)
    df = pd.read_sql_query(f"SELECT * FROM {NOME_TABELA}", conn)
    conn.close()
    print(f"Dados carregados com sucesso: {df.shape[0]} linhas e {df.shape[1]} colunas.")
except Exception as e:
    print(f"Erro ao carregar dados: {e}")
    exit()

# --- Pré-processamento ---
print("\nPasso 2: Aplicando pré-processamento (One-Hot Encoding)...")

# Define a coluna que queremos prever (nossa variável alvo 'y')
COLUNA_ALVO = "Financial Loss (in Million $)"

# Lista das colunas categóricas que precisam de One-Hot Encoding
# 'Year' pode ser tratada como categórica ou numérica, vamos tratá-la como categórica por enquanto.
colunas_categoricas = [
    'Attack Source', 'Attack Type', 'Country', 'Defense Mechanism Used', 
    'Security Vulnerability Type', 'Target Industry', 'Year'
]

# Usa pd.get_dummies() para fazer o One-Hot Encoding
# 'astype(int)' converte os booleanos (True/False) para 0 e 1
df_processado = pd.get_dummies(df, columns=colunas_categoricas, drop_first=True, dtype=int)

print("One-Hot Encoding concluído.")
print(f"Novas dimensões dos dados: {df_processado.shape[0]} linhas e {df_processado.shape[1]} colunas.")

# ==============================================================================
# ETAPA 2: SEPARAR DADOS EM TREINO E TESTE
# ==============================================================================
print("\nPasso 3: Separando dados em Features (X) e Alvo (y)...")

# 'y' é a coluna que queremos prever
y = df_processado[COLUNA_ALVO]

# 'X' são todas as outras colunas que usamos para fazer a predição
# Removemos a coluna alvo do dataframe para criar o X
X = df_processado.drop(columns=[COLUNA_ALVO])

print(f"Features (X) prontas com {X.shape[1]} colunas.")
print(f"Alvo (y) pronto.")

# --- Divisão de Treino e Teste ---
print("\nPasso 4: Dividindo dados em conjuntos de treino e teste...")

# Dividimos os dados: 80% para treino, 20% para teste
# random_state=42 garante que a divisão seja sempre a mesma, para reprodutibilidade
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f" - Dados de treino: {X_train.shape[0]} amostras")
print(f" - Dados de teste:  {X_test.shape[0]} amostras")

# ==============================================================================
# ETAPA 3: TREINAR E AVALIAR MODELOS (Regressão)
# ==============================================================================
print("\n--- ETAPA 3: TREINAMENTO E AVALIAÇÃO DE MODELOS ---")

# --- Modelo 1: Regressão Linear ---
print("\nModelo 1: Regressão Linear")
modelo_lr = LinearRegression()
modelo_lr.fit(X_train, y_train)

# Faz predições nos dados de teste
predicoes_lr = modelo_lr.predict(X_test)

# Avalia o modelo
mse_lr = mean_squared_error(y_test, predicoes_lr)
r2_lr = r2_score(y_test, predicoes_lr)
print(f"  - Erro Quadrático Médio (MSE): {mse_lr:.2f}")
print(f"  - Coeficiente R²: {r2_lr:.2f} (quanto mais próximo de 1.0, melhor)")

# --- Modelo 2: Random Forest Regressor ---
print("\nModelo 2: Random Forest Regressor")
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
modelo_rf.fit(X_train, y_train)

# Faz predições nos dados de teste
predicoes_rf = modelo_rf.predict(X_test)

# Avalia o modelo
mse_rf = mean_squared_error(y_test, predicoes_rf)
r2_rf = r2_score(y_test, predicoes_rf)
print(f"  - Erro Quadrático Médio (MSE): {mse_rf:.2f}")
print(f"  - Coeficiente R²: {r2_rf:.2f} (quanto mais próximo de 1.0, melhor)")

print("\n--- Treinamento Concluído ---")