import sqlite3
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.ensemble import IsolationForest # Import para o modelo de ML
import glob # Biblioteca para encontrar arquivos que correspondem a um padrão
import zipfile # Biblioteca para manipular arquivos ZIP

from datetime import datetime

horario_inicio = datetime.now()
horario_inicio_formatado = horario_inicio.strftime("%H:%M:%S")
print(f"Início: {horario_inicio_formatado}")

# ==============================================================================
# DEFINIÇÃO DE CAMINHOS
# ==============================================================================
# Caminho da pasta do projeto principal
caminho_projeto = Path(".")

# Caminho do arquivo ZIP
caminho_zip = caminho_projeto / "CyberSec.zip"
#caminho_zip = "CyberSec.zip"

# O caminho para a PASTA onde os arquivos CSV ficarão
caminho_pasta_csv = caminho_projeto / "CyberSec"
#caminho_pasta_csv = "CyberSec"

# Caminho para o arquivo do banco de dados (agora dentro da pasta dos CSVs)
caminho_db = caminho_pasta_csv / "CyberSec.db" 
NOME_TABELA = 'CyberSec_data' # Nome da nossa tabela no DB
NOME_TABELA_NOVA = f"{NOME_TABELA}_new"

# ==============================================================================
# ETAPA 0: DESCOMPACTAR OS DADOS (SE NECESSÁRIO)
# ==============================================================================
print(f"--- Verificando a necessidade de descompactação ---")
# Cria a pasta de destino se ela não existir
caminho_pasta_csv.mkdir(exist_ok=True)
# Verifica se já existem arquivos CSV na pasta de destino
arquivos_csv_existentes = glob.glob(str(caminho_pasta_csv / "*.csv"))

if not arquivos_csv_existentes and caminho_zip.exists():
    print(f"Arquivos CSV não encontrados. Descompactando '{caminho_zip.name}' para '{caminho_pasta_csv}'...")
    with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
        zip_ref.extractall(caminho_pasta_csv)
    print("Arquivos descompactados com sucesso!")
elif not arquivos_csv_existentes and not caminho_zip.exists():
    print(f"ERRO: A pasta '{caminho_pasta_csv}' está vazia e o arquivo '{caminho_zip.name}' não foi encontrado.")
    # Encerra o script se não houver dados para processar
    exit()
else:
    print("Arquivos CSV já existem na pasta. Pulando a descompactação.")

# ==============================================================================
# VERIFICAÇÃO E CRIAÇÃO DO BANCO DE DADOS (SE NECESSÁRIO)
# ==============================================================================

# Verifica se o arquivo de banco de dados já existe.
if caminho_db.exists():
    print(f"\nO banco de dados '{caminho_db.name}' já existe. Pulando a etapa de criação.")
