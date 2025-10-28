import sqlite3
import pandas as pd
from pathlib import Path
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

horario_fim = datetime.now()
horario_fim_formatado = horario_fim.strftime("%H:%M:%S")

print(f"Início: {horario_inicio_formatado} | Fim: {horario_fim_formatado}")
