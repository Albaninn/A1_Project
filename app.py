import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import joblib 
import matplotlib.pyplot as plt 
import seaborn as sns           

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E CAMINHOS
# ==============================================================================
st.set_page_config(layout="wide", page_title="Análise de CyberSecurity")

# --- Definição de Caminhos ---
caminho_projeto = Path(".") 
caminho_pasta_csv = caminho_projeto / "CyberSec"
caminho_db = caminho_pasta_csv / "CyberSec.db" 
NOME_TABELA = 'CyberSec_data'
CAMINHO_MODELO = caminho_pasta_csv / 'modelo_classificador.pkl'

# ==============================================================================
# FUNÇÕES DE CACHE
# ==============================================================================
@st.cache_resource
def carregar_modelo(caminho):
    print(f"Carregando modelo de: {caminho}")
    try:
        modelo = joblib.load(caminho)
        return modelo
    except FileNotFoundError:
        return None

@st.cache_data
def carregar_dados_completos(db_path, query):
    print(f"Carregando dados do banco: {db_path}")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==============================================================================
# CARREGAMENTO INICIAL
# ==============================================================================
modelo = carregar_modelo(CAMINHO_MODELO)
df_original = carregar_dados_completos(caminho_db, f"SELECT * FROM {NOME_TABELA}")

# Listas de colunas para os seletores do gráfico dinâmico
colunas_categoricas_plot = [
    'Attack Source', 'Attack Type', 'Country', 'Defense Mechanism Used', 
    'Security Vulnerability Type', 'Target Industry', 'Year'
]
colunas_numericas_plot = [
    'Financial Loss (in Million $)', 'Incident Resolution Time (in Hours)', 'Number of Affected Users'
]

# ==============================================================================
# INTERFACE DO USUÁRIO (Sidebar de Navegação)
# ==============================================================================
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Selecione uma página:", ["Análise Exploratória", "Simulador de Predição"])

# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# PÁGINA 1: ANÁLISE EXPLORATÓRIA
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
if pagina == "Análise Exploratória":
    st.title("Painel de Análise Exploratória de Incidentes")
    st.write("Visualizações sobre os dados de incidentes de segurança.")

    # --- Gráfico 1: Impacto Financeiro por Tipo de Ataque ---
    st.header("Gráfico 1: Impacto Financeiro Total por Tipo de Ataque")
    try:
        df_loss = df_original.groupby("Attack Type")["Financial Loss (in Million $)"].sum().reset_index()
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        sns.barplot(data=df_loss, x="Attack Type", y="Financial Loss (in Million $)", palette="viridis", ax=ax1)
        ax1.set_title('Impacto Financeiro Total por Tipo de Ataque', fontsize=16)
        ax1.set_xlabel('Tipo de Ataque (Código)', fontsize=12)
        ax1.set_ylabel('Prejuízo Total (em Milhões de $)', fontsize=12)
        st.pyplot(fig1)
    except Exception as e:
        st.error(f"Erro ao gerar Gráfico 1: {e}")

    # --- Gráfico 2: Relação Usuários Afetados vs. Prejuízo ---
    st.header("Gráfico 2: Relação entre Usuários Afetados e Prejuízo")
    try:
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        sns.regplot(data=df_original, x="Number of Affected Users", y="Financial Loss (in Million $)", scatter_kws={'alpha':0.5}, line_kws={'color':'red'}, ax=ax2)
        ax2.set_title('Relação entre Usuários Afetados e Prejuízo Financeiro', fontsize=16)
        ax2.set_xlabel('Número de Usuários Afetados', fontsize=12)
        ax2.set_ylabel('Prejuízo (em Milhões de $)', fontsize=12)
        st.pyplot(fig2)
    except Exception as e:
        st.error(f"Erro ao gerar Gráfico 2: {e}")

    # --- Gráfico 3: Distribuição do Tempo de Resolução ---
    st.header("Gráfico 3: Distribuição do Tempo de Resolução de Incidentes")
    try:
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        sns.histplot(df_original["Incident Resolution Time (in Hours)"], kde=True, bins=30, ax=ax3)
        ax3.set_title('Distribuição do Tempo de Resolução de Incidentes', fontsize=16)
        ax3.set_xlabel('Tempo de Resolução (em Horas)', fontsize=12)
        ax3.set_ylabel('Frequência (Nº de Incidentes)', fontsize=12)
        st.pyplot(fig3)
    except Exception as e:
        st.error(f"Erro ao gerar Gráfico 3: {e}")

    # --- GRÁFICO 4: GERADOR DE GRÁFICO DINÂMICO (NOVO) ---
    st.header("Gráfico 4: Gerador de Gráfico Dinâmico")
    st.write("Crie seu próprio gráfico de colunas selecionando as variáveis.")
    
    col_x = st.selectbox("Selecione a Categoria (Eixo X):", colunas_categoricas_plot, index=1)
    col_y = st.selectbox("Selecione o Valor (Eixo Y):", colunas_numericas_plot, index=0)
    agregacao = st.radio("Selecione a Agregação:", ("Soma", "Média"), horizontal=True)

    try:
        if agregacao == "Soma":
            df_dynamic = df_original.groupby(col_x)[col_y].sum().reset_index()
            titulo_grafico = f'Soma de "{col_y}" por "{col_x}"'
        else:
            df_dynamic = df_original.groupby(col_x)[col_y].mean().reset_index()
            titulo_grafico = f'Média de "{col_y}" por "{col_x}"'
        
        # Cria o gráfico
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        sns.barplot(data=df_dynamic, x=col_x, y=col_y, palette="coolwarm", ax=ax4)
        ax4.set_title(titulo_grafico, fontsize=16)
        ax4.set_xlabel(col_x, fontsize=12)
        ax4.set_ylabel(f"{agregacao} de {col_y}", fontsize=12)
        st.pyplot(fig4)

    except Exception as e:
        st.error(f"Erro ao gerar Gráfico Dinâmico: {e}")


# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# PÁGINA 2: SIMULADOR DE PREDIÇÃO
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
elif pagina == "Simulador de Predição":
    st.title("Simulador para Predição de Tipo de Ataque")
    st.info("Preencha os dados do incidente. Campos deixados em branco usarão o valor mais neutro (mediano/comum) para a predição.")

    if modelo is None:
        st.error(f"Erro: Arquivo do modelo ('{CAMINHO_MODELO.name}') não encontrado. "
                 "Execute o script '02_treinar_modelo.py' primeiro.")
    else:
        # --- Cálculo dos Valores Padrão (Median/Mode) ---
        defaults = {
            'financial_loss': df_original["Financial Loss (in Million $)"].median(),
            'resolution_time': df_original["Incident Resolution Time (in Hours)"].median(),
            'affected_users': df_original["Number of Affected Users"].median(),
            'attack_source': df_original['Attack Source'].mode()[0],
            'country': df_original['Country'].mode()[0],
            'defense': df_original['Defense Mechanism Used'].mode()[0],
            'vulnerability': df_original['Security Vulnerability Type'].mode()[0],
            'industry': df_original['Target Industry'].mode()[0],
            'year': df_original['Year'].mode()[0]
        }
        
        # --- Formulário de Input ---
        with st.form("prediction_form"):
            st.header("Insira as Características do Incidente:")
            col1, col2 = st.columns(2)

            with col1:
                # *** ALTERAÇÃO 1: Placeholder removido ***
                financial_loss = st.number_input(
                    "Prejuízo Financeiro (em Milhões $)", 
                    min_value=0.0, max_value=100.0, value=None
                )
                resolution_time = st.number_input(
                    "Tempo de Resolução (em Horas)", 
                    min_value=1, max_value=72, value=None
                )
                affected_users = st.number_input(
                    "Nº de Usuários Afetados", 
                    min_value=0, max_value=1000000, value=None
                )
            
            with col2:
                # *** ALTERAÇÃO 2: Texto do campo opcional alterado ***
                op_nao_informar = "Não Especificar"
                attack_source = st.selectbox(
                    "Fonte do Ataque (Código):", [op_nao_informar] + sorted(df_original['Attack Source'].unique())
                )
                country = st.selectbox(
                    "País de Origem (Código):", [op_nao_informar] + sorted(df_original['Country'].unique())
                )
                defense = st.selectbox(
                    "Mecanismo de Defesa (Código):", [op_nao_informar] + sorted(df_original['Defense Mechanism Used'].unique())
                )
                vulnerability = st.selectbox(
                    "Vulnerabilidade (Código):", [op_nao_informar] + sorted(df_original['Security Vulnerability Type'].unique())
                )
                industry = st.selectbox(
                    "Indústria Alvo (Código):", [op_nao_informar] + sorted(df_original['Target Industry'].unique())
                )
                year = st.selectbox(
                    "Ano:", [op_nao_informar] + sorted(df_original['Year'].unique())
                )
            
            submitted = st.form_submit_button("Prever Tipo de Ataque")

        # --- Lógica de Predição ---
        if submitted:
            
            input_data = {
                'Attack Source': [defaults['attack_source'] if attack_source == op_nao_informar else attack_source],
                'Country': [defaults['country'] if country == op_nao_informar else country],
                'Defense Mechanism Used': [defaults['defense'] if defense == op_nao_informar else defense],
                'Financial Loss (in Million $)': [defaults['financial_loss'] if financial_loss is None else financial_loss],
                'Incident Resolution Time (in Hours)': [defaults['resolution_time'] if resolution_time is None else resolution_time],
                'Number of Affected Users': [defaults['affected_users'] if affected_users is None else affected_users],
                'Security Vulnerability Type': [defaults['vulnerability'] if vulnerability == op_nao_informar else vulnerability],
                'Target Industry': [defaults['industry'] if industry == op_nao_informar else industry],
                'Year': [defaults['year'] if year == op_nao_informar else year]
            }
            input_df = pd.DataFrame(input_data)
            
            # *** ALTERAÇÃO 3: Remoção do print dos valores intermediários ***
            # st.write("--- Valores Utilizados para Predição (após preencher campos vazios) ---")
            # st.dataframe(input_df)
            
            df_para_dummies = pd.concat([df_original.drop(columns=['Attack Type']), input_df], ignore_index=True)
            df_processado = pd.get_dummies(df_para_dummies, 
                                           columns=[
                                               'Attack Source', 'Country', 'Defense Mechanism Used', 
                                               'Security Vulnerability Type', 'Target Industry', 'Year'
                                           ], 
                                           drop_first=True, 
                                           dtype=int)
            
            input_final = df_processado.iloc[-1:]
            
            try:
                predicao = modelo.predict(input_final)
                predicao_proba = modelo.predict_proba(input_final)
                
                st.subheader("Resultado da Predição")
                st.success(f"O modelo previu que o **Tipo de Ataque** é: **{predicao[0]}**")
                
                st.write("Probabilidades para cada tipo de ataque:")
                df_proba = pd.DataFrame(predicao_proba, columns=modelo.classes_)
                st.dataframe(df_proba.transpose().rename(columns={0: 'Probabilidade (%)'}).mul(100).round(2))

            except Exception as e:
                st.error(f"Erro ao fazer a predição: {e}")
                st.error("Verifique se as colunas do modelo treinado correspondem às colunas do input.")