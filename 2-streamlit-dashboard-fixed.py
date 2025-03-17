import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from pathlib import Path
import io

# -------------------------------
# Configuração Inicial da Página
# -------------------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Funções Auxiliares
# -------------------------------

def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar.
    Se o número for NaN ou '-', retorna '-'.
    """
    if pd.isna(numero) or numero == "-":
        return "-"
    return f"{int(numero):,}".replace(",", ".")

@st.cache_data
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    - Lê os arquivos: escolas.parquet, estado.parquet e municipio.parquet.
    - Converte colunas que começam com 'Número de' para tipo numérico.
    Em caso de erro, exibe uma mensagem e interrompe a execução.
    """
    try:
        # Definir possíveis localizações dos arquivos
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]
        
        # Tentar encontrar os arquivos em diferentes localizações
        escolas_df = None
        estado_df = None
        municipio_df = None
        
        for diretorio in diretorios_possiveis:
            escolas_path = os.path.join(diretorio, "escolas.parquet")
            estado_path = os.path.join(diretorio, "estado.parquet")
            municipio_path = os.path.join(diretorio, "municipio.parquet")
            
            if os.path.exists(escolas_path) and os.path.exists(estado_path) and os.path.exists(municipio_path):
                escolas_df = pd.read_parquet(escolas_path)
                estado_df = pd.read_parquet(estado_path)
                municipio_df = pd.read_parquet(municipio_path)
                break
        
        if escolas_df is None or estado_df is None or municipio_df is None:
            raise FileNotFoundError("Não foi possível encontrar os arquivos Parquet necessários.")
        
        # Converter colunas numéricas para o tipo correto
        for df in [escolas_df, estado_df, municipio_df]:
            for col in df.columns:
                if col.startswith("Número de"):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return escolas_df, estado_df, municipio_df
    
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        st.info("Verifique se os arquivos Parquet estão disponíveis no repositório.")
        st.stop()

def criar_mapeamento_colunas(df):
    """
    Cria um dicionário que mapeia as etapas de ensino para os nomes das colunas.
    Esse mapeamento inclui a coluna principal, subetapas e séries, facilitando a seleção
    dos dados conforme os filtros do usuário.
    
    Parâmetros:
    df (DataFrame): DataFrame a ser usado como referência para verificar colunas existentes
    """
    # Criar mapeamento de colunas (case-insensitive) apenas uma vez
    colunas_map = {col.lower().strip(): col for col in df.columns}
    
    # Função auxiliar para verificar e obter o nome correto da coluna
    def obter_coluna_real(nome_padrao):
        # Verifica se a coluna existe exatamente como foi especificada
        if nome_padrao in df.columns:
            return nome_padrao
            
        # Verifica se existe uma versão case-insensitive da coluna
        nome_normalizado = nome_padrao.lower().strip()
        if nome_normalizado in colunas_map:
            return colunas_map[nome_normalizado]
            
        # Se não encontrar, retorna o nome original
        return nome_padrao
    
    mapeamento = {
        "Educação Infantil": {
            "coluna_principal": obter_coluna_real("Número de Matrículas da Educação Infantil"),
            "subetapas": {
                "Creche": obter_coluna_real("Número de Matrículas da Educação Infantil - Creche"),
                "Pré-Escola": obter_coluna_real("Número de Matrículas da Educação Infantil - Pré-Escola")
            },
            "series": {}
        },
        "Ensino Fundamental": {
            "coluna_principal": obter_coluna_real("Número de Matrículas do Ensino Fundamental"),
            "subetapas": {
                "Anos Iniciais": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais"),
                "Anos Finais": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais")
            },
            "series": {
                "Anos Iniciais": {
                    "1º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 1º Ano"),
                    "2º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 2º Ano"),
                    "3º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 3º Ano"),
                    "4º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 4º Ano"),
                    "5º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 5º Ano")
                },
                "Anos Finais": {
                    "6º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 6º Ano"),
                    "7º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 7º Ano"),
                    "8º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 8º Ano"),
                    "9º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 9º Ano")
                }
            }
        },
        "Ensino Médio": {
            "coluna_principal": obter_coluna_real("Número de Matrículas do Ensino Médio"),
            "subetapas": {
                "Propedêutico": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico"),
                "Curso Técnico Integrado": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional"),
                "Normal/Magistério": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério")
            },
            "series": {
                "Propedêutico": {
                    "1ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 4º ano/4ª Série"),
                    "Não Seriado": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - Não Seriado")
                },
                "Curso Técnico Integrado": {
                    "1ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 4º ano/4ª Série"),
                    "Não Seriado": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - Não Seriado")
                },
                "Normal/Magistério": {
                    "1ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 4º ano/4ª Série")
                }
            }
        },
        "EJA": {
            "coluna_principal": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA)"),
            "subetapas": {
                "Ensino Fundamental": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental"),
                "Ensino Médio": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Médio")
            },
            "series": {
                "Ensino Fundamental": {
                    "Anos Iniciais": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Iniciais"),
                    "Anos Finais": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Finais")
                }
            }
        },
        "Educação Profissional": {
            "coluna_principal": obter_coluna_real("Número de Matrículas da Educação Profissional"),
            "subetapas": {
                "Técnica": obter_coluna_real("Número de Matrículas da Educação Profissional Técnica"),
                "Curso FIC": obter_coluna_real("Número de Matrículas da Educação Profissional - Curso FIC Concomitante")
            },
            "series": {
                "Técnica": {
                    "Concomitante": obter_coluna_real("Número de Matrículas da Educação Profissional Técnica - Curso Técnico Concomitante"),
                    "Subsequente": obter_coluna_real("Número de Matrículas da Educação Profissional Técnica - Curso Técnico Subsequente")
                }
            }
        }
    }
    
    return mapeamento

