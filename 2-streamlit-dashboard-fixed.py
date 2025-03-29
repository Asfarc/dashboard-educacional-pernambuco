import streamlit as st
import pandas as pd
import os
import io
import json

# ----------------------
# Constantes de Exemplo
# ----------------------
TITULO_DASHBOARD = "Painel de Indicadores PNE"
ROTULO_TOTAL_MATRICULAS = "Total de Matrículas"
ROTULO_MEDIA_POR_ESCOLA = "Média por Escola"
ROTULO_MEDIA_MATRICULAS = "Média de Matrículas"
ROTULO_TOTAL_ESCOLAS = "Total de Escolas"
ROTULO_TOTAL_MUNICIPIOS = "Total de Municípios"
ROTULO_MAXIMO_MATRICULAS = "Máximo de Matrículas"
TITULO_DADOS_DETALHADOS = "Dados Detalhados"
ROTULO_BTN_DOWNLOAD_CSV = "Baixar CSV"
ROTULO_BTN_DOWNLOAD_EXCEL = "Baixar Excel"
RODAPE_NOTA = "© 2025 - Meu Rodapé Personalizado"

ERRO_ARQUIVOS_NAO_ENCONTRADOS = "Não encontrei os arquivos Parquet (escolas, estado, municipio)."
INFO_VERIFICAR_ARQUIVOS = "Verifique se os arquivos .parquet estão no diretório correto."
ERRO_ETAPA_NAO_ENCONTRADA = "Etapa não encontrada: {}"
ERRO_SUBETAPA_NAO_ENCONTRADA = "Subetapa '{}' não encontrada na etapa '{}'"
ERRO_SERIE_NAO_ENCONTRADA = "Série '{}' não encontrada na subetapa '{}'"

# ----------------------
# Configuração da Página
# ----------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------
# CSS Básico para Sidebar
# ----------------------
css_sidebar = """
<style>
    /* Fundo da barra lateral */
    [data-testid="stSidebar"] {
        background-color: #364b60;
    }
    /* Deixa os textos (títulos, labels) em branco */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stRadio span:not([role="radio"]) {
        color: white !important;
    }
    /* Caixas de seleção e etc. ficam em branco */
    [data-testid="stSidebar"] .stSelectbox, 
    [data-testid="stSidebar"] .stSlider, 
    [data-testid="stSidebar"] .stRadio, 
    [data-testid="stSidebar"] .stTextInput, 
    [data-testid="stSidebar"] .stMultiselect {
        color: black;
        background-color: white;
    }
</style>
"""
st.markdown(css_sidebar, unsafe_allow_html=True)


# ----------------------
# Funções Auxiliares
# ----------------------
@st.cache_data
def carregar_dados():
    """Carrega dados Parquet de escolas, estado e municipio."""
    diretorios_possiveis = [".", "data", "dados"]
    escolas_df = estado_df = municipio_df = None
    for diretorio in diretorios_possiveis:
        e_path = os.path.join(diretorio, "escolas.parquet")
        uf_path = os.path.join(diretorio, "estado.parquet")
        m_path = os.path.join(diretorio, "municipio.parquet")
        if os.path.exists(e_path) and os.path.exists(uf_path) and os.path.exists(m_path):
            escolas_df = pd.read_parquet(e_path)
            estado_df = pd.read_parquet(uf_path)
            municipio_df = pd.read_parquet(m_path)
            break
    if escolas_df is None or estado_df is None or municipio_df is None:
        st.error(ERRO_ARQUIVOS_NAO_ENCONTRADOS)
        st.info(INFO_VERIFICAR_ARQUIVOS)
        st.stop()
    return escolas_df, estado_df, municipio_df