else:
    print(f"\nO banco de dados '{caminho_db.name}' não foi encontrado. Iniciando o processo de criação...")

    # ==============================================================================
    # 1. PRÉ-ANÁLISE: DESCOBRIR TODAS AS COLUNAS DE TODOS OS ARQUIVOS
    # ==============================================================================
    print("\n--- Analisando cabeçalhos de todos os arquivos... ---")
    lista_arquivos_csv = glob.glob(str(caminho_pasta_csv / "*.csv"))
    colunas_master = set()

    for arquivo in lista_arquivos_csv:
        # Lê apenas o cabeçalho (primeira linha) para pegar os nomes das colunas
        df_header = pd.read_csv(arquivo, nrows=0, low_memory=False)
        # Limpa os nomes das colunas
        df_header.columns = df_header.columns.str.strip().str.replace('\n', '')
        # Adiciona as colunas deste arquivo ao nosso conjunto de colunas mestras
        colunas_master.update(df_header.columns)

    # Converte o conjunto para uma lista para manter a ordem
    master_columns_list = sorted(list(colunas_master))
    print(f"Análise concluída. Total de colunas únicas encontradas: {len(master_columns_list)}")

    # ==============================================================================
    # 2. CRIAÇÃO DA TABELA MESTRA E INSERÇÃO DOS DADOS
    # ==============================================================================
    conn = sqlite3.connect(caminho_db)

    # Cria a tabela com a estrutura completa, mas vazia
    # Usamos um DataFrame vazio com todas as colunas mestras para definir o schema
    df_vazio = pd.DataFrame(columns=master_columns_list)
    df_vazio.to_sql(NOME_TABELA, conn, if_exists='replace', index=False)
    print(f"\nTabela '{NOME_TABELA}' criada com sucesso no banco de dados.")

    # Agora, processamos os arquivos e inserimos os dados
    for arquivo in lista_arquivos_csv:
        print(f"\nProcessando o arquivo em pedaços: {Path(arquivo).name}...")
        
        chunk_reader = pd.read_csv(arquivo, chunksize=100000, low_memory=False)
        
        for i, chunk in enumerate(chunk_reader):
            print(f"  - Preparando e escrevendo pedaço {i+1}...")
            
            # Limpa os nomes das colunas do chunk atual
            chunk.columns = chunk.columns.str.strip().str.replace('\n', '')
            
            # *** A MÁGICA ACONTECE AQUI ***
            # Reindexa o chunk para que ele tenha EXATAMENTE as mesmas colunas da tabela mestra.
            # Colunas que existem no chunk mas não na master são descartadas (se houver).
            # Colunas que existem na master mas não no chunk são adicionadas com valor Nulo (NaN).
            chunk_reindexado = chunk.reindex(columns=master_columns_list)
            
            # Anexa o chunk ajustado à tabela no banco de dados
            chunk_reindexado.to_sql(NOME_TABELA, conn, if_exists='append', index=False)

    conn.close()

    print(f"\n\n--- Processo Concluído! ---")
    print(f"Todos os dados foram salvos com sucesso na tabela '{NOME_TABELA}'.")

# ==============================================================================
# EXIBIÇÃO DO ESQUEMA DA TABELA (SEMPRE EXECUTA)
# ==============================================================================
print("\n" + "="*70)
print(f"--- Lendo e exibindo o esquema da tabela '{NOME_TABELA}' ---")
try:
    conn = sqlite3.connect(caminho_db)
    query = f"PRAGMA table_info('{NOME_TABELA}');"
    schema_df = pd.read_sql_query(query, conn)
    conn.close()

    print("\n--- Colunas e Tipos de Dados ---")
    pd.set_option('display.max_rows', None)
    print(schema_df[['name', 'type']])

except Exception as e:
    print(f"\nOcorreu um erro ao ler o esquema: {e}")

# ==============================================================================
# ANÁLISE DE NULOS E SUGESTÃO DE TIPOS
# ==============================================================================
print("\n" + "="*70)
print("--- Análise de Amostra: Verificação de Nulos e Sugestão de Tipos ---")
print("Analisando uma amostra dos dados para otimizar a performance...")

try:
    conn = sqlite3.connect(caminho_db)
    # Para não carregar tudo, pegamos uma amostra de 200.000 linhas
    SAMPLE_SIZE = 200000
    query_amostra = f"SELECT * FROM {NOME_TABELA} LIMIT {SAMPLE_SIZE}"
    df_amostra = pd.read_sql_query(query_amostra, conn)
    conn.close()

    print(f"\nAmostra de {len(df_amostra)} linhas carregada com sucesso.")

    # --- 1. Validação de Nulos e Vazios ---
    print("\n--- Verificando colunas com valores nulos ou vazios na amostra ---")
    colunas_com_nulos = []
    for col in df_amostra.columns:
        # Conta tanto nulos (NaN) quanto strings vazias ''
        nulos_count = df_amostra[col].isnull().sum()
        if nulos_count > 0:
            print(f"- Coluna '{col}': {nulos_count} valores nulos/vazios encontrados.")
            colunas_com_nulos.append(col)
    
    if not colunas_com_nulos:
        print("Nenhuma coluna com valores nulos ou vazios foi encontrada na amostra.")

    # --- 2. Análise e Sugestão de Tipos de Dados ---
    print("\n--- Analisando e sugerindo tipos de dados corretos ---")
    dtype_sugerido = {}
    for col in df_amostra.columns:
        tipo_original = df_amostra[col].dtype
        # Tenta converter a coluna para um tipo numérico.
        # errors='coerce' transforma o que não for número em NaN (Nulo)
        coluna_convertida = pd.to_numeric(df_amostra[col], errors='coerce')
        novo_tipo = coluna_convertida.dtype

        # Se o tipo mudou de 'object' (texto) para numérico, a conversão foi um sucesso!
        if tipo_original == 'object' and novo_tipo != 'object':
            print(f"- Coluna '{col}': pode ser convertida de TEXT para {novo_tipo}.")
            # Se não houver valores nulos após a conversão, pode ser inteiro
            if coluna_convertida.isnull().sum() == 0:
                dtype_sugerido[col] = 'integer'
            else:
                dtype_sugerido[col] = 'float'
        else:
            # Mantém o tipo original se não for conversível ou se já for numérico
            dtype_sugerido[col] = tipo_original

    print("\n--- Dicionário de Tipos Sugerido para seus próximos scripts ---")
    print("Você pode usar este dicionário para carregar os dados já com os tipos corretos:")
    # Formata o dicionário para ficar fácil de copiar e colar
    dtype_map_str = "dtype_map = {\n"
    for col, tipo in dtype_sugerido.items():
        dtype_map_str += f"    '{col}': '{str(tipo)}',\n"
    dtype_map_str += "}"
    print(dtype_map_str)

