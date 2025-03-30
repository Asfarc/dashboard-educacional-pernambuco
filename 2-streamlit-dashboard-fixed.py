import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
import io
import json
import re
from constantes import *  # Importa constantes (rótulos, textos, etc.)

# Inicialização do tempo de execução
import time

if 'tempo_inicio' not in st.session_state:
    st.session_state['tempo_inicio'] = time.time()

# -------------------------------
# Configuração Inicial da Página
# -------------------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS unificado e otimizado
css_unificado = """
/* CSS Unificado e Otimizado para o Dashboard */

/* Estilo da Barra Lateral */
[data-testid="stSidebar"]::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: #364b60;
    z-index: -1;
    border-radius: 1px;
    margin: 1rem;
    padding: 1rem;
}

[data-testid="stSidebar"] > div {
    position: relative;
    z-index: 1;
}

/* Texto branco para elementos da barra lateral */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stRadio span:not([role="radio"]) {
    color: white !important;
}

/* Mantém o texto das opções em preto */
[data-testid="stSidebar"] option,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: black !important;
}

/* Estilo de itens selecionados na barra lateral */
[data-testid="stSidebar"] .stMultiSelect [aria-selected="true"] {
    background-color: #e37777 !important;
    color: white !important;
    border-radius: 1px !important;
}

/* Estilo do hover */
[data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:hover {
    background-color: #d66c6c !important;
    cursor: pointer;
}

/* Remove a cor azul padrão do Streamlit */
[data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:focus {
    box-shadow: none !important;
}

/* Estilo dos pills na barra lateral (botões) */
[data-testid="stSidebar"] div[data-testid="stPills"] {
    margin-top: 8px;
}

/* Botões não selecionados (kind="pills") */
button[kind="pills"][data-testid="stBaseButton-pills"] {
    background-color: transparent !important;
    color: white !important;
    border: 1px solid #e37777 !important;
    border-radius: 1px !important;
    transition: all 0.3s ease;
}

/* Hover em botões não selecionados */
button[kind="pills"][data-testid="stBaseButton-pills"]:hover {
    background-color: rgba(227, 119, 119, 0.2) !important;
}

/* Botões selecionados (kind="pillsActive") */
button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] {
    background-color: #e37777 !important; 
    color: white !important;          
    border: none !important;
    border-radius: 1px !important;
}

/* Texto nos botões ativos */
button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] p {
    color: white !important;
    font-weight: bold;
}

/* Estilo para a área principal do dashboard */
.main-header {
    background-color: #f9f9f9;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
    border-left: 5px solid #364b60;
}

/* Estilo para os botões e controles */
.stButton > button, .stDownloadButton > button {
    background-color: #364b60 !important;
    color: white !important;
    border: none !important;
    border-radius: 3px !important;
    transition: all 0.3s ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: #25344d !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

/* Títulos de seção */
h2 {
    color: #364b60;
    border-bottom: 1px solid #e37777;
    padding-bottom: 0.3rem;
    margin-top: 1.5rem;
}

/* Containers para KPIs e métricas */
.metric-container {
    background-color: white;
    border-radius: 5px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    text-align: center;
    transition: all 0.3s ease;
}

.metric-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #364b60;
}

.metric-label {
    font-size: 0.9rem;
    color: #666;
    margin-top: 0.5rem;
}

/* Responsividade para telas menores */
@media screen and (max-width: 768px) {
    .metric-value {
        font-size: 1.5rem;
    }

    .metric-label {
        font-size: 0.8rem;
    }

    [data-testid="stSidebar"] {
        width: 100% !important;
        margin: 0 !important;
    }
}

/* Estilo KPIs */
.kpi-container {
    background-color: #f9f9f9;
    border-radius: 5px;
    padding: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.kpi-title {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 5px;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: bold;
    color: #364b60;
}
.kpi-badge {
    background-color: #e6f2ff;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
    color: #364b60;
}
"""

st.markdown(f"<style>{css_unificado}</style>", unsafe_allow_html=True)