def carregar_mapeamento_colunas():
    """Exemplo de leitura de mapeamento de colunas via JSON."""
    diretorios_possiveis = [".", "data", "dados"]
    for diretorio in diretorios_possiveis:
        json_path = os.path.join(diretorio, "mapeamento_colunas.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}  # Se não achar o arquivo, retorna dicionário vazio


def criar_mapeamento(df):
    """Cria um mapeamento (etapa -> coluna) simples."""
    # Aqui é apenas um exemplo. Ajuste ao seu JSON.
    base = carregar_mapeamento_colunas()
    if not base:
        return {}
    colunas_df = {c.lower(): c for c in df.columns}

    def get_col(c):
        # Tenta achar a coluna no DF
        if c in df.columns:
            return c
        c_low = c.lower()
        if c_low in colunas_df:
            return colunas_df[c_low]
        return c  # fallback

    saida = {}
    for etapa, info in base.items():
        saida[etapa] = {
            "coluna_principal": get_col(info.get("coluna_principal", "")),
            "subetapas": {},
            "series": {}
        }
        for sub, val in info.get("subetapas", {}).items():
            saida[etapa]["subetapas"][sub] = get_col(val)
        for sub, d_serie in info.get("series", {}).items():
            saida[etapa]["series"][sub] = {}
            for s, col_serie in d_serie.items():
                saida[etapa]["series"][sub][s] = get_col(col_serie)
    return saida


def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    """Retorna o nome da coluna correspondente."""
    if etapa not in mapeamento:
        return ""
    if subetapa == "Todas":
        return mapeamento[etapa]["coluna_principal"]
    if subetapa not in mapeamento[etapa]["subetapas"]:
        return mapeamento[etapa]["coluna_principal"]
    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]
    # Caso específico de série
    if subetapa in mapeamento[etapa]["series"]:
        if serie in mapeamento[etapa]["series"][subetapa]:
            return mapeamento[etapa]["series"][subetapa][serie]
    return mapeamento[etapa]["subetapas"][subetapa]


def formatar_numero_br(x):
    """Formata número no padrão brasileiro (milhares com ponto, decimais com vírgula)."""
    if pd.isna(x):
        return ""
    try:
        val = float(x)
        if val.is_integer():
            return f"{int(val):,}".replace(",", ".")
        else:
            inteiro = int(val)
            dec = abs(val - inteiro)
            return f"{inteiro:,}".replace(",", ".") + f",{dec:.2f}".replace("0.", "")
    except:
        return str(x)


def converter_df_para_csv(df):
    if df.empty:
        return "Sem dados".encode("utf-8")
    return df.to_csv(index=False).encode("utf-8")


def converter_df_para_excel(df):
    output = io.BytesIO()
    if df.empty:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame({"Sem dados": []}).to_excel(writer, sheet_name="SemDados", index=False)
    else:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name="Dados", index=False)
    return output.getvalue()


# ----------------------
# Carrega os dados
# ----------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()
except:
    st.stop()

# ----------------------
# Barra Lateral Única
# ----------------------
st.sidebar.title("Filtros e Configurações")

# Nível de Agregação
tipo_agr = st.sidebar.radio("Nível de Agregação:", ["Escola", "Município", "Estado"], index=0)
if tipo_agr == "Escola":
    df_base = escolas_df
elif tipo_agr == "Município":
    df_base = municipio_df
else:
    df_base = estado_df

mapeamento = criar_mapeamento(df_base)

# Filtro de Ano
if "ANO" in df_base.columns:
    anos_disp = sorted(df_base["ANO"].dropna().unique())
    anos_sel = st.sidebar.multiselect("Ano(s):", anos_disp, default=anos_disp[:1])
    if not anos_sel:
        st.warning("Selecione ao menos um ano.")
        st.stop()
    df_filtrado = df_base[df_base["ANO"].isin(anos_sel)]
else:
    df_filtrado = df_base.copy()

# Filtro de Etapa
etapas = list(mapeamento.keys())
if etapas:
    etapa_sel = st.sidebar.selectbox("Etapa:", etapas, index=0)
else:
    etapa_sel = ""

subetapas = []
if etapa_sel and etapa_sel in mapeamento:
    subetapas = list(mapeamento[etapa_sel]["subetapas"].keys())

sub_sel = "Todas"
if subetapas:
    sub_sel = st.sidebar.selectbox("Subetapa:", ["Todas"] + subetapas, index=0)

series_disp = []
if sub_sel != "Todas":
    series_disp = list(mapeamento[etapa_sel]["series"].get(sub_sel, {}).keys())

serie_sel = "Todas"
if series_disp:
    serie_sel = st.sidebar.selectbox("Série:", ["Todas"] + series_disp, index=0)

