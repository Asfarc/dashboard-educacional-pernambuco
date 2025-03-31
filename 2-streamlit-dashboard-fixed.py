import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
import io
import json
import re
from constantes import *  # Importa constantes (rótulos, textos, etc.)
import time
import altair as alt
import base64


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

/* Estilos para filtros de tabela */
.table-container {
    background-color: white;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.table-header {
    font-weight: 600;
    margin-bottom: 15px;
    color: #364b60;
    font-size: 18px;
}
.filter-input {
    margin-top: 10px;
    margin-bottom: 10px;
}
.info-text {
    color: #4c8bf5;
    font-size: 14px;
    margin-top: 10px;
    padding: 8px;
    background-color: #f0f7ff;
    border-radius: 5px;
    border-left: 3px solid #4c8bf5;
}
.warning-text {
    color: #dc3545;
    font-size: 14px;
    margin-top: 10px;
    padding: 8px;
    background-color: #fff5f5;
    border-radius: 5px;
    border-left: 3px solid #dc3545;
}
.icon-filter {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    margin-right: 4px;
    cursor: pointer;
    font-size: 14px;
}
.icon-filters-container {
    display: flex;
    gap: 2px;
    align-items: center;
}
"""

st.markdown(f"<style>{css_unificado}</style>", unsafe_allow_html=True)

# -------------------------------
# Funções Auxiliares
# -------------------------------
def aplicar_padrao_numerico_brasileiro(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR:
    Ex.: 1234567 -> '1.234.567'
         1234.56 -> '1.234,56'
    Se o número for NaN ou '-', retorna '-'.
    Aplica formatação apenas a valores numéricos.
    """
    if pd.isna(numero) or numero == "-":
        return "-"

    try:
        float_numero = float(numero)
        if float_numero.is_integer():
            return f"{int(float_numero):,}".replace(",", ".")
        else:
            parte_inteira = int(float_numero)
            parte_decimal = abs(float_numero - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except (ValueError, TypeError):
        return str(numero)

@st.cache_data(ttl=3600)
def importar_arquivos_parquet():
    try:
        escolas_path = "escolas.parquet"
        estado_path = "estado.parquet"
        municipio_path = "municipio.parquet"

        if not all(os.path.exists(path) for path in [escolas_path, estado_path, municipio_path]):
            raise FileNotFoundError(ERRO_ARQUIVOS_NAO_ENCONTRADOS)

        escolas_df = pd.read_parquet(escolas_path)
        estado_df = pd.read_parquet(estado_path)
        municipio_df = pd.read_parquet(municipio_path)

        # Converte colunas
        for df_ in [escolas_df, estado_df, municipio_df]:
            for col in df_.columns:
                if col.startswith("Número de"):
                    df_[col] = pd.to_numeric(df_[col], errors='coerce')
                elif col in ["ANO", "CODIGO DO MUNICIPIO", "CODIGO DA ESCOLA", "CODIGO DA UF"]:
                    df_[col] = df_[col].astype(str)

        return escolas_df, estado_df, municipio_df

    except Exception as e:
        st.error(ERRO_CARREGAR_DADOS.format(e))
        st.info(INFO_VERIFICAR_ARQUIVOS)
        st.stop()

@st.cache_data
def ler_dicionario_de_etapas():
    try:
        json_path = "dicionario_das_etapas_de_ensino.json"
        if not os.path.exists(json_path):
            raise FileNotFoundError("Arquivo dicionario_das_etapas_de_ensino.json não encontrado")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar o mapeamento de colunas: {e}")
        st.stop()

@st.cache_data
def padronizar_dicionario_de_etapas(df):
    colunas_map = {}
    for col in df.columns:
        nome_normalizado = col.replace('\n', '').lower().strip()
        colunas_map[nome_normalizado] = col

    def obter_coluna_real(nome_padrao):
        if nome_padrao in df.columns:
            return nome_padrao
        nome_normalizado = nome_padrao.replace('\n', '').lower().strip()
        if nome_normalizado in colunas_map:
            return colunas_map[nome_normalizado]
        return nome_padrao

    mapeamento_base = ler_dicionario_de_etapas()
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

def procurar_coluna_matriculas_por_etapa(etapa, subetapa, serie, mapeamento):
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

def confirmar_existencia_colunas_apos_normalizacao(df, coluna_nome):
    if not coluna_nome:
        return False, ""
    if coluna_nome in df.columns:
        return True, coluna_nome

    coluna_normalizada = coluna_nome.replace('\n', '').lower().strip()
    colunas_normalizadas = {col.replace('\n', '').lower().strip(): col for col in df.columns}
    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]
    return False, coluna_nome

def gerar_arquivo_csv(df):
    if df is None or df.empty:
        return "Não há dados para exportar.".encode('utf-8')
    try:
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Erro ao converter para CSV: {str(e)}")
        return "Erro na conversão".encode('utf-8')

def gerar_planilha_excel(df):
    if df is None or df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame({"Sem dados": []}).to_excel(writer, index=False, sheet_name='Sem_Dados')
        return output.getvalue()
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')

            workbook = writer.book
            worksheet = writer.sheets['Dados']
            formato_numero = workbook.add_format({'num_format': '#,##0'})
            formato_cabecalho = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#364b60',
                'font_color': 'white',
                'border': 1
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, formato_cabecalho)
            for i, col in enumerate(df.columns):
                if col.startswith("Número de"):
                    worksheet.set_column(i, i, 15, formato_numero)
                else:
                    worksheet.set_column(i, i, 15)
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)

        return output.getvalue()
    except Exception as e:
        st.error(f"Erro ao preparar Excel para download: {str(e)}")
        output = io.BytesIO()
        output.write("Erro na conversão".encode('utf-8'))
        return output.getvalue()

