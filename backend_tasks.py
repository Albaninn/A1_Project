import sqlite3
import pandas as pd
from pathlib import Path
import glob
import zipfile
import tempfile  # Usaremos para lidar com os uploads
import shutil    # Para limpar pastas temporárias
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

# ==============================================================================
# FUNÇÃO 1: PROCESSAR A NOVA BASE DE DADOS (Lógica do 01_preparar_dados.py)
# ==============================================================================
def processar_nova_base(uploaded_file, db_path, table_name):
    """
    Processa um arquivo (ZIP ou CSV) enviado pelo usuário e o transforma
    em um banco de dados SQLite otimizado.
    """
    print("Iniciando o processamento da nova base...")
    
    # Cria um diretório temporário para trabalhar com os arquivos
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        lista_arquivos_csv = []
        
        # Salva o arquivo enviado no diretório temporário
        temp_file_path = temp_dir_path / uploaded_file.name
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        print(f"Arquivo '{uploaded_file.name}' salvo em diretório temporário.")

        # --- Etapa 0: Descompactar (se for .zip) ---
        if uploaded_file.name.endswith('.zip'):
            print("Arquivo .zip detectado. Descompactando...")
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir_path)
            # Lista todos os CSVs extraídos
            lista_arquivos_csv = glob.glob(str(temp_dir_path / "*.csv"))
        
        # --- Etapa 0: Lidar com .csv único ---
        elif uploaded_file.name.endswith('.csv'):
            print("Arquivo .csv único detectado.")
            lista_arquivos_csv = [str(temp_file_path)]
        
        else:
            raise ValueError("Tipo de arquivo não suportado. Envie .zip ou .csv")
            
        if not lista_arquivos_csv:
            raise ValueError("Nenhum arquivo .csv encontrado no .zip ou no upload.")
            
        print(f"Arquivos CSV a processar: {len(lista_arquivos_csv)}")

        # --- Etapa 1: Pré-Análise (Achar todas as colunas) ---
        print("Analisando cabeçalhos de todos os arquivos...")
        colunas_master = set()
        for arquivo in lista_arquivos_csv:
            df_header = pd.read_csv(arquivo, nrows=0, low_memory=False, encoding='latin1')
            df_header.columns = df_header.columns.str.strip().str.replace('\n', '')
            colunas_master.update(df_header.columns)
        
        master_columns_list = sorted(list(colunas_master))
        print(f"Total de colunas únicas encontradas: {len(master_columns_list)}")

        # --- Etapa 2: Criação da Tabela Mestra e Inserção dos Dados ---
        # Deletamos o banco antigo, se existir, para criar o novo
        if db_path.exists():
            db_path.unlink()
            
        conn = sqlite3.connect(db_path)
        
        df_vazio = pd.DataFrame(columns=master_columns_list)
        df_vazio.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Tabela '{table_name}' criada com sucesso.")

        for arquivo in lista_arquivos_csv:
            print(f"Processando arquivo em pedaços: {Path(arquivo).name}...")
            chunk_reader = pd.read_csv(arquivo, chunksize=100000, low_memory=False, encoding='latin1')
            
            for i, chunk in enumerate(chunk_reader):
                chunk.columns = chunk.columns.str.strip().str.replace('\n', '')
                chunk_reindexado = chunk.reindex(columns=master_columns_list)
                chunk_reindexado.to_sql(table_name, conn, if_exists='append', index=False)
            
        print("Todos os dados foram inseridos na tabela.")
        conn.close()

        # --- Etapa 3: Correção dos Tipos de Dados ---
        print("Iniciando otimização de tipos de dados...")
        conn = sqlite3.connect(db_path)
        
        print("Analisando amostra para definir os tipos...")
        df_amostra = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 200000", conn)
        dtype_map = {}
        for col in df_amostra.columns:
            try:
                coluna_convertida = pd.to_numeric(df_amostra[col], errors='coerce')
                if df_amostra[col].dtype == 'object' and coluna_convertida.dtype != 'object':
                    if (coluna_convertida.dropna() % 1 == 0).all():
                        dtype_map[col] = 'INTEGER'
                    else:
                        dtype_map[col] = 'REAL'
                else:
                    dtype_map[col] = 'TEXT'
            except (ValueError, TypeError):
                 dtype_map[col] = 'TEXT'
        
        table_name_new = f"{table_name}_new"
        
        print("Criando nova tabela otimizada...")
        conn.execute(f"DROP TABLE IF EXISTS {table_name_new}")
        create_table_sql = f"CREATE TABLE {table_name_new} ({', '.join([f'\"{col}\" {tipo}' for col, tipo in dtype_map.items()])})"
        conn.execute(create_table_sql)

        print("Copiando dados para a nova tabela...")
        chunk_reader_sql = pd.read_sql_query(f"SELECT * FROM {table_name}", conn, chunksize=100000)
        
        for i, chunk in enumerate(chunk_reader_sql):
            chunk_convertido = chunk.astype({col: str for col in chunk.columns if dtype_map[col] == 'TEXT'})
            chunk_convertido.to_sql(table_name_new, conn, if_exists='append', index=False)
        
        print("Substituindo tabelas...")
        conn.execute(f"DROP TABLE {table_name}")
        conn.execute(f"ALTER TABLE {table_name_new} RENAME TO {table_name}")
        
        conn.commit()
        conn.close()
        
    print("Processamento da nova base concluído com sucesso!")
    return True, "Processamento da base concluído."

