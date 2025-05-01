# ======================  utils.py  ======================
import pandas as pd


def beautify(col: str) -> str:
    """Transforma 'CODIGO DO MUNICIPIO' -> 'Codigo Do Municipio'."""
    col = col.replace("\n", " ").strip()
    return " ".join(p.capitalize() for p in col.lower().split())


def format_number_br(num):
    """6883 -> '6.883'  |  1234.5 -> '1.234,50'. Retorna '-' p/ NaN."""
    if pd.isna(num) or num == "-":
        return "-"
    try:
        n = float(num)
        if n.is_integer():
            return f"{int(n):,}".replace(",", ".")
        inteiro, frac = str(f"{n:,.2f}").split(".")
        return f"{inteiro.replace(',', '.')},{frac}"
    except Exception:
        return str(num)


# ======================  data_io.py  =====================
import os, io, pandas as pd, streamlit as st
from utils import format_number_br


@st.cache_data(ttl=3600)
def load_parquets():
    """Carrega e tipa os três .parquet esperados; retorna (escola, uf, mun)."""
    paths = {
        "escolas": "escolas.parquet",
        "estado": "estado.parquet",
        "municipio": "municipio.parquet",
    }
    if not all(os.path.exists(p) for p in paths.values()):
        st.error("Arquivos .parquet não encontrados.")
        st.stop()

    dfs = {k: pd.read_parquet(p) for k, p in paths.items()}

    for df in dfs.values():
        for col in df.columns:
            if col.startswith("Número de"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif col in ("ANO", "CODIGO DO MUNICIPIO", "CODIGO DA ESCOLA", "CODIGO DA UF"):
                df[col] = df[col].astype(str)
    return dfs["escolas"], dfs["estado"], dfs["municipio"]


@st.cache_data
def df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data
def df_to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as wr:
        df.to_excel(wr, index=False, sheet_name="Dados")
        ws, wb = wr.sheets["Dados"], wr.book
        header = wb.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "top",
            "fg_color": "#364b60",
            "font_color": "white",
            "border": 1,
        })
        for c, name in enumerate(df.columns):
            ws.write(0, c, name, header)
            ws.set_column(c, c, max(len(name), 12))
    return buf.getvalue()


# ======================  static/style.css  ===============
/* Conteúdo resumido: junte aqui o CSS_unificado que você já tinha. */
css_unificado = """
/* =================== AJUSTES GERAIS =================== */
.stApp {
    padding-top: 1rem !important;  /* Espaçamento saudável no topo */
}

/* =================== BARRA LATERAL =================== */
[data-testid="stSidebar"]::before {
    content: ""; /* Elemento de conteúdo vazio para o pseudo-elemento */
    position: absolute; /* Posicionamento absoluto para cobrir toda a área */

    /* Posicionamento do elemento - controla onde o fundo começa */
    top: 0 !important; /* Distância do topo (0 = alinhado ao topo, valores maiores movem para baixo) - pode variar de 0 a qualquer valor positivo em px/rem */
    left: 0px;     /* Distância da esquerda (0 = alinhado à esquerda, valores maiores movem para direita) - pode variar de 0 a qualquer valor positivo em px/rem */

    /* Dimensões do elemento - controla o tamanho do fundo */
    width: 100%; /* Largura do elemento (100% = ocupa toda largura disponível) */
    height: 100%; /* Altura do elemento (100% = ocupa toda altura disponível) */

    background-color: #364b60; /* Cor de fundo azul escuro */
    z-index: 0 !important; /* Camada correta (valores negativos = atrás, positivos = na frente) */
    border-radius: 1px; /* Arredondamento dos cantos */
    margin: 0; /* Margem externa */
    padding: 0; /* Preenchimento interno */
}

[data-testid="stSidebar"] > div {
    position: relative;
    z-index: 1; /* Mantém o conteúdo acima do fundo */
    # padding: 2rem 1rem !important; /* Espaçamento interno adequado */
}

/* Define a cor do texto na barra lateral como branca */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stRadio span:not([role="radio"]) {
   color: white !important; /* Força a cor do texto como branca */
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

/* =================== TÍTULO PRINCIPAL =================== */
.stMarkdown h1:first-of-type {
    margin: 0 0 1.5rem 2rem !important; /* Alinhamento e espaçamento correto */
    color: #364b60;
    font-size: 2.2rem !important;
    padding: 0.25rem 0 !important;
}

/* =================== CONTEÚDO PRINCIPAL =================== */
.main-content {
    padding-left: 2rem;
    margin-top: -0.5rem !important;  /* Ajuste fino de alinhamento */
}

/* Espaço acima do primeiro elemento */
.stApp > div:first-child {
    padding-top: 0 !important;
    margin-top: -1rem !important;
}

/* =================== TABELAS =================== */
.custom-table {
    margin: 1.5rem 0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

/* =================== GRÁFICOS =================== */
.vega-embed {
    margin-top: 1rem !important;
    border-radius: 8px !important;
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
    padding: 0rem;
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
    padding: 0rem;
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

/* Estilo KPIs */
.kpi-container {
    background-color: #f9f9f9;
    border-radius: 5px;
    # padding: 15px;
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
    # padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
    color: #364b60;
}

/* Estilos para filtros de tabela */
.table-container {
    background-color: white;
    border-radius: 10px;
    # padding: 15px;
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
    # padding: 8px;
    background-color: #f0f7ff;
    border-radius: 5px;
    border-left: 3px solid #4c8bf5;
}
.warning-text {
    color: #dc3545;
    font-size: 14px;
    margin-top: 10px;
    # padding: 8px;
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

/* =================== RESPONSIVIDADE =================== */
@media screen and (max-width: 768px) {
    .metric-value {
        font-size: 1.5rem;
    }

    .metric-label {
        font-size: 0.8rem;
    }

    .stMarkdown h1:first-of-type {
        margin-left: 1rem !important;
        font-size: 1.8rem !important;
    }

    [data-testid="stSidebar"] {
        width: 100% !important;
        margin: 0 !important;
        padding: 0rem !important;
    }
}
"""