# -----------------------------------------------------------------------------
# Função para Paginação (chunk) - inspirada no snippet que você viu na internet
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def split_frame(input_df: pd.DataFrame, rows_per_page: int):
    """
    Recebe um DataFrame e o número de linhas por página (rows_per_page).
    Retorna uma lista de DataFrames, cada qual com 'rows_per_page' linhas.
    Se a última página tiver menos linhas que rows_per_page, também é retornada.
    """
    # Por exemplo, se len(input_df)=100 e rows_per_page=25,
    # cria 4 DataFrames de 25 linhas cada.
    chunks = []
    for i in range(0, len(input_df), rows_per_page):
        chunk = input_df.iloc[i : i + rows_per_page]
        chunks.append(chunk)
    return chunks

# -------------------------------
# Carregamento de Dados
# -------------------------------
with st.container():
    try:
        escolas_df, estado_df, municipio_df = importar_arquivos_parquet()

        if escolas_df.empty:
            st.error("O DataFrame de escolas está vazio.")
        if municipio_df.empty:
            st.error("O DataFrame de municípios está vazio.")
        if estado_df.empty:
            st.error("O DataFrame de estados está vazio.")

        for df_nome, df_temp in [("escolas", escolas_df), ("município", municipio_df), ("estado", estado_df)]:
            if "ANO" not in df_temp.columns:
                st.error(f"Coluna 'ANO' não encontrada no DataFrame de {df_nome}.")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        escolas_df = pd.DataFrame()
        estado_df = pd.DataFrame()
        municipio_df = pd.DataFrame()
        st.stop()

# ======================================
# CONFIGURAÇÃO DA BARRA LATERAL (FILTROS)
# ======================================
st.sidebar.title("Filtros")

tipo_nivel_agregacao_selecionado = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"]
)

if tipo_nivel_agregacao_selecionado == "Escola":
    df = escolas_df.copy()
elif tipo_nivel_agregacao_selecionado == "Município":
    df = municipio_df.copy()
else:
    df = estado_df.copy()

if df.empty:
    st.error(f"Não há dados disponíveis para o nível de agregação '{tipo_nivel_agregacao_selecionado}'.")
    st.stop()

if st.sidebar.checkbox("Mostrar informações de debug", value=False):
    st.sidebar.write(f"Colunas no DataFrame de {tipo_nivel_agregacao_selecionado}:")
    st.sidebar.write(df.columns.tolist())
    st.sidebar.write(f"Primeiras linhas do DataFrame de {tipo_nivel_agregacao_selecionado}:")
    st.sidebar.write(df.head(2))

dicionario_das_etapas_de_ensino = padronizar_dicionario_de_etapas(df)