# ==============================================================================
# FUNÇÃO 2: TREINAR O NOVO MODELO (Lógica do 02_treinar_modelo.py)
# ==============================================================================
def treinar_novo_modelo(db_path, table_name, model_save_path):
    """
    Carrega os dados do banco SQLite, treina os modelos de regressão e 
    classificação, e salva o melhor modelo de classificação.
    """
    print("Iniciando treinamento do novo modelo...")
    try:
        conn = sqlite3.connect(db_path)
        df_original = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        print(f"Dados carregados do DB: {df_original.shape[0]} linhas.")
    except Exception as e:
        return False, f"Erro ao carregar dados do DB: {e}"

    # --- PARTE 1: REGRESSÃO (Ainda fazemos para mostrar a análise) ---
    print("\nIniciando Parte 1: Regressão (Prever 'Financial Loss')")
    COLUNA_ALVO_REG = "Financial Loss (in Million $)"
    colunas_categoricas_reg = [
        'Attack Source', 'Attack Type', 'Country', 'Defense Mechanism Used', 
        'Security Vulnerability Type', 'Target Industry', 'Year'
    ]
    # Filtra colunas que realmente existem no df
    colunas_categoricas_reg_validas = [col for col in colunas_categoricas_reg if col in df_original.columns]
    
    df_reg = pd.get_dummies(df_original, columns=colunas_categoricas_reg_validas, drop_first=True, dtype=int)

    y_reg = df_reg[COLUNA_ALVO_REG]
    X_reg = df_reg.drop(columns=[COLUNA_ALVO_REG])
    X_reg_train, X_reg_test, y_reg_train, y_reg_test = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

    modelo_lr = LinearRegression()
    modelo_lr.fit(X_reg_train, y_reg_train)
    r2_lr = r2_score(y_reg_test, modelo_lr.predict(X_reg_test))
    print(f"  - Regressão Linear R²: {r2_lr:.2f}")

    # --- PARTE 2: CLASSIFICAÇÃO (O modelo que vamos salvar) ---
    print("\nIniciando Parte 2: Classificação (Prever 'Attack Type')")
    COLUNA_ALVO_CLASS = "Attack Type"
    colunas_categoricas_class = [
        'Attack Source', 'Country', 'Defense Mechanism Used', 
        'Security Vulnerability Type', 'Target Industry', 'Year'
    ]
    colunas_categoricas_class_validas = [col for col in colunas_categoricas_class if col in df_original.columns]
    
    df_class = pd.get_dummies(df_original, columns=colunas_categoricas_class_validas, drop_first=True, dtype=int)
    
    # Garantir que a coluna alvo exista
    if COLUNA_ALVO_CLASS not in df_class.columns:
        return False, f"Coluna alvo '{COLUNA_ALVO_CLASS}' não encontrada na nova base."

    y_class = df_class[COLUNA_ALVO_CLASS]
    X_class = df_class.drop(columns=[COLUNA_ALVO_CLASS])
    
    # Verifica se há dados suficientes para 'stratify'
    if y_class.nunique() > 1 and all(y_class.value_counts() > 1):
        X_class_train, X_class_test, y_class_train, y_class_test = train_test_split(X_class, y_class, test_size=0.2, random_state=42, stratify=y_class)
    else:
        X_class_train, X_class_test, y_class_train, y_class_test = train_test_split(X_class, y_class, test_size=0.2, random_state=42)

    modelo_rf_class = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    modelo_rf_class.fit(X_class_train, y_class_train)
    acc_rf_class = accuracy_score(y_class_test, modelo_rf_class.predict(X_class_test))
    print(f"  - Random Forest Classifier Acurácia: {acc_rf_class * 100:.2f}%")

    # --- ETAPA FINAL: SALVAR O MODELO ---
    print(f"\nSalvando modelo em: {model_save_path}")
    try:
        joblib.dump(modelo_rf_class, model_save_path)
        print("Modelo salvo com sucesso.")
    except Exception as e:
        return False, f"Erro ao salvar o modelo: {e}"
        
    return True, "Treinamento concluído com sucesso."