def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    """
    Determina a coluna de dados com base na etapa, subetapa e série selecionadas.
    
    Parâmetros:
    etapa (str): Etapa de ensino selecionada
    subetapa (str): Subetapa selecionada ("Todas" ou nome específico)
    serie (str): Série selecionada ("Todas" ou nome específico)
    mapeamento (dict): Mapeamento de colunas
    
    Retorna:
    str: Nome da coluna de dados
    """
    # Verificar se a etapa existe no mapeamento
    if etapa not in mapeamento:
        st.error(f"A etapa '{etapa}' não foi encontrada no mapeamento de colunas.")
        return ""
    
    # Caso 1: Nenhuma subetapa selecionada, usa coluna principal da etapa
    if subetapa == "Todas":
        return mapeamento[etapa].get("coluna_principal", "")
    
    # Verificar se a subetapa existe
    if "subetapas" not in mapeamento[etapa] or subetapa not in mapeamento[etapa]["subetapas"]:
        st.warning(f"A subetapa '{subetapa}' não foi encontrada para a etapa '{etapa}'.")
        return mapeamento[etapa].get("coluna_principal", "")
    
    # Caso 2: Nenhuma série específica selecionada, usa coluna da subetapa
    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]
    
    # Verificar se a subetapa tem séries e se a série selecionada existe
    series_subetapa = mapeamento[etapa].get("series", {}).get(subetapa, {})
    if not series_subetapa or serie not in series_subetapa:
        st.warning(f"A série '{serie}' não foi encontrada para a subetapa '{subetapa}'.")
        return mapeamento[etapa]["subetapas"][subetapa]
    
    # Caso 3: Série específica selecionada
    return series_subetapa[serie]

def verificar_coluna_existe(df, coluna_nome):
    """
    Verifica se uma coluna existe no DataFrame, tentando encontrar uma correspondência
    exata ou insensível a maiúsculas/minúsculas.
    
    Parâmetros:
    df (DataFrame): DataFrame a ser verificado
    coluna_nome (str): Nome da coluna a procurar
    
    Retorna:
    tuple: (coluna_existe, coluna_real)
        coluna_existe (bool): Indica se a coluna foi encontrada.
        coluna_real (str): Nome real da coluna encontrada ou nome original
    """
    # Verifica se a coluna existe exatamente como especificada
    if coluna_nome in df.columns:
        return True, coluna_nome
    
    # Verifica se existe uma versão case-insensitive
    coluna_normalizada = coluna_nome.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}
    
    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]
    
    # Não encontrou a coluna
    return False, coluna_nome

def adicionar_linha_totais(df, coluna_dados):
    """
    Adiciona uma linha de totais ao DataFrame.
    
    Parâmetros:
    df (DataFrame): DataFrame a ser processado
    coluna_dados (str): Nome da coluna de dados numéricos
    
    Retorna:
    DataFrame: DataFrame com a linha de totais adicionada
    """
    # Criar uma linha de totais
    totais = {}
    
    # Inicializar todas as colunas como vazias
    for col in df.columns:
        totais[col] = ""
    
    # Primeira coluna como "TOTAL"
    if len(df.columns) > 0:
        totais[df.columns[0]] = "TOTAL"
    
    # Calcular total para a coluna de dados
    if coluna_dados in df.columns:
        valor_total = pd.to_numeric(df[coluna_dados], errors='coerce').sum()
        totais[coluna_dados] = formatar_numero(valor_total)
    
    # Definir percentual como 100%
    if '% do Total' in df.columns:
        totais['% do Total'] = "100.00%"
    
    # Criar DataFrame com a linha de totais
    linha_totais = pd.DataFrame([totais], index=['TOTAL'])
    
    # Concatenar com o DataFrame original
    return pd.concat([df, linha_totais])