# -------------------------------
# Funções Auxiliares
# -------------------------------
def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR:
    Ex.: 1234567 -> '1.234.567'
         1234.56 -> '1.234,56'
    Se o número for NaN ou '-', retorna '-'.
    """
    if pd.isna(numero) or numero == "-":
        return "-"
    try:
        # Exibe sem casas decimais se for inteiro
        if float(numero).is_integer():
            return f"{int(numero):,}".replace(",", ".")
        else:
            # 2 casas decimais
            parte_inteira = int(float(numero))
            parte_decimal = abs(float(numero) - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except (ValueError, TypeError):
        return str(numero)


@st.cache_data(ttl=3600)  # Cache por 1 hora
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    - Lê os arquivos: escolas.parquet, estado.parquet e municipio.parquet.
    - Converte colunas que começam com 'Número de' para tipo numérico.
    Em caso de erro, exibe uma mensagem e interrompe a execução.
    """
    try:
        # Possíveis diretórios onde os arquivos podem estar
        diretorios_possiveis = [
            ".",
            "data",
            "dados",
            os.path.join(os.path.dirname(__file__), "data")
        ]

        escolas_df = estado_df = municipio_df = None
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
            raise FileNotFoundError(ERRO_ARQUIVOS_NAO_ENCONTRADOS)

        for df_ in [escolas_df, estado_df, municipio_df]:
            for col in df_.columns:
                if col.startswith("Número de"):
                    df_[col] = pd.to_numeric(df_[col], errors='coerce')

        return escolas_df, estado_df, municipio_df

    except Exception as e:
        st.error(ERRO_CARREGAR_DADOS.format(e))
        st.info(INFO_VERIFICAR_ARQUIVOS)
        st.stop()


@st.cache_data
def carregar_mapeamento_colunas():
    """
    Carrega o mapeamento de colunas a partir do arquivo JSON.
    """
    try:
        diretorios_possiveis = [
            ".",
            "data",
            "dados",
            os.path.join(os.path.dirname(__file__), "data")
        ]

        for diretorio in diretorios_possiveis:
            json_path = os.path.join(diretorio, "mapeamento_colunas.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)

        raise FileNotFoundError("Arquivo mapeamento_colunas.json não encontrado")

    except Exception as e:
        st.error(f"Erro ao carregar o mapeamento de colunas: {e}")
        st.stop()


def criar_mapeamento_colunas(df):
    """
    Ajusta o mapeamento de colunas original para considerar
    possíveis variações de nome nas colunas do DF real.
    """
    colunas_map = {col.lower().strip(): col for col in df.columns}

    def obter_coluna_real(nome_padrao):
        if nome_padrao in df.columns:
            return nome_padrao
        nome_normalizado = nome_padrao.lower().strip()
        if nome_normalizado in colunas_map:
            return colunas_map[nome_normalizado]
        return nome_padrao

    mapeamento_base = carregar_mapeamento_colunas()
    mapeamento_ajustado = {}

    for etapa, config in mapeamento_base.items():
        mapeamento_ajustado[etapa] = {
            "coluna_principal": obter_coluna_real(config.get("coluna_principal", "")),
            "subetapas": {},
            "series": {}
        }

        for subetapa, coluna in config.get("subetapas", {}).items():
            mapeamento_ajustado[etapa]["subetapas"][subetapa] = obter_coluna_real(coluna)

        for sub, series_dict in config.get("series", {}).items():
            if sub not in mapeamento_ajustado[etapa]["series"]:
                mapeamento_ajustado[etapa]["series"][sub] = {}
            for serie, col_serie in series_dict.items():
                mapeamento_ajustado[etapa]["series"][sub][serie] = obter_coluna_real(col_serie)

    return mapeamento_ajustado


def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    """
    Retorna o nome da coluna que contém os dados de matrículas
    de acordo com a etapa, subetapa e série.
    """
    if etapa not in mapeamento:
        st.error(ERRO_ETAPA_NAO_ENCONTRADA.format(etapa))
        return ""

    if subetapa == "Todas":
        return mapeamento[etapa].get("coluna_principal", "")

    if "subetapas" not in mapeamento[etapa] or subetapa not in mapeamento[etapa]["subetapas"]:
        st.warning(ERRO_SUBETAPA_NAO_ENCONTRADA.format(subetapa, etapa))
        return mapeamento[etapa].get("coluna_principal", "")

    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]

    series_subetapa = mapeamento[etapa].get("series", {}).get(subetapa, {})
    if not series_subetapa or serie not in series_subetapa:
        st.warning(ERRO_SERIE_NAO_ENCONTRADA.format(serie, subetapa))
        return mapeamento[etapa]["subetapas"][subetapa]

    return series_subetapa[serie]