except Exception as e:
    print(f"\nOcorreu um erro durante a análise da amostra: {e}")

# ==============================================================================
# CORREÇÃO DOS TIPOS DE DADOS NO BANCO DE DADOS (SE NECESSÁRIO)
# ==============================================================================
print("\n" + "="*70)
print(f"--- ETAPA FINAL: Verificando e corrigindo os tipos de dados na tabela '{NOME_TABELA}' ---")

try:
        
    horario_inicio_edidb = datetime.now()
    horario_inicio_formatado_edidb = horario_inicio_edidb.strftime("%H:%M:%S")
    conn = sqlite3.connect(caminho_db)
    
    # Verifica os tipos atuais da tabela principal
    schema_atual_df = pd.read_sql_query(f"PRAGMA table_info('{NOME_TABELA}');", conn)
    tipos_atuais = dict(zip(schema_atual_df['name'], schema_atual_df['type']))

    # Se a maioria das colunas (exceto 'Label', 'Timestamp', etc.) ainda for TEXT, a conversão é necessária.
    # Contamos quantos tipos 'TEXT' existem.
    text_count = sum(1 for tipo in tipos_atuais.values() if tipo == 'TEXT')

    # Se menos de 10 colunas são TEXT, assumimos que a conversão já foi feita.
    if text_count < 10:
        print("\nTipos de dados já parecem estar corrigidos. Nenhuma ação necessária.")
        conn.close()
    else:
        print("\nTipos de dados precisam ser corrigidos. Iniciando o processo de conversão (pode levar alguns minutos)...")
        
        # 1. Analisar uma amostra para definir o schema ideal
        print("\nPasso 1/5: Analisando amostra para definir os tipos de dados corretos...")
        SAMPLE_SIZE = 200000
        df_amostra = pd.read_sql_query(f"SELECT * FROM {NOME_TABELA} LIMIT {SAMPLE_SIZE}", conn)
        
        dtype_map = {}
        for col in df_amostra.columns:
            try:
                coluna_convertida = pd.to_numeric(df_amostra[col], errors='coerce')
                if df_amostra[col].dtype == 'object' and coluna_convertida.dtype != 'object':
                    # Usa 'INTEGER' se não houver casas decimais na amostra, senão 'REAL' (float)
                    if (coluna_convertida.dropna() % 1 == 0).all():
                         dtype_map[col] = 'INTEGER'
                    else:
                         dtype_map[col] = 'REAL'
                else:
                    dtype_map[col] = 'TEXT' # Mantém como texto se não for conversível
            except (ValueError, TypeError):
                 dtype_map[col] = 'TEXT'

        print("Tipos de dados ideais definidos com sucesso.")

        # 2. Criar a nova tabela com os tipos corretos
        print(f"\nPasso 2/5: Criando nova tabela '{NOME_TABELA_NOVA}' com os tipos corretos...")

        # Garante que qualquer resquício de uma execução anterior seja limpo
        print("  - Verificando e limpando resquícios de execuções anteriores...")
        conn.execute(f"DROP TABLE IF EXISTS {NOME_TABELA_NOVA}")

        # Cria a instrução SQL para a nova tabela
        create_table_sql = f"CREATE TABLE {NOME_TABELA_NOVA} ({', '.join([f'\"{col}\" {tipo}' for col, tipo in dtype_map.items()])})"
        conn.execute(create_table_sql)
        print("Nova tabela criada.")

        # 3. Copiar dados da tabela antiga para a nova em chunks (para não usar muita memória)
        print(f"\nPasso 3/5: Copiando dados para a nova tabela (isso pode ser demorado)...")
        chunk_reader = pd.read_sql_query(f"SELECT * FROM {NOME_TABELA}", conn, chunksize=100000)
        
        for i, chunk in enumerate(chunk_reader):
            print(f"  - Processando e inserindo o chunk {i+1}...")
            # Garante que os tipos do chunk estão corretos antes de inserir
            chunk_convertido = chunk.astype({col: str for col in chunk.columns if dtype_map[col] == 'TEXT'})
            chunk_convertido.to_sql(NOME_TABELA_NOVA, conn, if_exists='append', index=False)
        print("Cópia de dados concluída.")

        # 4. Apagar a tabela antiga
        print(f"\nPasso 4/5: Apagando a tabela antiga '{NOME_TABELA}'...")
        conn.execute(f"DROP TABLE {NOME_TABELA}")
        print("Tabela antiga apagada.")

        # 5. Renomear a nova tabela
        print(f"\nPasso 5/5: Renomeando '{NOME_TABELA_NOVA}' para '{NOME_TABELA}'...")
        conn.execute(f"ALTER TABLE {NOME_TABELA_NOVA} RENAME TO {NOME_TABELA}")
        print("Tabela renomeada com sucesso!")

        # Finaliza a transação
        conn.commit()
        conn.close()

        print("\n\n--- Processo de Conversão Concluído! ---")
        print("O banco de dados foi otimizado com os tipos de dados corretos.")

        # Mostra o novo schema para confirmação
        print("\n--- Novo Esquema da Tabela ---")
        conn = sqlite3.connect(caminho_db)
        schema_final_df = pd.read_sql_query(f"PRAGMA table_info('{NOME_TABELA}');", conn)
        conn.close()
        print(schema_final_df[['name', 'type']])

        horario_fim_edidb = datetime.now()
        horario_fim_formatado_edidb = horario_fim_edidb.strftime("%H:%M:%S")
        
        print(f"Início: {horario_inicio_formatado_edidb} | Fim: {horario_fim_formatado_edidb}")