def aplicar_estilo_tabela(df, modo_desempenho=False):
    """
    Aplica estilos à tabela conforme o modo de desempenho.
    
    Parâmetros:
    df (DataFrame): DataFrame a estilizar
    modo_desempenho (bool): Indica se deve usar estilo simplificado para melhor desempenho
    
    Retorna:
    Styler: DataFrame estilizado
    """
    if modo_desempenho or len(df) > 1000:
        # Estilo mínimo para melhor desempenho
        return df.style.set_properties(**{'text-align': 'center'})
    else:
        # Estilo completo para tabelas menores
        return df.style \
            .set_properties(**{'text-align': 'center'}) \
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center')]},
                {'selector': 'td', 'props': [('text-align', 'center')]},
                # Destacar a linha de totais
                {'selector': 'tr:last-child', 'props': [
                    ('font-weight', 'bold'),
                    ('background-color', '#e6f2ff'),
                    ('border-top', '2px solid #b3d9ff'),
                    ('color', '#0066cc')
                ]}
            ])

def converter_df_para_csv(df):
    """Converte DataFrame para formato CSV"""
    return df.to_csv(index=False).encode('utf-8')

def converter_df_para_excel(df):
    """Converte DataFrame para formato Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

# -------------------------------
# Carregamento de Dados
# -------------------------------
escolas_df, estado_df, municipio_df = carregar_dados()

# ======================================
# CONFIGURAÇÃO DA BARRA LATERAL (FILTROS)
# ======================================

st.sidebar.title("Filtros")

# Seleção do nível de agregação
tipo_visualizacao = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"]
)

# Seleção do DataFrame conforme o nível escolhido
if tipo_visualizacao == "Escola":
    df = escolas_df
elif tipo_visualizacao == "Município":
    df = municipio_df
else:
    df = estado_df

# Agora crie o mapeamento de colunas usando o DataFrame selecionado
mapeamento_colunas = criar_mapeamento_colunas(df)

# Filtro do Ano
if "ANO" in df.columns:
    anos_disponiveis = sorted(df["ANO"].unique())
    ano_selecionado = st.sidebar.selectbox("Ano do Censo:", anos_disponiveis)
    df_filtrado = df[df["ANO"] == ano_selecionado]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

# Filtro da DEPENDENCIA ADMINISTRATIVA
if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].unique())
    dependencia_selecionada = st.sidebar.multiselect(
        "DEPENDENCIA ADMINISTRATIVA:",
        dependencias_disponiveis,
        default=dependencias_disponiveis
    )
    if dependencia_selecionada:
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

# Filtro da Etapa de Ensino
etapas_disponiveis = list(mapeamento_colunas.keys())
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)

# Verificação se a etapa está no mapeamento
if etapa_selecionada not in mapeamento_colunas:
    st.error(f"A etapa '{etapa_selecionada}' não foi encontrada no mapeamento de colunas.")
    st.stop()

# Filtro da Subetapa (varia de acordo com a etapa selecionada)
if "subetapas" in mapeamento_colunas[etapa_selecionada] and mapeamento_colunas[etapa_selecionada]["subetapas"]:
    subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

# Filtro para a Série, se aplicável à subetapa selecionada
series_disponiveis = []
if (subetapa_selecionada != "Todas" and 
    "series" in mapeamento_colunas[etapa_selecionada] and 
    subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]):
    series_disponiveis = list(mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada].keys())
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )
else:
    serie_selecionada = "Todas"

# -------------------------------
# Determinação da Coluna de Dados (utilizando a nova função)
# -------------------------------
coluna_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento_colunas)

# Verifica se a coluna existe no DataFrame
coluna_existe, coluna_real = verificar_coluna_existe(df_filtrado, coluna_dados)
if coluna_existe:
    coluna_dados = coluna_real
else:
    st.warning(f"A coluna '{coluna_dados}' não está disponível nos dados.")
    # Tenta usar a coluna principal como fallback
    coluna_principal = mapeamento_colunas[etapa_selecionada].get("coluna_principal.", "")
    coluna_existe, coluna_principal_real = verificar_coluna_existe(df_filtrado, coluna_principal)
    
    if coluna_existe:
        coluna_dados = coluna_principal_real
        st.info(f"Usando '{coluna_dados}' como alternativa")
    else:
        st.error("Não foi possível encontrar dados para a etapa selecionada.")
        st.stop()

# -------------------------------
# Cabeçalho e Informações Iniciais do Dashboard
# -------------------------------
st.title("Dashboard de Matrículas - Inepy")
st.markdown(f"**Visualização por {tipo_visualizacao} - Ano: {ano_selecionado}**")

# Exibição dos filtros selecionados
filtro_texto = f"**Etapa:** {etapa_selecionada}"
if subetapa_selecionada != "Todas":
    filtro_texto += f" | **Subetapa:** {subetapa_selecionada}"
    if serie_selecionada != "Todas" and serie_selecionada in series_disponiveis:
        filtro_texto += f" | **Série:** {serie_selecionada}"
st.markdown(filtro_texto)

# -------------------------------
# Seção de Indicadores (KPIs)
# -------------------------------
col1, col2, col3 = st.columns(3)

# KPI 1: Total de Matrículas na etapa/subetapa/série selecionada
total_matriculas = df_filtrado[coluna_dados].sum()
with col1:
    st.metric("Total de Matrículas", formatar_numero(total_matriculas))

# KPI 2: Média de Matrículas
with col2:
    if tipo_visualizacao == "Escola":
        if len(df_filtrado) > 0:
            media_por_escola = df_filtrado[coluna_dados].mean()
            st.metric("Média de Matrículas por Escola", formatar_numero(media_por_escola))
        else:
            st.metric("Média de Matrículas por Escola", "-")
    else:
        media_por_dependencia = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[coluna_dados].mean()
        if not media_por_dependencia.empty:
            media_geral = media_por_dependencia.mean()
            st.metric("Média de Matrículas", formatar_numero(media_geral))
        else:
            st.metric("Média de Matrículas", "-")

# KPI 3: Indicador adicional conforme a visualização
with col3:
    if tipo_visualizacao == "Escola":
        total_escolas = len(df_filtrado)
        st.metric("Total de Escolas", formatar_numero(total_escolas))
    elif tipo_visualizacao == "Município":
        total_municipios = len(df_filtrado)
        st.metric("Total de Municípios", formatar_numero(total_municipios))
    else:
        st.metric("Máximo de Matrículas", formatar_numero(df_filtrado[coluna_dados].max()))

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown("## Dados Detalhados")

# Adicionar CSS personalizado para aumentar a espessura da barra de rolagem
st.markdown("""
<style>
    /* Aumenta a espessura da barra de rolagem principal */
    ::-webkit-scrollbar {
        width: 14px;
        height: 14px;
    }
    
    /* Estilo do "track" (trilho) da barra de rolagem */
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 7px;
    }
    
    /* Estilo do "thumb" (parte móvel) da barra de rolagem */
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 7px;
    }
    
    /* Ao passar o mouse */
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    /* Elimina a rolagem interna da tabela para prevenir barras de rolagem duplas */
    .stDataFrame > div:first-child {
        overflow: hidden !important;
    }
    
    /* Garante que apenas o contêiner externo tenha rolagem */
    .main .block-container {
        overflow-y: auto;
    }
    
    /* Remove barras de rolagem de elementos internos específicos */
    div[data-testid="stVerticalBlock"] {
        overflow: visible !important;
    }
    
    /* Ajuste para o canto da barra de rolagem */
    ::-webkit-scrollbar-corner {
        background: #f1f1f1;
    }