def verificar_coluna_existe(df, coluna_nome):
    """
    Verifica se a coluna existe no DataFrame,
    levando em conta variações de maiúsculas/minúsculas.
    Retorna (True, nome_correto) caso exista; senão, (False, nome_original).
    """
    if not coluna_nome:
        return False, ""
    if coluna_nome in df.columns:
        return True, coluna_nome
    coluna_normalizada = coluna_nome.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}
    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]
    return False, coluna_nome


def converter_df_para_csv(df):
    """
    Converte o DataFrame para CSV em memória e retorna como bytes.
    """
    if df is None or df.empty:
        return "Não há dados para exportar.".encode('utf-8')
    try:
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Erro ao converter para CSV: {str(e)}")
        return "Erro na conversão".encode('utf-8')


def converter_df_para_excel(df):
    """
    Converte o DataFrame para Excel em memória e retorna como bytes.
    Adiciona formatações específicas na planilha.
    """
    if df is None or df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame({"Sem dados": []}).to_excel(writer, index=False, sheet_name='Sem_Dados')
        return output.getvalue()
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')

            # Adiciona formatação para o Excel
            workbook = writer.book
            worksheet = writer.sheets['Dados']

            # Formato para números
            formato_numero = workbook.add_format({'num_format': '#,##0'})
            formato_cabecalho = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#364b60',
                'font_color': 'white',
                'border': 1
            })

            # Aplica formato de cabeçalho
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, formato_cabecalho)

            # Aplica formato numérico para colunas que começam com "Número de"
            for i, col in enumerate(df.columns):
                if col.startswith("Número de"):
                    worksheet.set_column(i, i, 15, formato_numero)
                else:
                    worksheet.set_column(i, i, 15)

            # Ajusta a largura das colunas de acordo com o conteúdo
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)

        return output.getvalue()
    except Exception as e:
        st.error(f"Erro ao preparar Excel para download: {str(e)}")
        output = io.BytesIO()
        output.write("Erro na conversão".encode('utf-8'))
        return output.getvalue()


# -------------------------------
# Carregamento de Dados
# -------------------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()

    # Verificação adicional para garantir que os DataFrames não estão vazios
    if escolas_df.empty:
        st.error("O DataFrame de escolas está vazio.")
    if municipio_df.empty:
        st.error("O DataFrame de municípios está vazio.")
    if estado_df.empty:
        st.error("O DataFrame de estados está vazio.")

    # Verificar colunas críticas em cada DataFrame
    for df_nome, df in [("escolas", escolas_df), ("município", municipio_df), ("estado", estado_df)]:
        if "ANO" not in df.columns:
            st.error(f"Coluna 'ANO' não encontrada no DataFrame de {df_nome}.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.stop()

# ======================================
# CONFIGURAÇÃO DA BARRA LATERAL (FILTROS)
# ======================================
st.sidebar.title("Filtros")

tipo_visualizacao = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"]
)

if tipo_visualizacao == "Escola":
    df = escolas_df.copy()  # Usar .copy() para evitar SettingWithCopyWarning
elif tipo_visualizacao == "Município":
    df = municipio_df.copy()
else:  # Estado
    df = estado_df.copy()

# Verificar se o DataFrame selecionado não está vazio
if df.empty:
    st.error(f"Não há dados disponíveis para o nível de agregação '{tipo_visualizacao}'.")
    st.stop()

# Debug: mostrar as primeiras linhas e colunas do DataFrame
if st.sidebar.checkbox("Mostrar informações de debug", value=False):
    st.sidebar.write(f"Colunas no DataFrame de {tipo_visualizacao}:")
    st.sidebar.write(df.columns.tolist())
    st.sidebar.write(f"Primeiras linhas do DataFrame de {tipo_visualizacao}:")
    st.sidebar.write(df.head(2))

