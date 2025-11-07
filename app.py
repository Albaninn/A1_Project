import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import joblib 
# import matplotlib.pyplot as plt
# import seaborn as sns
import plotly.express as px # <--- Graficos
from backend_tasks import processar_nova_base, treinar_novo_modelo 

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

caminho_pasta_csv.mkdir(exist_ok=True)

# ==============================================================================
# VERIFICAÇÃO INICIAL DE ARQUIVOS
# ==============================================================================
db_existe = caminho_db.exists()
modelo_existe = CAMINHO_MODELO.exists()
setup_necessario = not (db_existe and modelo_existe)

# ==============================================================================
# FUNÇÕES DE CACHE
# ==============================================================================
@st.cache_resource
def carregar_modelo(caminho):
    if not modelo_existe:
        print("Arquivo de modelo não encontrado. Pulando o carregamento.")
        return None
    print(f"Carregando modelo de: {caminho}")
    try:
        modelo = joblib.load(caminho)
        return modelo
    except FileNotFoundError:
        return None

@st.cache_data
def carregar_dados_completos(db_path, query):
    if not db_existe:
        return pd.DataFrame() 
        
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

# Listas de colunas (só as preenche se o df_original não estiver vazio)
colunas_categoricas_plot = []
colunas_numericas_plot = []
if not df_original.empty:
    colunas_categoricas_plot = [
        'Attack Source', 'Attack Type', 'Country', 'Defense Mechanism Used', 
        'Security Vulnerability Type', 'Target Industry', 'Year'
    ]
    colunas_numericas_plot = [
        'Financial Loss (in Million $)', 'Incident Resolution Time (in Hours)', 'Number of Affected Users'
    ]
    colunas_categoricas_plot = [col for col in colunas_categoricas_plot if col in df_original.columns]
    colunas_numericas_plot = [col for col in colunas_numericas_plot if col in df_original.columns]

# ==============================================================================
# INTERFACE DO USUÁRIO (Sidebar de Navegação)
# ==============================================================================
st.sidebar.title("Navegação")
pagina_opcoes = ["Atualizar Base de Dados", "Análise Exploratória", "Simulador de Predição"]
default_index = 0 if setup_necessario else 1 

if setup_necessario:
    st.sidebar.warning("Configuração necessária. Carregue uma base de dados para começar.")

pagina = st.sidebar.radio("Selecione uma página:", pagina_opcoes, index=default_index)


# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# PÁGINA 1: ATUALIZAR BASE DE DADOS
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
if pagina == "Atualizar Base de Dados":
    st.title("Atualizar Base de Dados e Re-treinar Modelo")
    
    st.warning("Atenção: Este processo irá substituir a base de dados e o modelo de ML existentes.")
    
    uploaded_file = st.file_uploader(
        "Selecione um arquivo .zip ou .csv",
        type=['zip', 'csv'],
        accept_multiple_files=False
    )
    
    if st.button("Processar e Treinar Nova Base"):
        if uploaded_file is not None:
            try:
                # --- Etapa 1: Processar a Base ---
                with st.spinner("Etapa 1/2: Processando nova base de dados... Isso pode levar vários minutos."):
                    sucesso_db, msg_db = processar_nova_base(
                        uploaded_file=uploaded_file,
                        db_path=caminho_db,
                        table_name=NOME_TABELA
                    )
                if not sucesso_db:
                    st.error(f"Falha ao processar a base: {msg_db}")
                else:
                    st.success(f"Etapa 1/2: {msg_db}")
                    
                    # --- Etapa 2: Treinar o Modelo ---
                    with st.spinner("Etapa 2/2: Treinando novo modelo de Machine Learning..."):
                        sucesso_ml, msg_ml = treinar_novo_modelo(
                            db_path=caminho_db,
                            table_name=NOME_TABELA,
                            model_save_path=CAMINHO_MODELO 
                        )
                    if not sucesso_ml:
                        st.error(f"Falha ao treinar o modelo: {msg_ml}")
                    else:
                        st.success(f"Etapa 2/2: {msg_ml}")
                        
                        st.info("Limpando cache e recarregando a aplicação...")
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        st.rerun() 

            except Exception as e:
                st.error(f"Um erro inesperado ocorreu: {e}")
        else:
            st.error("Por favor, selecione um arquivo para enviar.")

# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# PÁGINA 2: ANÁLISE EXPLORATÓRIA
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
elif pagina == "Análise Exploratória":
    st.title("Painel de Análise Exploratória de Incidentes")
    
    if setup_necessario or df_original.empty or not colunas_categoricas_plot or not colunas_numericas_plot:
        st.warning("Nenhum dado ou modelo encontrado. Por favor, carregue uma base de dados na página 'Atualizar Base de Dados'.")
    else:
        
        # ==============================================================================
        # SEÇÃO DE MÉTRICAS
        # ==============================================================================
        st.header("Resumo Geral da Base de Dados")

        total_linhas = df_original.shape[0]
        total_prejuizo = df_original['Financial Loss (in Million $)'].sum()
        tipos_ataque_unicos = sorted(df_original['Attack Type'].unique())
        paises_unicos = sorted(df_original['Country'].unique())
        
        tooltip_ataques = f"Códigos encontrados: {', '.join(map(str, tipos_ataque_unicos))}"
        tooltip_paises = f"Códigos encontrados: {', '.join(map(str, paises_unicos))}"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Incidentes", f"{total_linhas:,}")
        with col2:
            st.metric("Tipos de Ataque Únicos", f"{len(tipos_ataque_unicos)}", help=tooltip_ataques)
        with col3:
            st.metric("Países de Origem Únicos", f"{len(paises_unicos)}", help=tooltip_paises)
        with col4:
            st.metric("Prejuízo Total (Milhões $)", f"{total_prejuizo:,.2f}")
        st.divider() 

        # ==============================================================================
        # GRÁFICO DE MAPA (Coroplético com Plotly)
        # ==============================================================================
        st.subheader("Mapa de Frequência de Incidentes por País")
        
        MAPA_ISO = {
            'USA': 'USA', 'China': 'CHN', 'Russia': 'RUS', 'Brazil': 'BRA',
            'Germany': 'DEU', 'UK': 'GBR', 'India': 'IND', 'Australia': 'AUS',
            'Japan': 'JPN', 'France': 'FRA', 'Canada': 'CAN'
        }
        
        st.info("Nota: Este mapa traduz os códigos de país do seu dataset (ex: 'UK') para códigos ISO padrão (ex: 'GBR') para colorir o mapa-múndi.")

        try:
            contagem_paises = df_original['Country'].value_counts().reset_index()
            contagem_paises.columns = ['Country_Code', 'Contagem']
            contagem_paises['ISO_Code'] = contagem_paises['Country_Code'].map(MAPA_ISO)
            df_mapa = contagem_paises.dropna(subset=['ISO_Code'])

            if df_mapa.empty:
                st.warning("Não foi possível gerar o mapa. Nenhum dos códigos de país no seu dataset (ex: 'USA', 'China') "
                           "foi encontrado no `MAPA_ISO` dentro do `app.py`.")
            else:
                fig_mapa = px.choropleth(
                    df_mapa,
                    locations="ISO_Code",
                    color="Contagem",
                    hover_name="Country_Code",
                    color_continuous_scale=px.colors.sequential.YlOrRd,
                    title="Países por Frequência de Incidentes"
                )
                fig_mapa.update_layout(geo=dict(bgcolor='rgba(0,0,0,0)'), template='plotly_dark')
                st.plotly_chart(fig_mapa, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar o Gráfico de Mapa: {e}")
        st.divider()

        # ==============================================================================
        # SEÇÃO DE TABELAS DE FREQUÊNCIA
        # ==============================================================================
        st.subheader("Distribuição das Principais Categorias (Contagem e %)")
        col_t1, col_t2 = st.columns(2) 

        with col_t1:
            st.write("Por Tipo de Ataque:")
            df_dist_ataque = df_original['Attack Type'].value_counts().reset_index()
            df_dist_ataque.columns = ['Attack Type', 'Contagem']
            df_dist_ataque['Percentual (%)'] = (df_dist_ataque['Contagem'] / total_linhas * 100).round(2)
            df_dist_ataque.index = pd.RangeIndex(start=1, stop=len(df_dist_ataque) + 1, step=1)
            st.dataframe(df_dist_ataque, use_container_width=True)
        
        with col_t2:
            st.write("Por Indústria Alvo:")
            df_dist_industry = df_original['Target Industry'].value_counts().reset_index()
            df_dist_industry.columns = ['Target Industry', 'Contagem']
            df_dist_industry['Percentual (%)'] = (df_dist_industry['Contagem'] / total_linhas * 100).round(2)
            df_dist_industry.index = pd.RangeIndex(start=1, stop=len(df_dist_industry) + 1, step=1)
            st.dataframe(df_dist_industry, use_container_width=True)
        st.divider() 
        
        # ==============================================================================
        # SEÇÃO DE GRÁFICOS DETALHADOS (AGORA COM PLOTLY)
        # ==============================================================================
        st.header("Análises Gráficas Detalhadas")

        # --- Gráfico 1: Impacto Financeiro por Tipo de Ataque ---
        st.subheader("Impacto Financeiro Total por Tipo de Ataque") 
        try:
            df_loss = df_original.groupby("Attack Type", as_index=False)["Financial Loss (in Million $)"].sum()
            fig1 = px.bar(
                df_loss,
                x="Attack Type",
                y="Financial Loss (in Million $)",
                title="Impacto Financeiro Total por Tipo de Ataque",
                template="plotly_dark",
                color="Financial Loss (in Million $)",
                labels={'Attack Type': 'Tipo de Ataque (Código)', 'Financial Loss (in Million $)': 'Prejuízo Total (em Milhões de $)'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar Gráfico 1: {e}")

        # --- Gráfico 2: Relação Usuários Afetados vs. Prejuízo ---
        st.subheader("Relação entre Usuários Afetados e Prejuízo")
        try:
            fig2 = px.scatter(
                df_original,
                x="Number of Affected Users",
                y="Financial Loss (in Million $)",
                title="Relação entre Usuários Afetados e Prejuízo Financeiro",
                template="plotly_dark",
                color="Attack Type", # Colore por tipo de ataque para mais insight
                trendline="ols",     # Adiciona linha de regressão
                labels={'Number of Affected Users': 'Número de Usuários Afetados', 'Financial Loss (in Million $)': 'Prejuízo (em Milhões de $)'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar Gráfico 2: {e}")

        # --- Gráfico 3: Distribuição do Tempo de Resolução ---
        st.subheader("Distribuição do Tempo de Resolução de Incidentes")
        try:
            fig3 = px.histogram(
                df_original,
                x="Incident Resolution Time (in Hours)",
                title="Distribuição do Tempo de Resolução de Incidentes",
                template="plotly_dark",
                nbins=30,
                marginal="box", # Adiciona um box plot no topo
                labels={'Incident Resolution Time (in Hours)': 'Tempo de Resolução (em Horas)', 'count': 'Frequência (Nº de Incidentes)'}
            )
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar Gráfico 3: {e}")

        # --- GRÁFICO 4: GERADOR DE GRÁFICO DINÂMICO ---
        st.subheader("Gerador de Gráfico Dinâmico")
        st.write("Crie seu próprio gráfico de colunas selecionando as variáveis.")
        
        col_x = st.selectbox("Selecione a Categoria (Eixo X):", colunas_categoricas_plot, index=1 if len(colunas_categoricas_plot) > 1 else 0)
        col_y = st.selectbox("Selecione o Valor (Eixo Y):", colunas_numericas_plot, index=0)
        agregacao = st.radio("Selecione a Agregação:", ("Soma", "Média"), horizontal=True)

        try:
            if agregacao == "Soma":
                df_dynamic = df_original.groupby(col_x, as_index=False)[col_y].sum()
                titulo_grafico = f'Soma de "{col_y}" por "{col_x}"'
            else:
                df_dynamic = df_original.groupby(col_x, as_index=False)[col_y].mean()
                titulo_grafico = f'Média de "{col_y}" por "{col_x}"'
            
            fig4 = px.bar(
                df_dynamic,
                x=col_x,
                y=col_y,
                title=titulo_grafico,
                template="plotly_dark",
                color=col_y,
                labels={col_x: col_x, col_y: f"{agregacao} de {col_y}"}
            )
            st.plotly_chart(fig4, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao gerar Gráfico Dinâmico: {e}")


# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# PÁGINA 3: SIMULADOR DE PREDIÇÃO
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
elif pagina == "Simulador de Predição":
    st.title("Simulador para Predição de Tipo de Ataque")
    
    if setup_necessario or modelo is None or df_original.empty:
        st.error("Modelo ou banco de dados não encontrado. "
                 "Por favor, carregue e processe uma nova base na página 'Atualizar Base de Dados' primeiro.")
    else:
        st.info("Preencha os dados do incidente. Campos deixados em branco usarão o valor mais neutro (mediano/comum) para a predição.")
        
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
                op_nao_informar = "Não Especificar"
                # Garante que as opções do selectbox sejam únicas
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
            
            # Prepara os dados para o One-Hot Encoding
            df_para_dummies = pd.concat([df_original.drop(columns=['Attack Type']), input_df], ignore_index=True)
            df_processado = pd.get_dummies(df_para_dummies, 
                                           columns=[
                                               'Attack Source', 'Country', 'Defense Mechanism Used', 
                                               'Security Vulnerability Type', 'Target Industry', 'Year'
                                           ], 
                                           drop_first=True, 
                                           dtype=int)
            
            # Pega apenas a última linha (input do usuário)
            input_final = df_processado.iloc[-1:]
            
            try:
                predicao = modelo.predict(input_final)
                predicao_proba = modelo.predict_proba(input_final)
                
                st.subheader("Resultado da Predição")
                st.success(f"O modelo previu que o **Tipo de Ataque** é: **{predicao[0]}**")
                
                st.write("Probabilidades para cada tipo de ataque:")
                df_proba = pd.DataFrame(predicao_proba, columns=modelo.classes_)
                df_proba.index = pd.RangeIndex(start=1, stop=len(df_proba) + 1, step=1)
                st.dataframe(df_proba.transpose().rename(columns={1: 'Probabilidade (%)'}).mul(100).round(2))

            except Exception as e:
                st.error(f"Erro ao fazer a predição: {e}")
                st.error("Verifique se as colunas do modelo treinado correspondem às colunas do input.")