except Exception as e:
    print(f"\nOcorreu um erro durante a otimização do banco de dados: {e}")

# ==============================================================================
# ANÁLISE DE CATEGORIAS RARAS (ANOMALIAS CATEGÓRICAS)
# ==============================================================================
print("\n" + "="*70)
print("\n--- Análise de Frequência para Detecção de Anomalias Categóricas ---")

try:
    conn = sqlite3.connect(caminho_db)
    df_full = pd.read_sql_query(f"SELECT * FROM {NOME_TABELA}", conn)
    conn.close()

    # Lista das colunas categóricas que queremos analisar
    colunas_categoricas = [
        'Attack Source', 'Attack Type', 'Country', 'Defense Mechanism Used', 
        'Security Vulnerability Type', 'Target Industry', 'Year'
    ]

    # Define um limite para considerar uma categoria como "rara"
    limite_contagem_rara = 5 # Menos de 5 ocorrências

    for col in colunas_categoricas:
        print(f"\n--- Análise da Coluna: '{col}' ---")
        
        # Calcula a contagem e o percentual de cada categoria
        contagens = df_full[col].value_counts()
        percentuais = df_full[col].value_counts(normalize=True).mul(100).round(2)
        
        # Cria um DataFrame para exibir os resultados de forma organizada
        df_frequencia = pd.DataFrame({'Contagem': contagens, 'Percentual (%)': percentuais})
        
        print("Distribuição de todas as categorias:")
        print(df_frequencia)
        
        # Filtra para encontrar as categorias raras (nossas anomalias)
        anomalias_categoricas = df_frequencia[df_frequencia['Contagem'] < limite_contagem_rara]
        
        if not anomalias_categoricas.empty:
            print(f"\n>> ANOMALIAS ENCONTRADAS (Categorias com menos de {limite_contagem_rara} ocorrências):")
            print(anomalias_categoricas)
        else:
            print(f"\n>> Nenhuma categoria rara encontrada nesta coluna com o limite de {limite_contagem_rara} ocorrências.")