mapeamento_colunas = criar_mapeamento_colunas(df)

# Filtro do Ano
if "ANO" in df.columns:
    anos_disponiveis = sorted(df["ANO"].unique(), reverse=True)

    # Botões práticos para última opção e todas
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Último Ano", key="btn_ultimo_ano"):
        st.session_state["anos_multiselect"] = [anos_disponiveis[0]]
    if col2.button("Todos Anos", key="btn_todos_anos"):
        st.session_state["anos_multiselect"] = anos_disponiveis

    # Multiselect do ano usando session_state
    if "anos_multiselect" not in st.session_state:
        # Valor padrão
        st.session_state["anos_multiselect"] = [anos_disponiveis[0]]

    anos_selecionados = st.sidebar.multiselect(
        "Ano do Censo:",
        options=anos_disponiveis,
        default=st.session_state["anos_multiselect"],
        key="anos_multiselect"
    )
    if not anos_selecionados:
        st.warning("Por favor, selecione pelo menos um ano.")
        st.stop()

    df_filtrado = df[df["ANO"].isin(anos_selecionados)]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

# Filtro de Etapa, Subetapa e Série
etapas_disponiveis = list(mapeamento_colunas.keys())
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)

if etapa_selecionada not in mapeamento_colunas:
    st.error(f"A etapa '{etapa_selecionada}' não foi encontrada no mapeamento de colunas.")
    st.stop()

if "subetapas" in mapeamento_colunas[etapa_selecionada] and mapeamento_colunas[etapa_selecionada]["subetapas"]:
    subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

series_disponiveis = []
if (subetapa_selecionada != "Todas"
        and "series" in mapeamento_colunas[etapa_selecionada]
        and subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]):
    series_disponiveis = list(mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada].keys())
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )
else:
    serie_selecionada = "Todas"

# Filtro de Dependência Administrativa
if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())
    st.sidebar.caption(f"Total de {len(dependencias_disponiveis)} dependências disponíveis")

    # Usando session_state para armazenar seleção
    if "dep_selection" not in st.session_state:
        st.session_state["dep_selection"] = dependencias_disponiveis

    # Botões de seleção
    col_sel_all, col_clear = st.sidebar.columns(2)
    if col_sel_all.button("Selecionar Todas", key="btn_todas_dep"):
        st.session_state["dep_selection"] = dependencias_disponiveis
    if col_clear.button("Limpar Seleção", key="btn_limpar_dep"):
        st.session_state["dep_selection"] = []

    dependencia_selecionada = st.sidebar.multiselect(
        "DEPENDENCIA ADMINISTRATIVA:",
        options=dependencias_disponiveis,
        default=st.session_state["dep_selection"]
    )

    # Atualiza session_state após a multiselect
    st.session_state["dep_selection"] = dependencia_selecionada

    if dependencia_selecionada:
        st.sidebar.success(f"{len(dependencia_selecionada)} dependência(s) selecionada(s)")
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
    else:
        st.sidebar.warning("Nenhuma dependência selecionada. Selecione pelo menos uma.")
        df_filtrado = df_filtrado[0:0]  # DataFrame vazio
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

# Identifica a coluna de dados baseada em Etapa / Subetapa / Série
coluna_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento_colunas)
coluna_existe, coluna_real = verificar_coluna_existe(df_filtrado, coluna_dados)

# Verificar se a coluna de dados existe e tratar adequadamente
if coluna_existe:
    coluna_dados = coluna_real
    # Verificar se há dados válidos antes de filtrar
    try:
        df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_dados], errors='coerce') > 0]
    except Exception as e:
        st.warning(f"Erro ao filtrar dados por valor positivo: {e}")
        # Em caso de erro, não filtra
