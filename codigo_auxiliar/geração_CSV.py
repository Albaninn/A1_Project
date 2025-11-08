import pandas as pd
import numpy as np
import random
import os  # Importar a biblioteca 'os'

# Altere este 'N' para quantas linhas você quiser!
N = 4000 

# =========================================================================
# 1. Definir os "universos" de possibilidades BASEADOS NO SEU ARQUIVO
# =========================================================================

countries = ['USA', 'Brazil', 'Germany', 'China', 'India', 'UK', 'Russia', 'Japan', 'Canada', 'France', 'Australia', 'South Korea', 'Mexico', 'Nigeria', 'South Africa', 'Israel', 'Iran', 'Spain', 'Italy'] 

# Anos (baseado no nome do seu arquivo, 2015-2024)
years = list(range(2015, 2025)) 

# Categorias que eu li do seu arquivo
attack_types = ['Ransomware', 'DDoS', 'Phishing', 'Malware', 'Man-in-the-Middle', 'SQL Injection']
industries = ['Retail', 'Telecommunications', 'Healthcare', 'Banking', 'Education', 'IT', 'Government']
sources = ['Hacker Group', 'Nation-state', 'Unknown', 'Insider']
vulnerabilities = ['Weak Passwords', 'Social Engineering', 'Zero-day', 'Unpatched Software']
defenses = ['Antivirus', 'VPN', 'Encryption', 'AI-based Detection', 'Firewall']

# =========================================================================
# 2. Criar o dicionário de dados (geração aleatória)
# =========================================================================
data = {
    'Country': np.random.choice(countries, N),
    'Year': np.random.choice(years, N),
    'Attack Type': np.random.choice(attack_types, N),
    'Target Industry': np.random.choice(industries, N),
    
    # Gerando valores numéricos aleatórios que parecem com os seus
    'Financial Loss (in Million $)': np.round(np.random.uniform(1.0, 100.0, size=N), 2),
    'Number of Affected Users': np.random.randint(10000, 1000000, size=N),
    
    'Attack Source': np.random.choice(sources, N),
    'Security Vulnerability Type': np.random.choice(vulnerabilities, N),
    'Defense Mechanism Used': np.random.choice(defenses, N),
    
    'Incident Resolution Time (in Hours)': np.random.randint(24, 121, size=N)
}

# 3. Criar o DataFrame
df = pd.DataFrame(data)

# =========================================================================
# 4. Adicionar "lógica" para os dados sintéticos ficarem melhores
# =========================================================================
# Se o Ataque é Phishing, a Vulnerabilidade é Engenharia Social
phishing_indices = df[df['Attack Type'] == 'Phishing'].index
df.loc[phishing_indices, 'Security Vulnerability Type'] = 'Social Engineering'
df.loc[phishing_indices, 'Defense Mechanism Used'] = np.random.choice(['Antivirus', 'VPN'], len(phishing_indices))

# Se o Ataque é SQL Injection, a Vulnerabilidade é Zero-day (no seu padrão)
sql_indices = df[df['Attack Type'] == 'SQL Injection'].index
df.loc[sql_indices, 'Security Vulnerability Type'] = 'Zero-day'
df.loc[sql_indices, 'Defense Mechanism Used'] = 'Firewall'

# Se o Ataque é Ransomware, a Vulnerabilidade são Senhas Fracas
ransom_indices = df[df['Attack Type'] == 'Ransomware'].index
df.loc[ransom_indices, 'Security Vulnerability Type'] = 'Weak Passwords'

# =========================================================================
# 5. Salvar em CSV (na pasta correta e com o delimitador correto)
# =========================================================================

# Pega o caminho absoluto do diretório onde o script está
script_dir = os.path.dirname(os.path.abspath(__file__)) 

# Define o nome do arquivo que queremos criar
file_name = "global_cyber_threats_gr.csv" # Você pode mudar esse nome se quiser

# Cria o caminho completo (Ex: ...\codigo_auxiliar\global_cyber_threats_4k.csv)
destination_path = os.path.join(script_dir, file_name)

# Salva o DataFrame no caminho de destino completo
# MUITO IMPORTANTE: Adicionado 'delimiter=';' para seguir o padrão do seu arquivo
df.to_csv(destination_path, index=False, sep=';') 

print(f"Arquivo '{file_name}' salvo com sucesso em: {destination_path}")
print(f"O arquivo foi salvo usando ';' como delimitador, igual ao seu original.")
print("\nAmostra dos dados gerados:")
print(df.head())