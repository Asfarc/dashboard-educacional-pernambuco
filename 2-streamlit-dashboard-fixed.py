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
def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR:
    Ex.: 1234567 -> '1.234.567'
         1234.56 -> '1.234,56'
    Se o número for NaN ou '-', retorna '-'.
    Aplica formatação apenas a valores numéricos.
    """
    if pd.isna(numero) or numero == "-":
        return "-"

    # Verifica se o valor é numérico
    try:
        float_numero = float(numero)
        # Exibe sem casas decimais se for inteiro
        if float_numero.is_integer():
            return f"{int(float_numero):,}".replace(",", ".")
        else:
            # 2 casas decimais
            parte_inteira = int(float_numero)
            parte_decimal = abs(float_numero - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except (ValueError, TypeError):
        # Se não for numérico, retorna o valor original como string
        return str(numero)


@st.cache_data(ttl=3600)  # Cache por 1 hora
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    - Lê os arquivos: escolas.parquet, estado.parquet e municipio.parquet.
    - Converte colunas que começam com 'Número de' para tipo numérico.
    - Mantém outras colunas como texto.
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

        # Agora o processamento das colunas
        for df_ in [escolas_df, estado_df, municipio_df]:
            for col in df_.columns:
                # Converte apenas colunas de matrículas para numérico
                if col.startswith("Número de"):
                    df_[col] = pd.to_numeric(df_[col], errors='coerce')
                elif col in ["ANO", "CODIGO DO MUNICIPIO", "CODIGO DA ESCOLA", "CODIGO DA UF"]:
                    # Garante que estas colunas sejam tratadas como texto
                    df_[col] = df_[col].astype(str)

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
    # Normalizar nomes de colunas para lidar com inconsistências como quebras de linha
    colunas_map = {}
    for col in df.columns:
        # Normaliza removendo quebras de linha e espaços extras
        nome_normalizado = col.replace('\n', '').lower().strip()
        colunas_map[nome_normalizado] = col

    def obter_coluna_real(nome_padrao):
        if nome_padrao in df.columns:
            return nome_padrao

        # Normaliza o nome padrão também
        nome_normalizado = nome_padrao.replace('\n', '').lower().strip()
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
    levando em conta variações de maiúsculas/minúsculas e quebras de linha.
    """
    if not coluna_nome:
        return False, ""

    if coluna_nome in df.columns:
        return True, coluna_nome

    # Normaliza removendo quebras de linha e espaços
    coluna_normalizada = coluna_nome.replace('\n', '').lower().strip()
    colunas_normalizadas = {col.replace('\n', '').lower().strip(): col for col in df.columns}

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
    # Inicializar as variáveis com valores vazios para garantir que elas existam
    escolas_df = pd.DataFrame()
    estado_df = pd.DataFrame()
    municipio_df = pd.DataFrame()

    # Carregar os dados
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

    # Criar DataFrames vazios caso não existam
    if 'escolas_df' not in locals():
        escolas_df = pd.DataFrame()
    if 'estado_df' not in locals():
        estado_df = pd.DataFrame()
    if 'municipio_df' not in locals():
        municipio_df = pd.DataFrame()

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
if (
    subetapa_selecionada != "Todas"
    and "series" in mapeamento_colunas[etapa_selecionada]
    and subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]
):
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
    try:
        # Filtrar apenas matrículas > 0 (se numérico)
        df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_dados], errors='coerce') > 0]
        if df_filtrado.empty:
            st.error("Não foi possível encontrar dados para a etapa selecionada.")
            st.stop()
    except Exception as e:
        st.warning(f"Erro ao filtrar dados por valor positivo: {e}")
        # Em caso de erro, não filtra nada além do que já foi feito
else:
    # Coluna não existe mesmo depois de verificação
    st.warning("A coluna de matrículas correspondente não foi encontrada. Os resultados podem ficar inconsistentes.")

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
        "DEPENDENCIA ADMINISTRATIVA"
    ]
elif tipo_visualizacao == "Município":
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
        colunas_tabela.append(col)
    else:
        st.sidebar.warning(f"Coluna '{col}' não encontrada no DataFrame de {tipo_visualizacao}")