else:
    st.warning(f"A coluna '{coluna_dados}' não está disponível nos dados.")
    coluna_principal = mapeamento_colunas[etapa_selecionada].get("coluna_principal", "")
    coluna_existe, coluna_principal_real = verificar_coluna_existe(df_filtrado, coluna_principal)
    if coluna_existe:
        coluna_dados = coluna_principal_real
        st.info(f"Usando '{coluna_dados}' como alternativa")
        try:
            df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_dados], errors='coerce') > 0]
        except Exception as e:
            st.warning(f"Erro ao filtrar dados por valor positivo: {e}")
            # Em caso de erro, não filtra
    else:
        st.error("Não foi possível encontrar dados para a etapa selecionada.")
        st.stop()

# ------------------------------
# Configurações da Tabela
# ------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### Configurações da tabela")

ajustar_altura = st.sidebar.checkbox("Ajustar altura da tabela", value=False,
                                     help="Permite ajustar a altura da tabela de dados")
if ajustar_altura:
    altura_tabela = st.sidebar.slider("Altura da tabela (pixels)", 200, 1000, 600, 50)
else:
    altura_tabela = 600

# Colunas para exibir na tabela
st.sidebar.markdown("### Colunas adicionais")
colunas_tabela = []

# Campos básicos
if "ANO" in df_filtrado.columns:
    colunas_tabela.append("ANO")

# Definir colunas base de acordo com o tipo de visualização
if tipo_visualizacao == "Escola":
    colunas_base = [
        "CODIGO DA ESCOLA",
        "NOME DA ESCOLA",
        "CODIGO DO MUNICIPIO",
        "NOME DO MUNICIPIO",
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]
elif tipo_visualizacao == "Município":
    colunas_base = [
        "CODIGO DO MUNICIPIO",
        "NOME DO MUNICIPIO",
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]
else:  # Estado
    colunas_base = [
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]

# Adicionar apenas colunas que existem no DataFrame
for col in colunas_base:
    if col in df_filtrado.columns:
        colunas_tabela.append(col)
    else:
        st.sidebar.warning(f"Coluna '{col}' não encontrada no DataFrame de {tipo_visualizacao}")

# Inclui a coluna de dados principal (caso exista)
if coluna_dados in df_filtrado.columns:
    colunas_tabela.append(coluna_dados)

# Multiselect de colunas opcionais
todas_colunas_possiveis = [c for c in df_filtrado.columns if c not in colunas_tabela]
colunas_adicionais_selecionadas = st.sidebar.multiselect(
    "Selecionar colunas adicionais:",
    todas_colunas_possiveis,
    placeholder="Selecionar colunas adicionais..."
)
if colunas_adicionais_selecionadas:
    colunas_tabela.extend(colunas_adicionais_selecionadas)

# Garantir que todas as colunas selecionadas existam no DataFrame
colunas_existentes = [c for c in colunas_tabela if c in df_filtrado.columns]
if len(colunas_existentes) != len(colunas_tabela):
    st.sidebar.warning("Algumas colunas selecionadas não existem no DataFrame atual.")

# -------------------------------
# Botões de Download
# -------------------------------
st.sidebar.markdown("### Download dos dados")
col1, col2 = st.sidebar.columns(2)