# Filtro do Ano
if "ANO" in df.columns:
    anos_disponiveis = sorted(df["ANO"].unique(), reverse=True)

    col1, col2 = st.sidebar.columns(2)
    if col1.button("Último Ano", key="btn_ultimo_ano"):
        st.session_state["anos_multiselect"] = [anos_disponiveis[0]]
    if col2.button("Todos Anos", key="btn_todos_anos"):
        st.session_state["anos_multiselect"] = anos_disponiveis

    if "anos_multiselect" not in st.session_state:
        st.session_state["anos_multiselect"] = [anos_disponiveis[0]]

    anos_selecionados = st.sidebar.multiselect(
        "Ano do Censo:",
        options=anos_disponiveis,
        default=st.session_state["anos_multiselect"],
        key="anos_multiselect_widget"
    )
    st.session_state["anos_multiselect"] = anos_selecionados

    if not anos_selecionados:
        st.warning("Por favor, selecione pelo menos um ano.")
        st.stop()

    df_filtrado = df[df["ANO"].isin(anos_selecionados)]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

# Filtro de Etapa, Subetapa e Série
lista_etapas_ensino = list(dicionario_das_etapas_de_ensino.keys())
etapa_ensino_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    lista_etapas_ensino
)

if etapa_ensino_selecionada not in dicionario_das_etapas_de_ensino:
    st.error(f"A etapa '{etapa_ensino_selecionada}' não foi encontrada no mapeamento de colunas.")
    st.stop()

if ("subetapas" in dicionario_das_etapas_de_ensino[etapa_ensino_selecionada] and
    dicionario_das_etapas_de_ensino[etapa_ensino_selecionada]["subetapas"]):
    subetapas_disponiveis = list(dicionario_das_etapas_de_ensino[etapa_ensino_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

lista_de_series_das_etapas_de_ensino = []
if (
    subetapa_selecionada != "Todas"
    and "series" in dicionario_das_etapas_de_ensino[etapa_ensino_selecionada]
    and subetapa_selecionada in dicionario_das_etapas_de_ensino[etapa_ensino_selecionada]["series"]
):
    lista_de_series_das_etapas_de_ensino = list(
        dicionario_das_etapas_de_ensino[etapa_ensino_selecionada]["series"][subetapa_selecionada].keys()
    )
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + lista_de_series_das_etapas_de_ensino
    )
else:
    serie_selecionada = "Todas"

# Filtro de Dependência Administrativa
if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())
    st.sidebar.caption(f"Total de {len(dependencias_disponiveis)} dependências disponíveis")

    if "dep_selection" not in st.session_state:
        st.session_state["dep_selection"] = dependencias_disponiveis

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

    st.session_state["dep_selection"] = dependencia_selecionada

    if dependencia_selecionada:
        st.sidebar.success(f"{len(dependencia_selecionada)} dependência(s) selecionada(s)")
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
    else:
        st.sidebar.warning("Nenhuma dependência selecionada. Selecione pelo menos uma.")
        df_filtrado = df_filtrado[0:0]
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

# Identifica a coluna de dados
coluna_matriculas_por_etapa = procurar_coluna_matriculas_por_etapa(
    etapa_ensino_selecionada,
    subetapa_selecionada,
    serie_selecionada,
    dicionario_das_etapas_de_ensino
)

coluna_existe, coluna_real = confirmar_existencia_colunas_apos_normalizacao(df_filtrado, coluna_matriculas_por_etapa)

if coluna_existe:
    coluna_matriculas_por_etapa = coluna_real
    try:
        df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_matriculas_por_etapa], errors='coerce') > 0]
        if df_filtrado.empty:
            st.error("Não foi possível encontrar dados para a etapa selecionada.")
            st.stop()
    except Exception as e:
        st.warning(f"Erro ao filtrar dados por valor positivo: {e}")
else:
    st.warning("A coluna de matrículas correspondente não foi encontrada. Os resultados podem ficar inconsistentes.")