st.markdown(obter_estilo_css_container(PARAMETROS_ESTILO_CONTAINER), unsafe_allow_html=True)
st.markdown(f"<style>{css_unificado}</style>", unsafe_allow_html=True)
st.title(TITULO_DASHBOARD)

# ======================  main.py  ========================
import streamlit as st, pandas as pd, re, time, base64
from pathlib import Path
from utils import beautify, format_number_br
from data_io import load_parquets, df_to_csv, df_to_excel
from constantes import *  # rótulos e textos externos
from layout_primeiros_indicadores import (
    obter_estilo_css_container,
    PARAMETROS_ESTILO_CONTAINER,
    construir_grafico_linha_evolucao,
)

# ---------- Config inicial -----------------------------------------
st.set_page_config(page_title="Dashboard PNE", page_icon="📊", layout="wide")
CSS_PATH = Path("static/style.css")

st.markdown(obter_estilo_css_container(PARAMETROS_ESTILO_CONTAINER), unsafe_allow_html=True)
st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

# ---------- Dados ---------------------------------------------------
escolas_df, estado_df, municipio_df = load_parquets()

# ---------- Sidebar nível de agregação ------------------------------
tipo_nivel = st.sidebar.radio("Número de Matrículas por:", ["Escola", "Município", "Estado PE"])

df_map = {"Escola": escolas_df, "Município": municipio_df, "Estado PE": estado_df}
df = df_map[tipo_nivel].copy()
if df.empty:
    st.error(f"DataFrame vazio para {tipo_nivel}"); st.stop()

# ---------- Helpers de dicionário de etapas -------------------------
@st.cache_data
def ler_dict_etapas():
    import json, os
    path = "dicionario_das_etapas_de_ensino.json"
    if not os.path.exists(path):
        st.error("dicionario_das_etapas_de_ensino.json não encontrado"); st.stop()
    return json.loads(Path(path).read_text(encoding="utf-8"))

def padronizar_dict(df):
    base = ler_dict_etapas(); norm = {c.replace('\n','').lower():c for c in df.columns}
    def real(n):
        n0 = n.replace('\n','').lower(); return norm.get(n0, n)
    out = {}
    for etapa, cfg in base.items():
        out[etapa] = {
            "coluna_principal": real(cfg.get("coluna_principal", "")),
            "subetapas": {k: real(v) for k, v in cfg.get("subetapas", {}).items()},
            "series": {k: {s: real(c) for s, c in sd.items()} for k, sd in cfg.get("series", {}).items()},
        }
    return out

dict_etapas = padronizar_dict(df)
lista_etapas = list(dict_etapas.keys())