# Dependência Administrativa
if "DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns:
    deps_disp = sorted(df_filtrado["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())
    deps_sel = st.sidebar.multiselect("Dependência Administrativa:", deps_disp, default=deps_disp)
    df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(deps_sel)]

# Escolhe a coluna de dados principal
col_dados = obter_coluna_dados(etapa_sel, sub_sel, serie_sel, mapeamento)
if col_dados not in df_filtrado.columns:
    # fallback: tenta "coluna_principal"
    if etapa_sel in mapeamento:
        col_dados = mapeamento[etapa_sel]["coluna_principal"]

# Filtra para valores > 0 (opcional)
if col_dados in df_filtrado.columns:
    df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[col_dados], errors='coerce') > 0]

st.sidebar.markdown("---")

# Ordenação
colunas_disp = df_filtrado.columns.tolist()
if col_dados in colunas_disp:
    idx_default = colunas_disp.index(col_dados)
else:
    idx_default = 0 if colunas_disp else 0
col_ordenacao = st.sidebar.selectbox("Ordenar por:", colunas_disp, index=idx_default)
ordem = st.sidebar.radio("Ordem:", ["Crescente", "Decrescente"], index=1)
asc = True if ordem == "Crescente" else False

# Quantidade máxima de linhas
max_linhas = st.sidebar.slider("Máximo de linhas:", 1, 5000, 50, step=1)

# Download
st.sidebar.markdown("### Exportar Dados")
# Botão CSV
# Vamos preparar o df_ordenado depois que o usuário escolher col_ordenacao
# e exibir no main
# Então baixamos ele no final
# (ainda assim, podemos só declarar aqui e criar o download no final)

# ----------------------
# Área Principal
# ----------------------
st.title(TITULO_DASHBOARD)
anos_texto = ", ".join(map(str, anos_sel))
st.markdown(f"**Visualização:** {tipo_agr} | **Anos:** {anos_texto}")

filtro_texto = f"**Etapa:** {etapa_sel}"
if sub_sel != "Todas":
    filtro_texto += f" | **Subetapa:** {sub_sel}"
if serie_sel != "Todas":
    filtro_texto += f" | **Série:** {serie_sel}"
st.markdown(filtro_texto)

# KPIs
col1, col2, col3 = st.columns(3)
try:
    total = df_filtrado[col_dados].sum()
    col1.metric(ROTULO_TOTAL_MATRICULAS, f"{int(total):,}".replace(",", "."))  # formata inteiro
except:
    col1.metric(ROTULO_TOTAL_MATRICULAS, "-")

try:
    media = df_filtrado[col_dados].mean()
    if tipo_agr == "Escola":
        col2.metric(ROTULO_MEDIA_POR_ESCOLA, formatar_numero_br(media))
    else:
        col2.metric(ROTULO_MEDIA_MATRICULAS, formatar_numero_br(media))
except:
    col2.metric("Média", "-")

try:
    if tipo_agr == "Escola":
        col3.metric(ROTULO_TOTAL_ESCOLAS, f"{len(df_filtrado):,}".replace(",", "."))
    elif tipo_agr == "Município":
        col3.metric(ROTULO_TOTAL_MUNICIPIOS, f"{len(df_filtrado):,}".replace(",", "."))
    else:
        maximo = df_filtrado[col_dados].max()
        col3.metric(ROTULO_MAXIMO_MATRICULAS, formatar_numero_br(maximo))
except:
    col3.metric("Indicador", "-")

st.markdown(f"## {TITULO_DADOS_DETALHADOS}")

# Ordena e limita
df_ordenado = df_filtrado.sort_values(by=col_ordenacao, ascending=asc).head(max_linhas).copy()

# Formata colunas numéricas no padrão brasileiro
for c in df_ordenado.select_dtypes(include=["int", "float"]).columns:
    df_ordenado[c] = df_ordenado[c].apply(formatar_numero_br)

# Exibe o dataframe
st.dataframe(df_ordenado, use_container_width=True)

# Botões de download
csv_data = converter_df_para_csv(df_filtrado.sort_values(by=col_ordenacao, ascending=asc))
excel_data = converter_df_para_excel(df_filtrado.sort_values(by=col_ordenacao, ascending=asc))

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        label=ROTULO_BTN_DOWNLOAD_CSV,
        data=csv_data,
        file_name="dados_export.csv",
        mime="text/csv"
    )
with col_dl2:
    st.download_button(
        label=ROTULO_BTN_DOWNLOAD_EXCEL,
        data=excel_data,
        file_name="dados_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")
st.markdown(RODAPE_NOTA)