</style>
""", unsafe_allow_html=True)

# Seleção das colunas a serem exibidas na tabela, conforme o nível de visualização
# Adicionando ANO como primeira coluna sempre
colunas_tabela = ["ANO"]

if tipo_visualizacao == "Escola":
    colunas_tabela.extend(["CODIGO DA ESCOLA", "NOME DA ESCOLA", "CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"])
elif tipo_visualizacao == "Município":
    colunas_tabela.extend(["CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"])
else:  # Estado
    colunas_tabela.extend(["CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"])

# Adiciona a coluna de dados selecionada ao final
colunas_tabela.append(coluna_dados)

# Verifica se todas as colunas estão presentes no DataFrame filtrado
colunas_existentes = [col for col in colunas_tabela if col in df_filtrado.columns]
colunas_tabela = colunas_existentes

# Converter a coluna de dados para numérico para ordenação correta
df_filtrado_tabela = df_filtrado.copy()
if coluna_dados in df_filtrado_tabela.columns:
    # Converter para numérico para cálculos e ordenação
    df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')
    
    # Adicionar coluna de percentual
    total = df_filtrado_tabela[coluna_dados].sum()
    if total > 0:
        df_filtrado_tabela['% do Total'] = df_filtrado_tabela[coluna_dados].apply(
            lambda x: (x/total)*100 if pd.notnull(x) else None
        )
        colunas_tabela.append('% do Total')
    
    # Ordenar a tabela pelos valores do coluna_dados em ordem decrescente
    tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
    
    # Criar versão formatada para exibição
    tabela_exibicao = tabela_dados.copy()
    tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
        lambda x: formatar_numero(x) if pd.notnull(x) else "-"
    )
    
    # Formatar a coluna de percentual se existir
    if '% do Total' in tabela_exibicao.columns:
        tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
            lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
        )
else:
    tabela_dados = df_filtrado_tabela[colunas_existentes]
    tabela_exibicao = tabela_dados.copy()

# Criar abas para diferentes visualizações
tab1, tab2 = st.tabs(["Visão Tabular", "Resumo Estatístico"])

with tab1:
    # Adicionar controle para ajustar a altura da tabela e resolver problemas de barras de rolagem
    st.write("### Configurações de exibição")
    col1, col2, col3, col4 = st.columns(4)
    
    with col4:
        # Permitir que o usuário ajuste a altura da tabela
        altura_personalizada = st.checkbox("Ajustar altura da tabela", value=False,
                                         help="Use esta opção se estiver vendo barras de rolagem duplicadas")
        if altura_personalizada:
            altura_manual = st.slider("Altura da tabela (pixels)", 
                                    min_value=200, 
                                    max_value=1000, 
                                    value=600, 
                                    step=50)
    
    with col1:
        # Mostrar todos os registros não é recomendado para grandes conjuntos de dados
        total_registros = len(tabela_exibicao)
        if total_registros > 1000:
            st.warning(f"⚠️ Há {formatar_numero(total_registros)} registros no total. Mostrar todos pode causar lentidão.")
            mostrar_todos = st.checkbox("Mostrar todos os registros", value=False)
        else:
            mostrar_todos = st.checkbox("Mostrar todos os registros", value=False)

    with col2:
        if not mostrar_todos:
            max_registros = min(500, total_registros)
            
            # Caso 1: Se há poucos registros, não usamos slider
            if max_registros < 10:
                registros_por_pagina = max_registros
                st.info(f"Total de {formatar_numero(max_registros)} registros disponíveis.")
            # Caso 2: Usamos slider com configurações ajustadas ao número de registros
            else:
                # Definir step adequado ao número de registros
                step = 1 if max_registros < 20 else 10
                
                registros_por_pagina = st.slider(
                    "Registros por página:", 
                    min_value=1,  # Valor mínimo sempre será 1
                    max_value=max_registros,
                    value=min(200, max_registros),
                    step=step
                )
        else:
            # Se selecionar mostrar todos, ainda limitamos a um máximo seguro para evitar travamentos
            if total_registros > 1000:
                registros_por_pagina = 1000
                st.warning(f"Para evitar travamentos, limitamos a exibição a 1000 registros de um total de {formatar_numero(total_registros)}.")
            else:
                registros_por_pagina = total_registros
    
    with col3:
        # Opção para ativar modo de desempenho
        modo_desempenho = st.checkbox("Ativar modo de desempenho", value=True, 
                                      help="Otimiza o carregamento para grandes conjuntos de dados.")
        if modo_desempenho and total_registros > 500:
            st.info("Modo de desempenho ativado. Algumas formatações visuais serão simplificadas.")

    
    # Adicionar filtros de busca mais próximos da tabela e com largura reduzida
    st.write("### Filtros da tabela")
    
    # Ajustando proporções para evitar quebra de texto nos rótulos
    col1, col2, col3, col4, col5, col6 = st.columns([0.6, 3.0, 0.6, 3.0, 0.6, 3.0])
    
    # Filtros para texto (nomes de localidades)
    filtro_texto = None
    colunas_localidade = [col for col in ["NOME DA UF", "NOME DO MUNICIPIO", "NOME DA ESCOLA"] if col in tabela_exibicao.columns]
    if colunas_localidade:
        with col1:
            st.write("**Localidade:**")
        with col2:
            coluna_texto_selecionada = st.selectbox("", ["Nenhum"] + colunas_localidade, label_visibility="collapsed")
            if coluna_texto_selecionada != "Nenhum":
                filtro_texto = st.text_input("", placeholder=f"Filtrar {coluna_texto_selecionada}...", label_visibility="collapsed", key="filtro_texto")
    
    # Filtros para códigos (numéricos)
    filtro_codigo = None
    colunas_codigo = [col for col in ["CODIGO DA UF", "CODIGO DO MUNICIPIO", "CODIGO DA ESCOLA"] if col in tabela_exibicao.columns]
    if colunas_codigo:
        with col3:
            st.write("**Código:**")
        with col4:
            coluna_codigo_selecionada = st.selectbox(" ", ["Nenhum"] + colunas_codigo, label_visibility="collapsed")
            if coluna_codigo_selecionada != "Nenhum":
                filtro_codigo = st.text_input(" ", placeholder=f"Filtrar {coluna_codigo_selecionada}...", label_visibility="collapsed", key="filtro_codigo")
    
    # Colunas adicionais
    with col5:
        st.write("**Colunas:**")
    with col6:
        # Permitir que o usuário selecione colunas adicionais para exibir
        todas_colunas = [col for col in df_filtrado.columns if col not in colunas_tabela]
        if todas_colunas:
            colunas_adicionais = st.multiselect(
                "",
                todas_colunas,
                label_visibility="collapsed",
                placeholder="Selecionar colunas adicionais..."
            )
            if colunas_adicionais:
                colunas_tabela = colunas_tabela + colunas_adicionais
                # Atualizar tabelas com as novas colunas
                tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
                tabela_exibicao = tabela_dados.copy()
                tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
                    lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                )
                if '% do Total' in tabela_exibicao.columns:
                    tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
                        lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                    )
        else:
            st.write("Não há colunas adicionais disponíveis")

    # Aplicar filtros com feedback de desempenho
    tabela_filtrada = tabela_exibicao.copy()
    filtros_aplicados = False
    
    # Adicionar botão de aplicar filtros para conjuntos grandes de dados
    if len(tabela_exibicao) > 1000:
        col_filtrar = st.columns([1])[0]
        with col_filtrar:
            aplicar_filtros = st.button("Aplicar Filtros", type="primary")
        mostrar_dica = True
    else:
        aplicar_filtros = True  # Para conjuntos pequenos, sempre aplicar filtros em tempo real
        mostrar_dica = False
    
    # Filtros para texto
    if filtro_texto and coluna_texto_selecionada != "Nenhum":
        if len(filtro_texto) >= 3 and aplicar_filtros:
            # Usar método mais eficiente para grandes conjuntos de dados
            if len(tabela_filtrada) > 5000:
                # Para dados muito grandes, usamos um método mais rápido 
                # mas potencialmente menos preciso (sem case=False)
                tabela_filtrada = tabela_filtrada[
                    tabela_filtrada[coluna_texto_selecionada].astype(str).str.contains(filtro_texto, na=False)
                ]
            else:
                tabela_filtrada = tabela_filtrada[
                    tabela_filtrada[coluna_texto_selecionada].astype(str).str.contains(filtro_texto, case=False, na=False)
                ]
            filtros_aplicados = True
        elif mostrar_dica and len(filtro_texto) > 0 and len(filtro_texto) < 3:
            st.info("Digite pelo menos 3 caracteres para filtrar por texto.")
    
    # Filtros para códigos
    if filtro_codigo and coluna_codigo_selecionada != "Nenhum":
        if len(filtro_codigo) >= 1 and aplicar_filtros:
            tabela_filtrada = tabela_filtrada[
                tabela_filtrada[coluna_codigo_selecionada].astype(str).str.contains(filtro_codigo, na=False)
            ]
            filtros_aplicados = True
            
    # Mostrar informações sobre o número de registros filtrados
    if filtros_aplicados and len(tabela_filtrada) < len(tabela_exibicao):
        st.success(f"Filtro aplicado: {len(tabela_filtrada)} de {len(tabela_exibicao)} registros correspondem aos critérios.")

    # Cálculo de paginação
    total_registros = len(tabela_filtrada)
    total_paginas = max(1, (total_registros - 1) // registros_por_pagina + 1)

    # Paginação otimizada
    if not mostrar_todos and total_paginas > 1:
        # Para grandes conjuntos de dados, usamos uma interface de paginação mais eficiente
        if total_registros > 1000:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.write("**Página:**")
            with col2:
                pagina_atual = st.number_input(
                    "",
                    min_value=1,
                    max_value=total_paginas,
                    value=1,
                    key="pagina_atual",
                    label_visibility="collapsed"
                )
            with col3:
                # Criar 4 colunas para os botões de navegação
                col_first, col_prev, col_next, col_last = st.columns(4)

                with col_first:
                    if st.button("⏮ Primeira", disabled=(pagina_atual <= 1), key="btn_first"):
                        pagina_atual = 1

                with col_prev:
                    if st.button("◀ Anterior", disabled=(pagina_atual <= 1), key="btn_prev"):
                        pagina_atual -= 1

                with col_next:
                    if st.button("Próxima ▶", disabled=(pagina_atual >= total_paginas), key="btn_next"):
                        pagina_atual += 1

                with col_last:
                    if st.button("Última ⏭", disabled=(pagina_atual >= total_paginas), key="btn_last"):
                        pagina_atual = total_paginas
        else:
            # Interface simples para conjuntos menores de dados
            col1, col2, col3 = st.columns([1, 5, 2])
            with col1:
                st.write("**Página:**")
            with col2:
                pagina_atual = st.number_input(
                    "",
                    min_value=1,
                    max_value=total_paginas,
                    value=1,
                    key="pagina_atual",
                    label_visibility="collapsed"
                )
            with col3:
                # Criar 4 colunas para os botões de navegação
                col_first, col_prev, col_next, col_last = st.columns(4)

                with col_first:
                    if st.button("⏮", disabled=(pagina_atual <= 1), key="btn_first_simple"):
                        pagina_atual = 1

                with col_prev:
                    if st.button("◀", disabled=(pagina_atual <= 1), key="btn_prev_simple"):
                        pagina_atual -= 1

                with col_next:
                    if st.button("▶", disabled=(pagina_atual >= total_paginas), key="btn_next_simple"):
                        pagina_atual += 1

                with col_last:
                    if st.button("⏭", disabled=(pagina_atual >= total_paginas), key="btn_last_simple"):
                        pagina_atual = total_paginas

        # Calcular quais registros mostrar - MANTENDO O NÚMERO CONSISTENTE DE REGISTROS POR PÁGINA
        inicio = (pagina_atual - 1) * registros_por_pagina
        fim = min(inicio + registros_por_pagina, len(tabela_filtrada))
        tabela_para_exibir = tabela_filtrada.iloc[inicio:fim]
    else:
        # Limitação de registros para evitar travamentos
        if len(tabela_filtrada) > registros_por_pagina:
            tabela_para_exibir = tabela_filtrada.iloc[:registros_por_pagina]
            st.warning(
                f"Para melhor desempenho, exibindo os primeiros {formatar_numero(registros_por_pagina)} de {formatar_numero(len(tabela_filtrada))} registros.")
        else:
            tabela_para_exibir = tabela_filtrada

    # Adicionar linha de totais usando a função refatorada
    tabela_com_totais = adicionar_linha_totais(tabela_para_exibir, coluna_dados)

    # Exibir informação atualizada sobre total de registros no estilo info azul
    if total_registros > 1000 and not mostrar_todos:
        st.info(
            f"Exibindo {formatar_numero(len(tabela_para_exibir))} de {formatar_numero(total_registros)} resultados.")

    # Adicionar dica de navegação na tabela
    st.markdown("""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <p style="margin: 0;">
                <b>Dica de navegação:</b> Use as teclas <kbd>Home</kbd> para ir ao topo da tabela e <kbd>End</kbd> para ir ao final.
                <br>Use as teclas <kbd>↑</kbd> <kbd>↓</kbd> ou a roda do mouse para navegar entre as linhas.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Determinar altura da tabela
    if altura_personalizada:
        altura_tabela = altura_manual
    elif len(tabela_com_totais) > 20:
        altura_tabela = 600  # Altura fixa para tabelas maiores
    else:
        altura_tabela = len(tabela_com_totais) * 35 + 38  # 35px por linha + 38px para o cabeçalho

    # Aplicar estilo e exibir tabela
    usar_estilo_simples = modo_desempenho and len(tabela_com_totais) > 500

    if usar_estilo_simples:
        with st.container():
            st.dataframe(tabela_com_totais, use_container_width=True, height=altura_tabela, hide_index=True)
        st.caption("*Última linha representa os totais. Modo de desempenho ativo para maior velocidade.*")

    else:
        tabela_estilizada = aplicar_estilo_tabela(tabela_com_totais, modo_desempenho)
        with st.container():
            st.dataframe(tabela_estilizada, use_container_width=True, height=altura_tabela, hide_index=True)

    # Informação de paginação abaixo da tabela
    if not mostrar_todos and total_paginas > 1:
        st.write(
            f"Página {pagina_atual} de {total_paginas} • Registros por página: {formatar_numero(registros_por_pagina)}")
    st.markdown("""
    <style>
    .nav-buttons {
        position: absolute;
        right: 20px;
        margin-top: -50px;
        display: flex;
        gap: 10px;
        z-index: 999;
    }
    .nav-btn {
        background-color: rgba(255, 255, 255, 0.8);
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 6px 12px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .nav-btn:hover {
        background-color: #f0f0f0;
    }
    </style>
    <div class="nav-buttons">
        <button onclick="scrollTableToTop()" class="nav-btn" title="Ir ao topo da tabela">↑ Topo</button>
        <button onclick="scrollTableToBottom()" class="nav-btn" title="Ir ao final da tabela">↓ Final</button>
    </div>

    <script>
    function scrollTableToTop() {
        // Função melhorada para encontrar o contêiner correto da tabela
        setTimeout(function() {
            // Busca todos os possíveis contêineres de tabela
            const tables = document.querySelectorAll('.stDataFrame');
            if (tables.length > 0) {
                // Primeiro, tenta encontrar o contêiner direto que tenha scroll
                let scrollables = tables[0].querySelectorAll('div[style*="overflow"]');
                let scrollable = null;

                // Percorre os contêineres para encontrar o que tem scrollHeight > clientHeight
                for (let i = 0; i < scrollables.length; i++) {
                    if (scrollables[i].scrollHeight > scrollables[i].clientHeight) {
                        scrollable = scrollables[i];
                        break;
                    }
                }

                // Se não encontrou, tenta o primeiro div dentro da tabela
                if (!scrollable) {
                    scrollable = tables[0].querySelector('div');
                }

                // Se encontrou qualquer contêiner com scroll, rola para o topo
                if (scrollable) {
                    scrollable.scrollTop = 0;
                    console.log("Rolando para o topo", scrollable);
                }
            }
        }, 200);
    }

    function scrollTableToBottom() {
        // Função melhorada para encontrar o contêiner correto da tabela
        setTimeout(function() {
            // Busca todos os possíveis contêineres de tabela
            const tables = document.querySelectorAll('.stDataFrame');
            if (tables.length > 0) {
                // Primeiro, tenta encontrar o contêiner direto que tenha scroll
                let scrollables = tables[0].querySelectorAll('div[style*="overflow"]');
                let scrollable = null;

                // Percorre os contêineres para encontrar o que tem scrollHeight > clientHeight
                for (let i = 0; i < scrollables.length; i++) {
                    if (scrollables[i].scrollHeight > scrollables[i].clientHeight) {
                        scrollable = scrollables[i];
                        break;
                    }
                }

                // Se não encontrou, tenta o primeiro div dentro da tabela
                if (!scrollable) {
                    scrollable = tables[0].querySelector('div');
                }

                // Se encontrou qualquer contêiner com scroll, rola para o final
                if (scrollable) {
                    scrollable.scrollTop = scrollable.scrollHeight;
                    console.log("Rolando para o final", scrollable);
                }
            }
        }, 200);
    }

    // Executar imediatamente para garantir que o script está pronto
    document.addEventListener('DOMContentLoaded', function() {
        console.log("DOM carregado, script de navegação da tabela ativo");
    });
    </script>
    """, unsafe_allow_html=True)

    # Adicionar também CSS para garantir que os botões permaneçam visíveis
    # mesmo quando a tabela é muito grande
    st.markdown("""
    <style>
    /* Aumentar z-index para garantir que os botões permaneçam sobre outros elementos */
    .nav-buttons {
        z-index: 9999;
    }

    /* Garantir que a tabela não sobreponha os botões */
    .stDataFrame {
        position: relative;
        z-index: 1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Botões para download
    col1, col2 = st.columns(2)
    
    with col1:
        # Download como CSV
        st.download_button(
            label="Download CSV",
            data=converter_df_para_csv(tabela_dados.loc[tabela_para_exibir.index]),  # Apenas registros exibidos
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.csv',
            mime='text/csv',
        )
    
    with col2:
        # Download como Excel
        st.download_button(
            label="Download Excel",
            data=converter_df_para_excel(tabela_dados.loc[tabela_para_exibir.index]),  # Apenas registros exibidos
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

with tab2:
    # Apresentar um resumo estatístico dos dados
    if coluna_dados in tabela_dados.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Tabela de estatísticas
            resumo = pd.DataFrame({
                'Métrica': ['Total', 'Média', 'Mediana', 'Mínimo', 'Máximo', 'Desvio Padrão'],
                'Valor': [
                    formatar_numero(tabela_dados[coluna_dados].sum()),
                    formatar_numero(tabela_dados[coluna_dados].mean()),
                    formatar_numero(tabela_dados[coluna_dados].median()),
                    formatar_numero(tabela_dados[coluna_dados].min()),
                    formatar_numero(tabela_dados[coluna_dados].max()),
                    formatar_numero(tabela_dados[coluna_dados].std())
                ]
            })
            st.write("### Resumo Estatístico")
            
            # Estilizar a tabela de resumo
            resumo_estilizado = resumo.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
            
            st.dataframe(resumo_estilizado, use_container_width=True, hide_index=True)
        
        with col2:
            # Top 5 valores
            st.write("### Top 5 Valores")
            top5 = tabela_dados.nlargest(5, coluna_dados)
            
            # Selecionar colunas para exibição
            colunas_exibir = []
            if tipo_visualizacao == "Escola" and "NOME DA ESCOLA" in top5.columns:
                colunas_exibir.append("NOME DA ESCOLA")
            elif tipo_visualizacao == "Município" and "NOME DO MUNICIPIO" in top5.columns:
                colunas_exibir.append("NOME DO MUNICIPIO")
            elif "NOME DA UF" in top5.columns:
                colunas_exibir.append("NOME DA UF")
            
            if "DEPENDENCIA ADMINISTRATIVA" in top5.columns:
                colunas_exibir.append("DEPENDENCIA ADMINISTRATIVA")
                
            colunas_exibir.append(coluna_dados)
            if '% do Total' in top5.columns:
                colunas_exibir.append('% do Total')
            
            # Formatar valores para exibição
            top5_exibir = top5[colunas_exibir].copy()
            if coluna_dados in top5_exibir.columns:
                top5_exibir[coluna_dados] = top5_exibir[coluna_dados].apply(
                    lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                )
            
            if '% do Total' in top5_exibir.columns:
                top5_exibir['% do Total'] = top5_exibir['% do Total'].apply(
                    lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                )
                
            # Estilizar a tabela top5
            top5_estilizado = top5_exibir.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
            
            st.dataframe(top5_estilizado, use_container_width=True, hide_index=True)

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown("**Nota:** Os dados são provenientes do Censo Escolar. Os traços (-) indicam ausência de dados.")