except Exception as e:
    print(f"Ocorreu um erro durante a análise de anomalias categóricas: {e}")

# ==============================================================================
# ANÁLISE DE ANOMALIAS MULTIVARIADAS (CONEXÃO ENTRE COLUNAS)
# ==============================================================================
print("\n" + "="*70)
print("\n--- Análise de Anomalias Multivariadas (baseada em conexões entre colunas) ---")

try:
    conn = sqlite3.connect(caminho_db)
    df_full = pd.read_sql_query(f"SELECT * FROM {NOME_TABELA}", conn)
    conn.close()
    
    # --- Técnica 1: Análise Visual (Gráficos de Dispersão Agrupados) ---
    print("\n--- Técnica 1: Gerando análise visual de anomalias de grupo...")
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(14, 9))
    sns.scatterplot(data=df_full, x="Number of Affected Users", y="Financial Loss (in Million $)", hue="Attack Type", palette="viridis", alpha=0.8, s=100)
    plt.title('Prejuízo vs. Usuários Afetados, Agrupado por Tipo de Ataque', fontsize=16)
    plt.xlabel('Número de Usuários Afetados', fontsize=12)
    plt.ylabel('Prejuízo Financeiro (em Milhões de $)', fontsize=12)
    plt.legend(title='Tipo de Ataque', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    caminho_salvar5 = caminho_pasta_csv / "grafico_5_anomalia_multivariada_visual.png"
    plt.tight_layout()
    plt.savefig(caminho_salvar5)
    print(f"Gráfico de dispersão agrupado salvo em: {caminho_salvar5}")
    plt.close()

    # --- Técnica 2: Análise Estatística Agrupada (Z-Score por Grupo) ---
    print("\n--- Técnica 2: Análise com Z-Score por Grupo ---")
    coluna_numerica = "Financial Loss (in Million $)"
    coluna_grupo = "Attack Type"
    threshold = 2.5

    df_full['media_grupo'] = df_full.groupby(coluna_grupo)[coluna_numerica].transform('mean')
    df_full['std_grupo'] = df_full.groupby(coluna_grupo)[coluna_numerica].transform('std')
    df_full['z_score_grupo'] = (df_full[coluna_numerica] - df_full['media_grupo']) / df_full['std_grupo'].fillna(1)

    anomalias_grupo = df_full[np.abs(df_full['z_score_grupo']) > threshold]

    if not anomalias_grupo.empty:
        print(f"\n>> Encontradas {len(anomalias_grupo)} anomalias com Z-Score de grupo > {threshold}:")
        print(anomalias_grupo[[coluna_grupo, coluna_numerica, 'z_score_grupo', 'Target Industry', 'Year']])
    else:
        print(f"\n>> Nenhuma anomalia de grupo encontrada com o threshold de {threshold}.")

    # --- Técnica 3: Usando Machine Learning (Isolation Forest) ---
    print("\n--- Técnica 3: Detecção de Anomalias com Machine Learning (Isolation Forest) ---")
    df_numeric = df_full.select_dtypes(include=np.number)
    
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(df_numeric)
    df_full['anomalia_ml'] = model.predict(df_numeric)
    
    anomalias_ml = df_full[df_full['anomalia_ml'] == -1]

    if not anomalias_ml.empty:
        print(f"\n>> O modelo de Machine Learning encontrou {len(anomalias_ml)} anomalias potenciais:")
        print(anomalias_ml)
    else:
        print("\n>> Nenhum ponto foi classificado como anomalia pelo modelo.")

except Exception as e:
    print(f"\nOcorreu um erro durante a análise de anomalias multivariadas: {e}")

# ==============================================================================
# GERAÇÃO DOS NOVOS GRÁFICOS DE ANÁLISE
# ==============================================================================
print("\n" + "="*70)
print("\n--- Gerando novos gráficos de análise ---")

# --- GRÁFICO 1: BARRAS - IMPACTO FINANCEIRO POR TIPO DE ATAQUE ---
try:
    print("Gerando Gráfico 1: Impacto Financeiro por Tipo de Ataque...")
    conn = sqlite3.connect(caminho_db)
    query = f'''
        SELECT "Attack Type", SUM("Financial Loss (in Million $)") as Total_Loss
        FROM {NOME_TABELA}
        GROUP BY "Attack Type"
        ORDER BY Total_Loss DESC
    '''
    df_loss = pd.read_sql_query(query, conn)
    conn.close()

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 8))
    sns.barplot(data=df_loss, x="Attack Type", y="Total_Loss", palette="viridis")
    
    plt.title('Impacto Financeiro Total por Tipo de Ataque', fontsize=16)
    plt.xlabel('Tipo de Ataque (Código)', fontsize=12)
    plt.ylabel('Prejuízo Total (em Milhões de $)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    
    caminho_salvar1 = caminho_pasta_csv / "grafico_1_impacto_financeiro.png"
    plt.tight_layout()
    plt.savefig(caminho_salvar1)
    print(f"Gráfico 1 salvo em: {caminho_salvar1}")
    plt.close() # Fecha a figura para liberar memória

except Exception as e:
    print(f"\nOcorreu um erro ao gerar o Gráfico 1: {e}")

# --- GRÁFICO 2: DISPERSÃO - USUÁRIOS AFETADOS VS PREJUÍZO FINANCEIRO ---
try:
    print("\nGerando Gráfico 2: Usuários Afetados vs. Prejuízo Financeiro...")
    conn = sqlite3.connect(caminho_db)
    query = f'''
        SELECT "Number of Affected Users", "Financial Loss (in Million $)"
        FROM {NOME_TABELA}
    '''
    df_scatter = pd.read_sql_query(query, conn)
    conn.close()

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 8))
    sns.regplot(
        data=df_scatter, 
        x="Number of Affected Users", 
        y="Financial Loss (in Million $)",
        scatter_kws={'alpha':0.5, 's':50},
        line_kws={'color':'red'}
    )
    
    plt.title('Relação entre Usuários Afetados e Prejuízo Financeiro', fontsize=16)
    plt.xlabel('Número de Usuários Afetados', fontsize=12)
    plt.ylabel('Prejuízo (em Milhões de $)', fontsize=12)
    
    caminho_salvar2 = caminho_pasta_csv / "grafico_2_usuarios_vs_prejuizo.png"
    plt.tight_layout()
    plt.savefig(caminho_salvar2)
    print(f"Gráfico 2 salvo em: {caminho_salvar2}")
    plt.close()