# ------------------------------
# Configurações da Tabela
# ------------------------------
# Agrupar as configurações da tabela em um expander
with st.sidebar.expander("Configurações avançadas da tabela", expanded=False):
    st.markdown("### Configurações da tabela")

    modificar_altura_tabela = st.checkbox("Ajustar altura da tabela", value=False,
                                          help="Permite ajustar a altura da tabela de dados")
    if modificar_altura_tabela:
        altura_tabela = st.slider("Altura da tabela (pixels)", 200, 1000, 600, 50)
    else:
        altura_tabela = 600

    # Colunas para exibir na tabela
    st.markdown("### Colunas adicionais")
    colunas_selecionadas_para_exibicao = []

    # Campos básicos
    if "ANO" in df_filtrado.columns:
        colunas_selecionadas_para_exibicao.append("ANO")

    # Definir colunas base de acordo com o tipo de visualização
    if tipo_nivel_agregacao_selecionado == "Escola":
        colunas_base = [
            "CODIGO DA ESCOLA",
            "NOME DA ESCOLA",
            "CODIGO DO MUNICIPIO",
            "NOME DO MUNICIPIO",
            "DEPENDENCIA ADMINISTRATIVA"
        ]
    elif tipo_nivel_agregacao_selecionado == "Município":
        colunas_base = [
            "CODIGO DO MUNICIPIO",
            "NOME DO MUNICIPIO",
            "DEPENDENCIA ADMINISTRATIVA"
        ]
    else:  # Estado
        colunas_base = [
            "DEPENDENCIA ADMINISTRATIVA",
            "CODIGO DA UF",
            "NOME DA UF",
        ]

    # Adicionar apenas colunas que existem no DataFrame
    for col in colunas_base:
        if col in df_filtrado.columns:
            colunas_selecionadas_para_exibicao.append(col)
        else:
            st.warning(f"Coluna '{col}' não encontrada no DataFrame de {tipo_nivel_agregacao_selecionado}")

    # Tentar encontrar a coluna de matrículas principal independentemente da formatação
    for col in df_filtrado.columns:
        if "número de matrículas da educação básica" in col.lower().replace('\n', ''):
            if col not in colunas_selecionadas_para_exibicao:
                colunas_selecionadas_para_exibicao.append(col)
                break

    # Inclui a coluna de dados principal (caso exista)
    if coluna_matriculas_por_etapa in df_filtrado.columns and coluna_matriculas_por_etapa not in colunas_selecionadas_para_exibicao:
        colunas_selecionadas_para_exibicao.append(coluna_matriculas_por_etapa)

    # Multiselect de colunas opcionais
    conjunto_total_de_colunas = [c for c in df_filtrado.columns if c not in colunas_selecionadas_para_exibicao]
    colunas_adicionais_selecionadas_para_exibicao = st.multiselect(
        "Selecionar colunas adicionais:",
        conjunto_total_de_colunas,
        placeholder="Selecionar colunas adicionais..."
    )
    if colunas_adicionais_selecionadas_para_exibicao:
        colunas_selecionadas_para_exibicao.extend(colunas_adicionais_selecionadas_para_exibicao)

    # Garantir que todas as colunas selecionadas existam no DataFrame
    colunas_matriculas_por_etapa_existentes = [c for c in colunas_selecionadas_para_exibicao if
                                               c in df_filtrado.columns]
    if len(colunas_matriculas_por_etapa_existentes) != len(colunas_selecionadas_para_exibicao):
        st.warning("Algumas colunas selecionadas não existem no DataFrame atual.")

# -------------------------------
# Botões de Download
# -------------------------------
st.sidebar.markdown("### Download dos dados")
col1, col2 = st.sidebar.columns(2)

if 'filtro_matriculas_tipo' not in st.session_state:
    st.session_state.filtro_matriculas_tipo = "Sem filtro"