# Tentar encontrar a coluna de matrículas principal independentemente da formatação
for col in df_filtrado.columns:
    if "número de matrículas da educação básica" in col.lower().replace('\n', ''):
        if col not in colunas_tabela:
            colunas_tabela.append(col)
            break

# Inclui a coluna de dados principal (caso exista)
if coluna_dados in df_filtrado.columns and coluna_dados not in colunas_tabela:
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

# Inicialização para filtros avançados de matrículas
if 'filtro_matriculas_tipo' not in st.session_state:
    st.session_state.filtro_matriculas_tipo = "Sem filtro"

# Preparar tabela para exibição e download
try:
    # Verificar se a coluna de dados existe, considerando possíveis variações no nome
    coluna_existe = False
    coluna_real = coluna_dados

    if coluna_dados in df_filtrado.columns:
        coluna_existe = True
    else:
        # Busca alternativa considerando quebras de linha
        coluna_normalizada = coluna_dados.replace('\n', '').lower().strip()
        for col in df_filtrado.columns:
            if col.replace('\n', '').lower().strip() == coluna_normalizada:
                coluna_existe = True
                coluna_real = col
                break

    # Criar cópia do DataFrame para exibição e downloads
    with pd.option_context('mode.chained_assignment', None):
        df_filtrado_tabela = df_filtrado[colunas_existentes].copy()

        # Converter apenas colunas de dados para numérico
        for col in df_filtrado_tabela.columns:
            if col.startswith("Número de"):
                df_filtrado_tabela[col] = pd.to_numeric(df_filtrado_tabela[col], errors='coerce')

        # Ordenar por coluna de dados (decrescente) se existir
        if coluna_existe and coluna_real in df_filtrado_tabela.columns:
            tabela_dados = df_filtrado_tabela.sort_values(by=coluna_real, ascending=False)
        else:
            tabela_dados = df_filtrado_tabela

        # Criar cópia para exibição (formatada)
        tabela_exibicao = tabela_dados.copy()

        # Formatar apenas colunas numéricas para exibição com separador de milhares
        for col in tabela_exibicao.columns:
            if col.startswith("Número de"):
                tabela_exibicao[col] = tabela_exibicao[col].apply(
                    lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                )

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
    if 'tabela_dados' not in locals() or 'tabela_exibicao' not in locals():
        tabela_dados = df_filtrado[colunas_existentes].copy() if not df_filtrado.empty else pd.DataFrame()
        tabela_exibicao = tabela_dados.copy()

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
                        if not df_filtrado.empty and coluna_dados in df_filtrado.columns:
                            media_por_dependencia = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[coluna_dados].mean()
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
    st.markdown('<div class="table-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="table-header">Dados Detalhados - {tipo_visualizacao}</div>', unsafe_allow_html=True)

    # Configurações de paginação e ordenação ANTES dos filtros
    if tipo_visualizacao != "Estado":
        config_col1, config_col2 = st.columns([1, 3])

        with config_col1:
            registros_por_pagina = st.selectbox(
                "Registros por página:",
                options=[10, 25, 50, 100, "Todos"],
                index=1  # Padrão: 25
            )

        with config_col2:
            opcoes_ordenacao = ["Maior valor", "Menor valor"]
            if "NOME DA ESCOLA" in tabela_exibicao.columns:
                opcoes_ordenacao.extend(["Alfabético (A-Z) por Escola", "Alfabético (Z-A) por Escola"])
            if "NOME DO MUNICIPIO" in tabela_exibicao.columns:
                opcoes_ordenacao.extend(["Alfabético (A-Z) por Município", "Alfabético (Z-A) por Município"])

            if coluna_real in tabela_exibicao.columns:
                ordem_tabela = st.radio(
                    "Ordenar por:",
                    opcoes_ordenacao,
                    horizontal=True
                )

                # Aplicar ordenação à tabela_dados e tabela_exibicao
                if ordem_tabela == "Maior valor":
                    tabela_dados = tabela_dados.sort_values(by=coluna_real, ascending=False)
                    tabela_exibicao = tabela_exibicao.loc[tabela_dados.index]
                elif ordem_tabela == "Menor valor":
                    tabela_dados = tabela_dados.sort_values(by=coluna_real, ascending=True)
                    tabela_exibicao = tabela_exibicao.loc[tabela_dados.index]
                elif "por Escola" in ordem_tabela and "NOME DA ESCOLA" in tabela_exibicao.columns:
                    tabela_exibicao = tabela_exibicao.sort_values(by="NOME DA ESCOLA",
                                                                  ascending=("A-Z" in ordem_tabela))
                elif "por Município" in ordem_tabela and "NOME DO MUNICIPIO" in tabela_exibicao.columns:
                    tabela_exibicao = tabela_exibicao.sort_values(by="NOME DO MUNICIPIO",
                                                                  ascending=("A-Z" in ordem_tabela))

    # Caso específico para nível "Estado"
    if tipo_visualizacao == "Estado":
        # [Código para Estado permanece igual]
        pass

    # Caso para nível "Escola" ou "Município"
    else:
        try:
            # Processar filtros avançados e obter tabela filtrada
            df_filtrado_final = tabela_exibicao.copy()

            # Aplicar filtros de texto por coluna alinhados diretamente acima da tabela
            # -----------------------------------------------------------------------
            col_filters = {}

            # Criar a linha de filtros - IMEDIATAMENTE antes da tabela
            filtro_cols = st.columns(len(df_filtrado_final.columns))

            # Adicionar os filtros diretamente acima das colunas da tabela
            for i, col_name in enumerate(df_filtrado_final.columns):
                with filtro_cols[i]:
                    st.write(f"**{col_name}**")
                    # Usar text_input simples para todas as colunas para manter o alinhamento
                    col_filters[col_name] = st.text_input(
                        "",
                        key=f"filter_{col_name}",
                        label_visibility="collapsed",
                        placeholder=f"Filtrar {col_name}..."
                    )

            # Aplicar os filtros de texto
            df_texto_filtrado = df_filtrado_final.copy()
            for col_name, filter_text in col_filters.items():
                if filter_text:
                    df_texto_filtrado = df_texto_filtrado[
                        df_texto_filtrado[col_name].astype(str).str.contains(filter_text, case=False)
                    ]

            # Paginação e exibição da tabela
            if len(df_texto_filtrado) > 0:
                if registros_por_pagina != "Todos":
                    registros_por_pagina = int(registros_por_pagina)
                    num_paginas = max(1, (len(df_texto_filtrado) - 1) // registros_por_pagina + 1)

                    pagina_atual = st.number_input(
                        "Página",
                        min_value=1,
                        max_value=num_paginas,
                        value=1,
                        step=1
                    )

                    inicio = (pagina_atual - 1) * registros_por_pagina
                    fim = min(inicio + registros_por_pagina, len(df_texto_filtrado))
                    df_paginado = df_texto_filtrado.iloc[inicio:fim]

                    # Exibição da tabela - após todos os controles
                    st.dataframe(df_paginado, height=altura_tabela, use_container_width=True)
                    st.caption(
                        f"Exibindo registros {inicio + 1} a {fim} de {len(df_texto_filtrado):,}".replace(",", ".")
                    )
                else:
                    # Exibição sem paginação
                    st.dataframe(df_texto_filtrado, height=altura_tabela, use_container_width=True)

                # Total
                if coluna_real in df_texto_filtrado.columns:
                    total_col = pd.to_numeric(tabela_dados.loc[df_texto_filtrado.index, coluna_real],
                                              errors='coerce').sum()
                    st.markdown(f"**Total de {coluna_real}:** {formatar_numero(total_col)}")
            else:
                st.warning("Nenhum registro encontrado com os filtros aplicados.")

        except Exception as e:
            st.error(f"Erro ao exibir a tabela: {str(e)}")
            st.dataframe(tabela_exibicao.head(100), height=altura_tabela, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

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

# Tempo de execução
tempo_final = time.time()
tempo_total = round(tempo_final - st.session_state.get('tempo_inicio', tempo_final), 2)
st.session_state['tempo_inicio'] = tempo_final
st.caption(f"Tempo de processamento: {tempo_total} segundos")