# ---------- Top‑bar de filtros --------------------------------------
TOPBAR_COLOR = "#364b60"
st.markdown(f"""
<style>
.top-bar {{background:{TOPBAR_COLOR};padding:0.5rem 1rem;border-radius:5px;
          margin:0.5rem 0 1rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap}}
.top-bar label {{color:#fff;font-size:0.8rem;font-weight:600;margin-bottom:2px}}
.top-bar .stSelectbox > div, .top-bar .stMultiSelect > div {{min-height:36px}}
</style>""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    c_ano, c_etapa, c_rede = st.columns([1.1, 1.8, 1.5], gap="small")

    with c_ano:
        st.markdown('<label>Ano(s)</label>', unsafe_allow_html=True)
        anos_disp = sorted(df["ANO"].unique(), reverse=True)
        anos = st.multiselect("", anos_disp, default=anos_disp,
                              key="anos", label_visibility="collapsed")

    with c_etapa:
        st.markdown('<label>Etapa / Subetapa</label>', unsafe_allow_html=True)
        etapa = st.selectbox("", lista_etapas, key="etapa",
                             label_visibility="collapsed")
        sub_opts = ["Todas"] + list(dict_etapas[etapa]["subetapas"].keys())
        sub   = st.selectbox("", sub_opts, key="subetapa",
                              label_visibility="collapsed")

    with c_rede:
        st.markdown('<label>Rede(s)</label>', unsafe_allow_html=True)
        redes = sorted(df["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())
        dep_sel = st.multiselect("", redes, default=redes,
                                 key="dep", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Aplica filtros aos dados --------------------------------
df_filt = df[df["ANO"].isin(anos)]
if dep_sel:
    df_filt = df_filt[df_filt["DEPENDENCIA ADMINISTRATIVA"].isin(dep_sel)]
else:
    st.warning("Nenhuma rede selecionada."); st.stop()

# --------- identifica coluna de matrículas --------------------------

def coluna_matriculas(et, sub, serie="Todas"):
    cfg = dict_etapas[et]
    if sub == "Todas":
        return cfg["coluna_principal"]
    if serie == "Todas":
        return cfg["subetapas"].get(sub, cfg["coluna_principal"])
    return cfg["series"].get(sub, {}).get(serie, cfg["coluna_principal"])

COL_MATR = coluna_matriculas(etapa, sub)
if COL_MATR not in df_filt.columns:
    st.error("Coluna de matrículas não encontrada"); st.stop()

df_filt = df_filt[pd.to_numeric(df_filt[COL_MATR], errors="coerce") > 0]
if df_filt.empty:
    st.error("Sem dados após filtros"); st.stop()

# ---------- Tabela paginada ----------------------------------------
PAGE_SZ = st.session_state.get("page_sz", 50)
TOT_PG   = max(1, -(-len(df_filt) // PAGE_SZ))
PG       = st.session_state.get("pg", 1)
PG       = max(1, min(PG, TOT_PG))
st.session_state["pg"] = PG

inicio = (PG-1)*PAGE_SZ
fim    = PG*PAGE_SZ
page_df = df_filt.iloc[inicio:fim].copy()

for c in page_df.columns:
    if c.startswith("Número de"):
        page_df[c] = page_df[c].apply(format_number_br)

st.dataframe(page_df.reset_index(drop=True), height=600,
             hide_index=True, use_container_width=True)

# ---------- Paginador ----------------------------------------------
a1, a2, a3 = st.columns(3)
with a1:
    if st.button("◀", disabled=PG==1):
        st.session_state.pg = PG-1; st.experimental_rerun()
with a2:
    st.markdown(f"**Página {PG}/{TOT_PG}**")
with a3:
    if st.button("▶", disabled=PG==TOT_PG):
        st.session_state.pg = PG+1; st.experimental_rerun()

# ---------- Downloads ----------------------------------------------
col_csv, col_xls = st.sidebar.columns(2)
with col_csv:
    st.download_button("CSV", df_to_csv(df_filt), "dados_filtrados.csv", mime="text/csv")
with col_xls:
    st.download_button("Excel", df_to_excel(df_filt), "dados_filtrados.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------- KPIs / gráfico demo (exemplo simples) -------------------
# → aqui você pode reusar seu bloco de KPIs/grafico se desejar

# ---------- Rodapé --------------------------------------------------
registro_fim = time.time()
st.caption(f"Tempo de processamento: {registro_fim - st.session_state.get('start', registro_fim):.2f}s")