try:
    coluna_existe = False
    coluna_real = coluna_matriculas_por_etapa

    if coluna_matriculas_por_etapa in df_filtrado.columns:
        coluna_existe = True
    else:
        coluna_normalizada = coluna_matriculas_por_etapa.replace('\n', '').lower().strip()
        for col in df_filtrado.columns:
            if col.replace('\n', '').lower().strip() == coluna_normalizada:
                coluna_existe = True
                coluna_real = col
                break

    with pd.option_context('mode.chained_assignment', None):
        df_filtrado_tabela = df_filtrado[colunas_matriculas_por_etapa_existentes].copy()

        for col in df_filtrado_tabela.columns:
            if col.startswith("Número de"):
                df_filtrado_tabela[col] = pd.to_numeric(df_filtrado_tabela[col], errors='coerce')

        if coluna_existe and coluna_real in df_filtrado_tabela.columns:
            tabela_dados = df_filtrado_tabela.sort_values(by=coluna_real, ascending=False)
        else:
            tabela_dados = df_filtrado_tabela

        tabela_exibicao = tabela_dados.copy()

        # Formatar colunas numéricas
        for col in tabela_exibicao.columns:
            if col.startswith("Número de"):
                tabela_exibicao[col] = tabela_exibicao[col].apply(
                    lambda x: aplicar_padrao_numerico_brasileiro(x) if pd.notnull(x) else "-"
                )

    if tabela_dados.empty:
        st.sidebar.warning("Não há dados para download com os filtros atuais.")
    else:
        try:
            csv_data = gerar_arquivo_csv(tabela_dados)
            with col1:
                st.download_button(
                    label="Baixar CSV",
                    data=csv_data,
                    file_name=f'dados_{etapa_ensino_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.csv',
                    mime='text/csv',
                )
        except Exception as e:
            st.error(f"Erro ao preparar CSV para download: {str(e)}")

        try:
            excel_data = gerar_planilha_excel(tabela_dados)
            with col2:
                st.download_button(
                    label="Baixar Excel",
                    data=excel_data,
                    file_name=f'dados_{etapa_ensino_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
        except Exception as e:
            st.error(f"Erro ao preparar Excel para download: {str(e)}")

except Exception as e:
    st.error(f"Erro ao preparar dados para download: {str(e)}")
    if 'tabela_dados' not in locals() or 'tabela_exibicao' not in locals():
        tabela_dados = df_filtrado[colunas_matriculas_por_etapa_existentes].copy() if not df_filtrado.empty else pd.DataFrame()
        tabela_exibicao = tabela_dados.copy()

# -------------------------------
# Cabeçalho e Informações Iniciais
# -------------------------------
# Importa tudo do config_containers
from layout_primeiros_indicadores import (
    obter_estilo_css_container,
    aplicar_padrao_numerico_brasileiro,
    construir_grafico_linha_evolucao,
    PARAMETROS_ESTILO_CONTAINER
)
# -----------------------------------------
# 1) Injetar o CSS de estilo dos containers
# -----------------------------------------
st.markdown(obter_estilo_css_container(), unsafe_allow_html=True)

st.title("Meu Dashboard")

# -----------------------------
# 2) Dados de exemplo
# -----------------------------
dados_absolutos = {
    "Rede": ["Estaduais", "Municipais", "Privadas"],
    "Escolas": [408, 2228, 350],
    "Matrículas": [274436, 607055, 100000],
    "Professores": [50816, 117972, 25000]
}
df_absolutos = pd.DataFrame(dados_absolutos)

df_evolucao = pd.DataFrame({
    "Ano": list(range(2015, 2026)),
    "Escolas": [400 + (i * 5) for i in range(11)],
    "Matrículas": [800000 + (i * 8000) for i in range(11)],
    "Professores": [15000 + (i * 600) for i in range(11)],
})

# Transformamos em formato 'melt' para plotar 3 linhas separadas no Altair
df_transformado = df_evolucao.melt(id_vars="Ano", var_name="Categoria", value_name="Valor")

# -----------------------------------------------------
# 3) Criar duas colunas para exibir lado a lado
# -----------------------------------------------------
coluna_esquerda, coluna_direita = st.columns(2)
# -----------------------------------------------------
# 4) CONTAINER ESQUERDO: Tabela de dados absolutos
# -----------------------------------------------------
with coluna_esquerda:
    # Abre um container HTML
    st.markdown('<div class="container-custom">', unsafe_allow_html=True)
    # Título do container
    st.markdown('<div class="container-title">Dados Absolutos</div>', unsafe_allow_html=True)


    # Função para converter imagens em strings base64
    def get_image_as_base64(file_path):
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()


    # Converter os ícones para base64
    try:
        icone_escolas_base64 = get_image_as_base64("icones/Escolas.png")
        icone_matriculas_base64 = get_image_as_base64("icones/Matriculas.png")
        icone_professores_base64 = get_image_as_base64("icones/Professores.png")
    except Exception as e:
        st.error(f"Erro ao carregar ícones: {e}")
        # Valores vazios como fallback se houver erro
        icone_escolas_base64 = ""
        icone_matriculas_base64 = ""
        icone_professores_base64 = ""

    # Montagem de tabela via HTML com imagens em base64
    tabela_html = f"""
    <table class="custom-table container-text">
        <colgroup>
            <col /><col /><col /><col /><col />
        </colgroup>
        <thead>
            <tr>
                <th></th>
                <th><strong>Estaduais</strong></th>
                <th><strong>Municipais</strong></th>
                <th><strong>Privadas</strong></th>
                <th><strong>Total</strong></th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>
                    <img class="icone" src="data:image/png;base64,{icone_escolas_base64}" />
                    Escolas
                </strong></td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Escolas'][0])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Escolas'][1])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Escolas'][2])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Escolas'].sum())}</td>
            </tr>
            <tr>
                <td><strong>
                    <img class="icone" src="data:image/png;base64,{icone_matriculas_base64}" />
                    Matrículas
                </strong></td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Matrículas'][0])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Matrículas'][1])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Matrículas'][2])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Matrículas'].sum())}</td>
            </tr>
            <tr>
                <td><strong>
                    <img class="icone" src="data:image/png;base64,{icone_professores_base64}" />
                    Professores
                </strong></td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Professores'][0])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Professores'][1])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Professores'][2])}</td>
                <td>{aplicar_padrao_numerico_brasileiro(df_absolutos['Professores'].sum())}</td>
            </tr>
        </tbody>
    </table>
    """

    st.markdown(tabela_html, unsafe_allow_html=True)

    # Fecha o container
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------
# 5) CONTAINER DIREITO: Gráfico de linhas
# -----------------------------------------------------
with coluna_direita:
    st.markdown('<div class="container-custom">', unsafe_allow_html=True)
    st.markdown('<div class="container-title">Evolução dos números</div>', unsafe_allow_html=True)

    # Utilizamos nossa função construir_grafico_linha_evolucao
    grafico = construir_grafico_linha_evolucao(
        df_transformado=df_transformado,
        largura=450,         # Ajuste se preferir
        altura=300,         # Ajuste se preferir
        espessura_linha=4,  # Espessura da linha
        tamanho_ponto=100     # Tamanho das bolinhas
    )
    st.altair_chart(grafico, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown(f"## {TITULO_DADOS_DETALHADOS}")

if 'tabela_exibicao' not in locals() or tabela_exibicao.empty:
    st.warning("Não há dados para exibir com os filtros selecionados.")
else:

    st.markdown(f'<div class="table-header">Dados Detalhados - {tipo_nivel_agregacao_selecionado}</div>', unsafe_allow_html=True)

    if tipo_nivel_agregacao_selecionado == "Estado":
        try:
            colunas_essenciais = ["DEPENDENCIA ADMINISTRATIVA"]
            if coluna_real in tabela_exibicao.columns:
                colunas_essenciais.append(coluna_real)
            for col in ["ANO", "CODIGO DA UF", "NOME DA UF"]:
                if col in tabela_exibicao.columns:
                    colunas_essenciais.append(col)
            tabela_simplificada = tabela_exibicao[colunas_essenciais].copy()

            st.write("Dados por Dependência Administrativa:")
            st.dataframe(tabela_simplificada, height=altura_tabela, use_container_width=True)

            if coluna_real in tabela_simplificada.columns:
                total_col = 0
                if coluna_real in tabela_dados.columns:
                    total_col = tabela_dados[coluna_real].sum()

                st.markdown(f"**Total de {coluna_real}:** {aplicar_padrao_numerico_brasileiro(total_col)}")

        except Exception as e:
            st.error(f"Erro ao exibir tabela para nível Estado: {str(e)}")
            st.write("Tentando exibição alternativa...")
            try:
                if ("DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns and
                    coluna_matriculas_por_etapa in df_filtrado.columns):
                    resumo = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[coluna_matriculas_por_etapa].sum().reset_index()
                    st.write("Resumo por Dependência Administrativa:")
                    st.dataframe(resumo, use_container_width=True)
                else:
                    st.write("Dados disponíveis:")
                    st.dataframe(df_filtrado.head(100), use_container_width=True)
            except:
                st.error("Não foi possível exibir dados mesmo no formato simplificado.")

    else:
        # ------------------------------------------------------------
        # Exemplo de Paginação manual por 'chunk' (split_frame)
        # ------------------------------------------------------------
        def split_frame(df, size):
            return [df[i:i + size] for i in range(0, len(df), size)]

        # Função para formatar número com separador de milhar (padrão brasileiro)
        def format_number_br(num):
            """Converte 6883 -> '6.883'."""
            return f"{num:,}".replace(",", ".")

        df_sem_filtros_texto = tabela_exibicao.copy()

        # ------------------------------------------------------------
        # Filtros manuais (acima das colunas)
        # ------------------------------------------------------------
        col_filters = {}
        if len(df_sem_filtros_texto.columns) > 0:
            filtro_cols = st.columns(len(df_sem_filtros_texto.columns))
            for i, col_name in enumerate(df_sem_filtros_texto.columns):
                with filtro_cols[i]:
                    st.write(f"**{col_name}**")
                    col_filters[col_name] = st.text_input(
                        label=f"Filtro para {col_name}",
                        key=f"filter_{col_name}",
                        label_visibility="collapsed",
                        placeholder=f"Filtrar {col_name}..."
                    )

        df_texto_filtrado = df_sem_filtros_texto.copy()

        # Aplicação dos filtros
        for col_name, filter_text in col_filters.items():
            if filter_text:
                try:
                    filter_text_escaped = re.escape(filter_text)
                    # Verifica se a coluna pode ser tratada como numérica
                    if (
                            col_name.startswith("Número de")
                            or pd.api.types.is_numeric_dtype(df_texto_filtrado[col_name])
                    ):
                        filter_text_ponto = filter_text.replace(",", ".")
                        # Tenta converter para float
                        try:
                            if (
                                    filter_text_ponto.replace(".", "", 1).isdigit()
                                    and filter_text_ponto.count(".") <= 1
                            ):
                                num_value = float(filter_text_ponto)
                                df_texto_filtrado = df_texto_filtrado[
                                    df_texto_filtrado[col_name] == num_value
                                    ]
                            else:
                                df_texto_filtrado = df_texto_filtrado[
                                    df_texto_filtrado[col_name].astype(str).str.contains(
                                        filter_text_escaped,
                                        case=False,
                                        regex=True
                                    )
                                ]
                        except ValueError:
                            df_texto_filtrado = df_texto_filtrado[
                                df_texto_filtrado[col_name].astype(str).str.contains(
                                    filter_text_escaped,
                                    case=False,
                                    regex=True
                                )
                            ]
                    else:
                        df_texto_filtrado = df_texto_filtrado[
                            df_texto_filtrado[col_name].astype(str).str.contains(
                                filter_text_escaped,
                                case=False,
                                regex=True
                            )
                        ]
                except Exception as e:
                    st.warning(f"Erro ao aplicar filtro na coluna {col_name}: {e}")

        # ------------------------------------------------------------
        # Paginação manual
        # ------------------------------------------------------------
        try:
            # Remove a linha "Total de Registros após filtros: X"
            # e vamos direto para a paginação.

            if "page_size" not in st.session_state:
                st.session_state["page_size"] = 10

            paginated_frames = split_frame(df_texto_filtrado, st.session_state["page_size"])
            total_pages = len(paginated_frames)

            if total_pages == 0:
                st.warning("Nenhum registro para exibir após filtragem.")
                st.stop()

            # Inicializa current_page se não existir
            if "current_page" not in st.session_state:
                st.session_state["current_page"] = 1

            # Garante que a página atual seja válida
            if st.session_state["current_page"] > total_pages:
                st.session_state["current_page"] = 1

            # Mostra a tabela da página atual
            df_pagina_atual = paginated_frames[st.session_state["current_page"] - 1]
            st.dataframe(df_pagina_atual, height=altura_tabela, use_container_width=True)

            # --------------------------------------------------------
            # Layout em uma única linha para controles de paginação
            # --------------------------------------------------------
            try:
                # Definição de parâmetros de layout - AJUSTE AQUI!
                LARGURA_TOTAL = 10  # Escala relativa total (soma de todas as larguras)

                # Larguras das colunas principais
                L_INFO = 3.0  # Largura da coluna de informações (Total: registros...)
                L_ANTERIOR = 0.2  # Largura do botão Anterior
                L_ESPACO1 = 0.3  # Espaço entre Anterior e Próximo
                L_PROXIMO = 1.2  # Largura do botão Próximo
                L_ESPACO2 = 2.0  # Espaço entre Próximo e Página
                L_PAGINA = 1.2  # Largura da seção Página
                L_ESPACO3 = 0.3  # Espaço entre Página e Itens por Página
                L_ITENS = 1.8  # Largura da seção Itens por Página

                # Proporções dentro das subcolunas
                PROP_LABEL_PAGINA = 0.33  # Proporção do label "Página:" (0-1)
                PROP_LABEL_ITENS = 0.55  # Proporção do label "Itens por página:" (0-1)

                # Ajuste de padding para alinhamento vertical (em pixels)
                PADDING_TOP = 5

                # Criação das colunas com base nos parâmetros definidos
                col_info, col_anterior, col_espaco1, col_proximo, col_espaco2, col_pagina, col_espaco3, col_itens = st.columns(
                    [L_INFO, L_ANTERIOR, L_ESPACO1, L_PROXIMO, L_ESPACO2, L_PAGINA, L_ESPACO3, L_ITENS]
                )

                # 1) Texto: "Total: registros | Página x de y"
                with col_info:
                    total_registros_br = format_number_br(len(df_texto_filtrado))
                    st.markdown(
                        f"**Total: {total_registros_br} registros | Página {st.session_state['current_page']} de {format_number_br(total_pages)}**"
                    )

                # 2) Botão ◀ Anterior
                with col_anterior:
                    if st.button("◀ Anterior", disabled=st.session_state["current_page"] <= 1,
                                 use_container_width=True):
                        st.session_state["current_page"] -= 1
                        st.rerun()

                # Espaço entre Anterior e Próximo
                with col_espaco1:
                    st.empty()

                # 3) Botão Próximo ▶
                with col_proximo:
                    if st.button("Próximo ▶", disabled=st.session_state["current_page"] >= total_pages,
                                 use_container_width=True):
                        st.session_state["current_page"] += 1
                        st.rerun()

                # Espaço entre Próximo e Página
                with col_espaco2:
                    st.empty()

                # 4) Número da Página com label
                with col_pagina:
                    container = st.container()
                    label_col, input_col = container.columns([PROP_LABEL_PAGINA, 1 - PROP_LABEL_PAGINA])

                    with label_col:
                        st.markdown(f"<div style='padding-top: {PADDING_TOP}px;'>Página:</div>", unsafe_allow_html=True)

                    with input_col:
                        nova_pagina = st.number_input(
                            "",
                            min_value=1,
                            max_value=total_pages,
                            value=st.session_state["current_page"],
                            step=1,
                            label_visibility="collapsed"
                        )
                        if nova_pagina != st.session_state["current_page"]:
                            st.session_state["current_page"] = nova_pagina
                            st.rerun()

                # Espaço entre Página e Itens por Página
                with col_espaco3:
                    st.empty()

                # 5) Itens por página com label
                with col_itens:
                    container = st.container()
                    label_col, select_col = container.columns([PROP_LABEL_ITENS, 1 - PROP_LABEL_ITENS])

                    with label_col:
                        st.markdown(f"<div style='padding-top: {PADDING_TOP}px;'>Itens por página:</div>",
                                    unsafe_allow_html=True)

                    with select_col:
                        novo_page_size = st.selectbox(
                            "",
                            options=[10, 25, 50, 100],
                            index=[10, 25, 50, 100].index(st.session_state["page_size"]),
                            label_visibility="collapsed"
                        )
                        if novo_page_size != st.session_state["page_size"]:
                            st.session_state["page_size"] = novo_page_size
                            st.session_state["current_page"] = 1
                            st.rerun()

            except Exception as e:
                st.error(f"Erro ao exibir a tabela: {str(e)}")

        except Exception as e:
            st.error(f"Erro ao exibir a tabela: {str(e)}")
# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
if 'RODAPE_NOTA' in globals():
    st.markdown(RODAPE_NOTA)
else:
    st.markdown(
        """
        <style>
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 12px;
        }
        </style>
        <div class="footer">
            © Dashboard Educacional - Desenvolvido para visualização de dados do Censo Escolar
            <br>Última atualização: Março/2025
        </div>
        """,
        unsafe_allow_html=True
    )

registro_conclusao_processamento = time.time()
tempo_total_processamento_segundos = round(
    registro_conclusao_processamento - st.session_state.get('tempo_inicio', registro_conclusao_processamento),
    2
)
st.session_state['tempo_inicio'] = registro_conclusao_processamento
st.caption(f"Tempo de processamento: {tempo_total_processamento_segundos} segundos")