# Preparar tabela para exibição e download
try:
    if coluna_dados in df_filtrado.columns:
        with pd.option_context('mode.chained_assignment', None):
            df_filtrado_tabela = df_filtrado[colunas_existentes].copy()
            # Converter coluna de dados para numérico se existir
            df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')
        # Ordenar por coluna de dados (descrescente)
        tabela_dados = df_filtrado_tabela.sort_values(by=coluna_dados, ascending=False)
        tabela_exibicao = tabela_dados.copy()
    else:
        tabela_dados = df_filtrado[colunas_existentes].copy()
        tabela_exibicao = tabela_dados.copy()

    # Verificar se a tabela está vazia
    if tabela_dados.empty:
        st.sidebar.warning("Não há dados para download com os filtros atuais.")
    else:
        # Preparar para download CSV
        try:
            csv_data = converter_df_para_csv(tabela_dados)
            with col1:
                st.download_button(
                    label="Baixar CSV",
                    data=csv_data,
                    file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.csv',
                    mime='text/csv',
                )
        except Exception as e:
            st.error(f"Erro ao preparar CSV para download: {str(e)}")

        # Preparar para download Excel
        try:
            excel_data = converter_df_para_excel(tabela_dados)
            with col2:
                st.download_button(
                    label="Baixar Excel",
                    data=excel_data,
                    file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
        except Exception as e:
            st.error(f"Erro ao preparar Excel para download: {str(e)}")
except Exception as e:
    st.error(f"Erro ao preparar dados para download: {str(e)}")

# -------------------------------
# Cabeçalho e Informações Iniciais
# -------------------------------
st.title(TITULO_DASHBOARD)
# -------------------------------
# Seção de Indicadores (KPIs)
# -------------------------------
st.markdown("## Indicadores")
kpi_container = st.container()
with kpi_container:
    col1, col2, col3 = st.columns(3)

    # KPI 1: Total de Matrículas
    try:
        if coluna_dados in df_filtrado.columns:
            total_matriculas = df_filtrado[coluna_dados].sum()
            with col1:
                st.markdown(
                    f'<div class="kpi-container">'
                    f'<p class="kpi-title">{ROTULO_TOTAL_MATRICULAS}</p>'
                    f'<p class="kpi-value">{formatar_numero(total_matriculas)}</p>'
                    f'<span class="kpi-badge">Total</span>'
                    f'</div>', unsafe_allow_html=True
                )
        else:
            with col1:
                st.markdown(
                    '<div class="kpi-container">'
                    '<p class="kpi-title">Total de Matrículas</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Coluna não disponível</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
    except Exception as e:
        with col1:
            st.markdown(
                '<div class="kpi-container">'
                '<p class="kpi-title">Total de Matrículas</p>'
                '<p class="kpi-value">-</p>'
                '<span class="kpi-badge">Erro</span>'
                '</div>',
                unsafe_allow_html=True
            )
            st.caption(f"Erro ao calcular: {str(e)}")

    # KPI 2: Média
    with col2:
        try:
            if coluna_dados in df_filtrado.columns:
                if tipo_visualizacao == "Escola":
                    if len(df_filtrado) > 0:
                        media_por_escola = df_filtrado[coluna_dados].mean()
                        st.markdown(
                            f'<div class="kpi-container">'
                            f'<p class="kpi-title">{ROTULO_MEDIA_POR_ESCOLA}</p>'
                            f'<p class="kpi-value">{formatar_numero(media_por_escola)}</p>'
                            f'<span class="kpi-badge">Média</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            '<div class="kpi-container">'
                            '<p class="kpi-title">Média de Matrículas por Escola</p>'
                            '<p class="kpi-value">-</p>'
                            '<span class="kpi-badge">Sem dados</span>'
                            '</div>',
                            unsafe_allow_html=True
                        )
                else:
                    if "DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns:
                        # Verificar se há dados suficientes para o agrupamento
                        if not df_filtrado.empty and coluna_dados in df_filtrado.columns:
                            media_por_dependencia = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[
                                coluna_dados].mean()
                            if not media_por_dependencia.empty:
                                media_geral = media_por_dependencia.mean()
                                st.markdown(
                                    f'<div class="kpi-container">'
                                    f'<p class="kpi-title">{ROTULO_MEDIA_MATRICULAS}</p>'
                                    f'<p class="kpi-value">{formatar_numero(media_geral)}</p>'
                                    f'<span class="kpi-badge">Média</span>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    '<div class="kpi-container">'
                                    '<p class="kpi-title">Média de Matrículas</p>'
                                    '<p class="kpi-value">-</p>'
                                    '<span class="kpi-badge">Sem dados</span>'
                                    '</div>',
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown(
                                '<div class="kpi-container">'
                                '<p class="kpi-title">Média de Matrículas</p>'
                                '<p class="kpi-value">-</p>'
                                '<span class="kpi-badge">Dados insuficientes</span>'
                                '</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        if not df_filtrado.empty and coluna_dados in df_filtrado.columns:
                            media_geral = df_filtrado[coluna_dados].mean()
                            st.markdown(
                                f'<div class="kpi-container">'
                                f'<p class="kpi-title">Média de Matrículas</p>'
                                f'<p class="kpi-value">{formatar_numero(media_geral)}</p>'
                                f'<span class="kpi-badge">Média</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                '<div class="kpi-container">'
                                '<p class="kpi-title">Média de Matrículas</p>'
                                '<p class="kpi-value">-</p>'
                                '<span class="kpi-badge">Dados insuficientes</span>'
                                '</div>',
                                unsafe_allow_html=True
                            )
            else:
                st.markdown(
                    '<div class="kpi-container">'
                    '<p class="kpi-title">Média de Matrículas</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Coluna não disponível</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
        except Exception as e:
            st.markdown(
                '<div class="kpi-container">'
                '<p class="kpi-title">Média de Matrículas</p>'
                '<p class="kpi-value">-</p>'
                '<span class="kpi-badge">Erro</span>'
                '</div>',
                unsafe_allow_html=True
            )
            st.caption(f"Erro ao calcular: {str(e)}")

    # KPI 3: Depende do tipo de visualização
    with col3:
        try:
            if tipo_visualizacao == "Escola":
                total_escolas = len(df_filtrado)
                st.markdown(
                    f'<div class="kpi-container">'
                    f'<p class="kpi-title">{ROTULO_TOTAL_ESCOLAS}</p>'
                    f'<p class="kpi-value">{formatar_numero(total_escolas)}</p>'
                    f'<span class="kpi-badge">Contagem</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            elif tipo_visualizacao == "Município":
                total_municipios = len(df_filtrado)
                st.markdown(
                    f'<div class="kpi-container">'
                    f'<p class="kpi-title">{ROTULO_TOTAL_MUNICIPIOS}</p>'
                    f'<p class="kpi-value">{formatar_numero(total_municipios)}</p>'
                    f'<span class="kpi-badge">Contagem</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:  # Estado
                if coluna_dados in df_filtrado.columns:
                    max_valor = df_filtrado[coluna_dados].max()
                    st.markdown(
                        f'<div class="kpi-container">'
                        f'<p class="kpi-title">{ROTULO_MAXIMO_MATRICULAS}</p>'
                        f'<p class="kpi-value">{formatar_numero(max_valor)}</p>'
                        f'<span class="kpi-badge">Máximo</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div class="kpi-container">'
                        '<p class="kpi-title">Máximo de Matrículas</p>'
                        '<p class="kpi-value">-</p>'
                        '<span class="kpi-badge">Coluna não disponível</span>'
                        '</div>',
                        unsafe_allow_html=True
                    )
        except Exception as e:
            if tipo_visualizacao == "Escola":
                st.markdown(
                    '<div class="kpi-container">'
                    '<p class="kpi-title">Total de Escolas</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Erro</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
            elif tipo_visualizacao == "Município":
                st.markdown(
                    '<div class="kpi-container">'
                    '<p class="kpi-title">Total de Municípios</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Erro</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="kpi-container">'
                    '<p class="kpi-title">Máximo de Matrículas</p>'
                    '<p class="kpi-value">-</p>'
                    '<span class="kpi-badge">Erro</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
            st.caption(f"Erro ao calcular: {str(e)}")

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown(f"## {TITULO_DADOS_DETALHADOS}")

# Verificar se há dados para exibir
if 'tabela_exibicao' not in locals() or tabela_exibicao.empty:
    st.warning("Não há dados para exibir com os filtros selecionados.")
else:
    try:
        # Adicionar opções de filtragem acima da tabela
        filtro_col1, filtro_col2 = st.columns([1, 3])

        with filtro_col1:
            registros_por_pagina = st.selectbox(
                "Registros por página:",
                options=[10, 25, 50, 100, "Todos"],
                index=1  # Padrão: 25
            )

        with filtro_col2:
            opcoes_ordenacao = ["Maior valor", "Menor valor"]

            # Opções adicionais de ordenação baseadas nas colunas disponíveis
            if "NOME DA ESCOLA" in tabela_exibicao.columns:
                opcoes_ordenacao.extend(["Alfabético (A-Z) por Escola", "Alfabético (Z-A) por Escola"])
            elif "NOME DO MUNICIPIO" in tabela_exibicao.columns:
                opcoes_ordenacao.extend(["Alfabético (A-Z) por Município", "Alfabético (Z-A) por Município"])
            elif "NOME DA UF" in tabela_exibicao.columns:
                opcoes_ordenacao.extend(["Alfabético (A-Z) por UF", "Alfabético (Z-A) por UF"])

            if len(opcoes_ordenacao) > 2 and coluna_dados in tabela_exibicao.columns:
                ordem_tabela = st.radio(
                    "Ordenar por:",
                    opcoes_ordenacao,
                    horizontal=True
                )

                if ordem_tabela == "Maior valor":
                    tabela_exibicao = tabela_exibicao.sort_values(by=coluna_dados, ascending=False)
                elif ordem_tabela == "Menor valor":
                    tabela_exibicao = tabela_exibicao.sort_values(by=coluna_dados, ascending=True)
                elif "por Escola" in ordem_tabela:
                    tabela_exibicao = tabela_exibicao.sort_values(
                        by="NOME DA ESCOLA",
                        ascending=("A-Z" in ordem_tabela)
                    )
                elif "por Município" in ordem_tabela:
                    tabela_exibicao = tabela_exibicao.sort_values(
                        by="NOME DO MUNICIPIO",
                        ascending=("A-Z" in ordem_tabela)
                    )
                elif "por UF" in ordem_tabela:
                    tabela_exibicao = tabela_exibicao.sort_values(
                        by="NOME DA UF",
                        ascending=("A-Z" in ordem_tabela)
                    )

        # Total de registros
        st.caption(f"Total de registros: {len(tabela_exibicao):,}".replace(",", "."))

        # Implementar paginação
        if registros_por_pagina != "Todos":
            registros_por_pagina = int(registros_por_pagina)
            num_paginas = max(1, (len(tabela_exibicao) - 1) // registros_por_pagina + 1)

            # Garantir que não haja erro se não houver registros
            if num_paginas > 0:
                pagina_atual = st.number_input(
                    "Página",
                    min_value=1,
                    max_value=num_paginas,
                    value=1,
                    step=1
                )

                inicio = (pagina_atual - 1) * registros_por_pagina
                fim = min(inicio + registros_por_pagina, len(tabela_exibicao))

                # Garantir que os índices sejam válidos
                if inicio < len(tabela_exibicao):
                    df_paginado = tabela_exibicao.iloc[inicio:fim]
                    st.dataframe(df_paginado, height=altura_tabela, use_container_width=True)

                    # Informação da paginação
                    st.caption(f"Exibindo registros {inicio + 1} a {fim} de {len(tabela_exibicao):,}".replace(",", "."))
                else:
                    st.warning("Índice de paginação inválido.")
                    st.dataframe(tabela_exibicao.head(registros_por_pagina), height=altura_tabela,
                                 use_container_width=True)
            else:
                st.warning("Não há páginas para exibir.")
        else:
            st.dataframe(tabela_exibicao, height=altura_tabela, use_container_width=True)

        # Adiciona linha de totais
        if coluna_dados in tabela_exibicao.columns:
            total_col = tabela_exibicao[coluna_dados].sum()
            st.markdown(f"**Total de {coluna_dados}:** {formatar_numero(total_col)}")

    except Exception as e:
        st.error(f"Erro ao exibir a tabela: {str(e)}")
        st.write("Detalhes do erro para depuração:")
        st.exception(e)

        # Tentativa alternativa de visualização
        st.write("Tentando exibir tabela simplificada...")
        try:
            # Mostrar apenas as primeiras 100 linhas como fallback
            st.dataframe(tabela_exibicao.head(100), height=altura_tabela)
        except:
            st.error("Não foi possível exibir a tabela mesmo em formato simplificado.")

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
if 'RODAPE_NOTA' in globals():
    st.markdown(RODAPE_NOTA)
else:
    st.markdown("© Dashboard Educacional - Desenvolvido para visualização de dados do Censo Escolar")

# Tempo de execução
tempo_final = time.time()
tempo_total = round(tempo_final - st.session_state.get('tempo_inicio', tempo_final), 2)
st.session_state['tempo_inicio'] = tempo_final
st.caption(f"Tempo de processamento: {tempo_total} segundos")