except Exception as e:
    print(f"\nOcorreu um erro ao gerar o Gráfico 2: {e}")

# --- GRÁFICO 3: HISTOGRAMA - TEMPO DE RESOLUÇÃO DE INCIDENTES ---
try:
    print("\nGerando Gráfico 3: Distribuição do Tempo de Resolução...")
    conn = sqlite3.connect(caminho_db)
    query = f'SELECT "Incident Resolution Time (in Hours)" FROM {NOME_TABELA}'
    df_hist = pd.read_sql_query(query, conn)
    conn.close()

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 8))
    sns.histplot(df_hist["Incident Resolution Time (in Hours)"], kde=True, bins=30)
    
    plt.title('Distribuição do Tempo de Resolução de Incidentes', fontsize=16)
    plt.xlabel('Tempo de Resolução (em Horas)', fontsize=12)
    plt.ylabel('Frequência (Nº de Incidentes)', fontsize=12)
    
    caminho_salvar3 = caminho_pasta_csv / "grafico_3_dist_tempo_resolucao.png"
    plt.tight_layout()
    plt.savefig(caminho_salvar3)
    print(f"Gráfico 3 salvo em: {caminho_salvar3}")
    plt.close()

except Exception as e:
    print(f"\nOcorreu um erro ao gerar o Gráfico 3: {e}")

horario_fim = datetime.now()
horario_fim_formatado = horario_fim.strftime("%H:%M:%S")

print(f"Início: {horario_inicio_formatado} | Fim: {horario_fim_formatado}")
