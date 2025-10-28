import sqlite3
import pandas as pd
from pathlib import Path
import joblib # Biblioteca para salvar o modelo de ML

from sklearn.model_selection import train_test_split
# Importações para Regressão
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Importações para Classificação
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# ==============================================================================
# DEFINIÇÃO DE CAMINHOS
# ==============================================================================
caminho_projeto = Path(".") 
caminho_pasta_csv = caminho_projeto / "CyberSec"
caminho_db = caminho_pasta_csv / "CyberSec.db" 
NOME_TABELA = 'CyberSec_data'
CAMINHO_MODELO_SALVO = caminho_projeto / 'modelo_classificador.pkl'

# ==============================================================================
# ETAPA 1: CARREGAR OS DADOS (COMPARTILHADO)
# ==============================================================================
print("--- Iniciando o script de treinamento de modelo ---")
print("Passo 1: Carregando dados do banco de dados...")
try:
    conn = sqlite3.connect(caminho_db)
    df_original = pd.read_sql_query(f"SELECT * FROM {NOME_TABELA}", conn)
    conn.close()
    print(f"Dados carregados com sucesso: {df_original.shape[0]} linhas e {df_original.shape[1]} colunas.")
except Exception as e:
    print(f"Erro ao carregar dados: {e}")
    exit()

# ==============================================================================
# PARTE 1: TENTATIVA DE REGRESSÃO (Prever "Financial Loss")
# ==============================================================================
print("\n" + "="*70)
print("--- PARTE 1: MODELO DE REGRESSÃO (Prever Prejuízo Financeiro) ---")
print("="*70)

# --- Pré-processamento para Regressão ---
COLUNA_ALVO_REG = "Financial Loss (in Million $)"
colunas_categoricas_reg = [
    'Attack Source', 'Attack Type', 'Country', 'Defense Mechanism Used', 
    'Security Vulnerability Type', 'Target Industry', 'Year'
]
df_reg = pd.get_dummies(df_original, columns=colunas_categoricas_reg, drop_first=True, dtype=int)

# Separar X e y
y_reg = df_reg[COLUNA_ALVO_REG]
X_reg = df_reg.drop(columns=[COLUNA_ALVO_REG])
X_reg_train, X_reg_test, y_reg_train, y_reg_test = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

print("\n--- Treinando Modelos de REGRESSÃO ---")
# --- Modelo 1: Regressão Linear ---
print("\nModelo 1: Regressão Linear")
modelo_lr = LinearRegression()
modelo_lr.fit(X_reg_train, y_reg_train)
predicoes_lr = modelo_lr.predict(X_reg_test)
mse_lr = mean_squared_error(y_reg_test, predicoes_lr)
r2_lr = r2_score(y_reg_test, predicoes_lr)
print(f"  - Erro Quadrático Médio (MSE): {mse_lr:.2f}")
print(f"  - Coeficiente R²: {r2_lr:.2f} (quanto mais próximo de 1.0, melhor)")

# --- Modelo 2: Random Forest Regressor ---
print("\nModelo 2: Random Forest Regressor")
modelo_rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
modelo_rf_reg.fit(X_reg_train, y_reg_train)
predicoes_rf_reg = modelo_rf_reg.predict(X_reg_test)
mse_rf_reg = mean_squared_error(y_reg_test, predicoes_rf_reg)
r2_rf_reg = r2_score(y_reg_test, predicoes_rf_reg)
print(f"  - Erro Quadrático Médio (MSE): {mse_rf_reg:.2f}")
print(f"  - Coeficiente R²: {r2_rf_reg:.2f} (quanto mais próximo de 1.0, melhor)")

print("\n--- Conclusão Parte 1: Os resultados de R² negativos indicam que NÃO HÁ correlação preditiva para o prejuízo financeiro. ---")


# ==============================================================================
# PARTE 2: MODELO DE CLASSIFICAÇÃO (Prever "Attack Type")
# ==============================================================================
print("\n" + "="*70)
print("--- PARTE 2: MODELO DE CLASSIFICAÇÃO (Prever Tipo de Ataque) ---")
print("="*70)

# --- Pré-processamento para Classificação ---
# O ALVO agora é 'Attack Type'
COLUNA_ALVO_CLASS = "Attack Type"

# 'Financial Loss' agora é uma FEATURE, não o alvo.
# As colunas categóricas são as mesmas, exceto a 'Attack Type', que é o nosso alvo.
colunas_categoricas_class = [
    'Attack Source', 'Country', 'Defense Mechanism Used', 
    'Security Vulnerability Type', 'Target Industry', 'Year'
]
df_class = pd.get_dummies(df_original, columns=colunas_categoricas_class, drop_first=True, dtype=int)

# Separar X e y
y_class = df_class[COLUNA_ALVO_CLASS]
# Removemos a coluna alvo ('Attack Type') de nossas features
X_class = df_class.drop(columns=[COLUNA_ALVO_CLASS])
X_class_train, X_class_test, y_class_train, y_class_test = train_test_split(X_class, y_class, test_size=0.2, random_state=42, stratify=y_class)

print("\n--- Treinando Modelos de CLASSIFICAÇÃO ---")

# --- Modelo 1: Regressão Logística ---
print("\nModelo 1: Regressão Logística")
# Aumentar max_iter para garantir que o modelo convirja
modelo_log = LogisticRegression(max_iter=1000, random_state=42)
modelo_log.fit(X_class_train, y_class_train)
predicoes_log = modelo_log.predict(X_class_test)
acc_log = accuracy_score(y_class_test, predicoes_log)
print(f"  - Acurácia: {acc_log * 100:.2f}% (quanto mais próximo de 100%, melhor)")

# --- Modelo 2: Random Forest Classifier ---
print("\nModelo 2: Random Forest Classifier")
modelo_rf_class = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
modelo_rf_class.fit(X_class_train, y_class_train)
predicoes_rf_class = modelo_rf_class.predict(X_class_test)
acc_rf_class = accuracy_score(y_class_test, predicoes_rf_class)
print(f"  - Acurácia: {acc_rf_class * 100:.2f}% (quanto mais próximo de 100%, melhor)")

print("\n--- Conclusão Parte 2: Os modelos de classificação apresentam resultados muito mais promissores. ---")


# ==============================================================================
# ETAPA FINAL: SALVAR O MELHOR MODELO PARA A APLICAÇÃO WEB
# ==============================================================================
print("\n" + "="*70)
print("--- ETAPA FINAL: Salvando o melhor modelo ---")
print("="*70)

# Com base nos resultados, o Random Forest Classifier é o nosso modelo escolhido.
try:
    joblib.dump(modelo_rf_class, CAMINHO_MODELO_SALVO)
    print(f"Modelo de Classificação (Random Forest) salvo com sucesso em:")
    print(f"{CAMINHO_MODELO_SALVO.resolve()}")
except Exception as e:
    print(f"Erro ao salvar o modelo: {e}")

print("\n--- Script de Treinamento Concluído ---")