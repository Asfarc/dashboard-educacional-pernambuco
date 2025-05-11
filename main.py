# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import altair as alt
import io, re, time
import base64, os
from pathlib import Path
import streamlit.components.v1 as components
import psutil

# ─── 2. PAGE CONFIG (primeiro comando Streamlit!) ───────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 3. ESTILO GLOBAL ──────────────────────────────────────────────
CORES = {
    "primaria":  "#6b8190", "secundaria":"#d53e4f", "terciaria": "#0073ba",
    "cinza_claro":"#ffffff","cinza_medio":"#e0e0e0","cinza_escuro":"#333333",
    "branco":"#ffffff","preto":"#000000","highlight":"#ffdfba",
    "botao_hover":"#fc4e2a","selecionado":"#08306b",
    "sb_titulo":"#ffffff","sb_subtitulo":"#ffffff","sb_radio":"#ffffff",
    "sb_secao":"#ffffff","sb_texto":"#ffffff","sb_slider":"#ffffff",
}

CSS_COMPLETO = """
<style>
/* Reset global para evitar texto vertical */
* {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
}

/* Variáveis de cor */
:root {
    --sb-bg: #6b8190;
    --radio-bg: #0073ba;
    --btn-hover: #fc4e2a;
}

/* ─── AJUSTES GERAIS DA SIDEBAR ───────────────────────────────────── */
/* Container principal da sidebar */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
    margin-top: -50px !important;  /* Compensa espaço residual */
}

/* Título "Modalidade" */
section[data-testid="stSidebar"] h1 {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Remove espaços em elementos internos */
section[data-testid="stSidebar"] .stRadio,
section[data-testid="stSidebar"] .stButton {
    margin-top: -20px !important;
}

/* ─── AJUSTES DO CONTEÚDO PRINCIPAL ──────────────────────────────── */
/* Container principal da página */
section.main .block-container {
    padding-top: 1rem !important;
}

/* Painel de filtros */
div.panel-filtros {
    margin-top: -30px !important;
}

/* Configurações da sidebar */
section[data-testid="stSidebar"] {
    min-width: 300px !important;
    width: 300px !important;      /* LARGURA DO SIDEBAR */
    background: linear-gradient(to bottom, #5a6e7e, #7b8e9e) !important;
}

section[data-testid="stSidebar"] > div {
    position: relative;
    z-index: 1;
    padding: 0rem 0rem !important;
}

/* Ajuste do container principal */
section.main .block-container {
    padding-top: 0.5rem !important;
}

/* Ajuste do painel de filtros */
div.panel-filtros {
    margin-top: -2rem !important;  # Compensa espaçamento residual
}

/* Ajuste dos títulos */
div.filter-title {
    margin: 0 !important;
    padding: 0 !important;
}

/* Forçar texto horizontal em TODOS os elementos da sidebar */
section[data-testid="stSidebar"] * {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    transform: none !important;
}

/* Título principal da sidebar */
section[data-testid="stSidebar"] h1 {
    color: #FFFFFF !important;
    font-size: 1.8rem !important;
    margin-bottom: 1.2rem !important;
    border-top: 2px solid #ffdfba !important;
    padding-bottom: 0.5rem !important;
}

/* Títulos secundários */
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-size: 1.5rem !important;
    margin: 1.5rem 0 0.8rem 0 !important;
    padding-left: 0.3rem !important;
    border-top: 2px solid #ffdfba !important;
    padding-bottom: 0.4rem !important;
}

/* Todos os parágrafos na sidebar */
section[data-testid="stSidebar"] p {
    color: #FFFFFF !important;
    writing-mode: horizontal-tb !important;
}

/* Radio buttons - container principal */
section[data-testid="stSidebar"] .stRadio > div {
    padding: 0;
    margin: 0;
}

/* Labels das opções */
section[data-testid="stSidebar"] .stRadio > div > label {
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    padding: 0.5rem 0.8rem !important;
    margin: 0.4rem 0 !important;
    background: linear-gradient(to bottom, #0080cc, #0067a3) !important;
    border: 1px solid rgba(0, 0, 0, 0.3) !important;
    border-radius: 5px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

/* ---------- [ESTILOS NOVOS] Destaque do item selecionado ---------- */
/* Label inteiro quando selecionado */
section[data-testid="stSidebar"] .stRadio > div > label:has(input[type="radio"]:checked) {
    background: #08306b !important;
    border: 2px solid #ffdfba !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
    transform: scale(1.02) !important;
}

/* Texto da opção selecionada */
section[data-testid="stSidebar"] .stRadio > div > label:has(input[type="radio"]:checked) p {
    font-weight: 600 !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
}

/* Bolinha interna mais vibrante */
section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + div:first-child::after {
    background: #ffdfba !important;
    box-shadow: 0 0 8px rgba(255,223,186,0.5) !important;
}

/* Esconde o input nativo */
section[data-testid="stSidebar"] .stRadio input[type="radio"] {
    opacity: 0 !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
}

/* Container customizado da bolinha */
section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
    position: relative !important;
    width: 20px !important;
    height: 20px !important;
    margin-right: 12px !important;
    flex-shrink: 0 !important;
}

/* Círculo externo */
section[data-testid="stSidebar"] .stRadio > div > label > div:first-child::before {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 18px;
    height: 18px;
    border: 2px solid #fff;
    border-radius: 50%;
    transition: all 0.2s ease;
}

/* Bolinha interna (selecionada) */
section[data-testid="stSidebar"] .stRadio > div > label > div:first-child::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    width: 10px;
    height: 10px;
    background: #ffdfba;
    border-radius: 50%;
    transition: transform 0.2s ease;
}

/* Estado selecionado - versão corrigida */
section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + div:first-child::before {
    border-color: #ffdfba !important;
}

section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + div:first-child::after {
    transform: translate(-50%, -50%) scale(1) !important;
}

/* Texto da opção */
section[data-testid="stSidebar"] .stRadio > div > label > div:last-child {
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    text-align: left !important;
    font-size: 0.9rem !important;
    white-space: normal !important;
    line-height: 1.3 !important;
}

/* Parágrafo interno */
section[data-testid="stSidebar"] .stRadio > div > label p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.4 !important;
    color: #FFFFFF !important;
}

/* Botões de download */
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] .stDownloadButton > button {
    height: 2.5rem !important;
    width: 100% !important;
    white-space: nowrap !important;
    background: #333333 !important;
    color: white !important;
    border: none !important;
    border-radius: 5px !important;
    font-weight: 500 !important;
}

/* Cabeçalhos das colunas */
.column-header {
    background: #ffdfba;
    text-align: center;
    font-weight: bold;
    height: 50px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 5px !important;
    margin-bottom: 8px !important;
}

/* Expander */
section[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(0, 0, 0, 0.15) !important;
    border: 1px solid rgba(0, 0, 0, 0.3) !important;
    border-radius: 5px !important;
    margin: 1.5rem 0 !important;
}
/* Ajustar padding da tabela: */

[data-testid="stDataFrame"] th, 
[data-testid="stDataFrame"] td {
    padding: 4px 8px !important;
}
/* Remove margem superior do container principal */
section.main .block-container {
    padding-top: 0 !important;
}

/* Ajusta o painel de filtros */
div.panel-filtros {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Ajusta títulos dos filtros */
div.filter-title {
    margin: 0 !important;
    padding: 0 !important;
}
</style>
"""

# Aplique o CSS completo uma única vez
st.markdown(CSS_COMPLETO, unsafe_allow_html=True)


# ─── 4. FUNÇÕES UTIL ────────────────────────────────────────────────
def beautify(col: str) -> str:

    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())


def beautify_column_header(col: str) -> str:
    abreviacoes = {
        "Número de Matrículas": "Matrículas",
        "Nome do Município": "Município",
        "Nome da Escola": "Escola",
        "Etapa de Ensino": "Etapa",
        "Cód. Município": "Cód. Mun.",
        "Cód. da Escola": "Cód. Esc.",
        "UF": "UF"
    }

    # Se a coluna está no dicionário, usar a abreviação
    if col in abreviacoes:
        return abreviacoes[col]

    # Caso contrário, usar o comportamento da beautify original
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())

def aplicar_padrao_numerico_brasileiro(num):
    if pd.isna(num): return "-"
    n = float(num)
    if n.is_integer(): return f"{int(n):,}".replace(",",".")
    inteiro, frac = str(f"{n:,.2f}").split('.')
    return f"{inteiro.replace(',', '.')},{frac}"
def format_number_br(num):
    try: return f"{int(num):,}".replace(",",".")
    except: return str(num)

# ─── 4‑B. PAGINAÇÃO ────────────────────────────────────────────────
class Paginator:
    def __init__(self, total, page_size=25, current=1):
        # Limita o page_size a 10.000 se for maior
        self.page_size = min(page_size, 10000)  # 🔥 Linha nova
        self.total_pages = max(1, (total - 1) // self.page_size + 1)
        self.current = max(1, min(current, self.total_pages))
        self.start = (self.current - 1) * self.page_size
        self.end = min(self.start + self.page_size, total)

    def slice(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.iloc[self.start:self.end]

# ─── 5. CARGA DO PARQUET ────────────────────────────────────────────
MODALIDADES = {
    "Ensino Regular":                     "Ensino Regular.parquet",
    "Educação Profissional":              "Educação Profissional.parquet",
    "EJA - Educação de Jovens e Adultos": "EJA - Educação de Jovens e Adultos.parquet",
}

@st.cache_resource(show_spinner="⏳ Carregando dados…")
def carregar_dados(modalidade: str):
    # Seleciona arquivo e carrega
    caminho = MODALIDADES[modalidade]
    df = pd.read_parquet(caminho, engine="pyarrow")

    # Normaliza códigos
    for cod in ["Cód. Município", "Cód. da Escola"]:
        if cod in df.columns:
            df[cod] = (pd.to_numeric(df[cod], errors="coerce")
                          .astype("Int64").astype(str)
                          .replace("<NA>", ""))

    # Converte ano e matrículas
    df["Ano"] = df["Ano"].astype(str)
    df["Número de Matrículas"] = pd.to_numeric(
        df["Número de Matrículas"], errors="coerce"
    )

    # Unifica colunas: Etapa / Subetapa / Série
    if "Etapa agregada" in df.columns:
        df["Etapa"] = df["Etapa agregada"].astype("category")
        df["Subetapa"] = (
            df["Nome da Etapa de ensino/Nome do painel de filtro"]
              .fillna("Total")
              .astype("category")
        )
        if "Ano/Série" in df.columns:
            df["Série"] = (
                df["Ano/Série"]
                  .fillna("")
                  .astype("category")
            )
        else:
            df["Série"] = pd.Categorical([""] * len(df), categories=[""])
    else:
        # esquema antigo
        def _split(s: str):
            p = s.split(" - ")
            etapa = p[0]
            sub   = p[1] if len(p) > 1 else ""
            serie = " - ".join(p[2:]) if len(p) > 2 else ""
            return etapa, sub, serie

        df[["Etapa", "Subetapa", "Série"]] = (
            df["Etapa de Ensino"]
              .apply(lambda x: pd.Series(_split(x)))
        )
        for c in ["Etapa", "Subetapa", "Série"]:
            df[c] = df[c].astype("category")

    # Comuns
    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    df["Rede"] = df["Rede"].astype("category")

    # Retorna views
    return (
        df[df["Nível de agregação"].eq("escola")],
        df[df["Nível de agregação"].eq("município")],
        df[df["Nível de agregação"].eq("estado")],
    )

# ----- seleção de modalidade e chamada protegida ---------------------
try:
    with st.sidebar:
        st.markdown(
            '<p style="color:#FFFFFF;font-weight:600;font-size:1.8rem;margin-top:0.5rem">'
            'Modalidade</p>', unsafe_allow_html=True
        )
        tipo_ensino = st.radio(
            "Selecione a modalidade",  # Label descritivo em vez de string vazia
            list(MODALIDADES.keys()),
            index=0,
            label_visibility="collapsed"  # Você ainda pode esconder visualmente
        )

    escolas_df, municipio_df, estado_df = carregar_dados(tipo_ensino)
except Exception as e:
    st.error(f"Erro ao carregar '{tipo_ensino}': {e}")
    st.stop()

# uso de memória
ram_mb=psutil.Process(os.getpid()).memory_info().rss/1024**2
st.sidebar.markdown(f"💾 RAM usada: **{ram_mb:.0f} MB**")

# ─── 6. SIDEBAR – nível de agregação ────────────────────────────────
st.sidebar.title("Filtros")
nivel = st.sidebar.radio(
    "",
    ["Escolas", "Municípios", "Pernambuco"],
    label_visibility="collapsed",
    key="nivel_sel"
)

# Selecionar o DataFrame baseado no nível
df_base = {
    "Escolas": escolas_df,
    "Municípios": municipio_df,
    "Pernambuco": estado_df
}[nivel]

if df_base.empty:
    st.error("DataFrame vazio")
    st.stop()

# ─── 7. PAINEL DE FILTROS ───────────────────────────────────────────
with st.container():
    st.markdown('<div class="panel-filtros" style="margin-top:-30px">', unsafe_allow_html=True)

    # 1ª LINHA - Ajuste na proporção para o lado direito ter menos espaço
    c_left, c_right = st.columns([0.5, 0.7], gap="large")

    # Lado esquerdo permanece o mesmo
    with c_left:
        # Ano(s) - com espaço vertical mínimo
        st.markdown('<div class="filter-title" style="margin:0;padding:0;display:flex;align-items:center;height:32px">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df_base["Ano"].unique(), reverse=True)
        default_anos = ["2024"] if "2024" in anos_disp else []
        ano_sel = st.multiselect("Ano(s)", anos_disp, default=default_anos,
                                 key="ano_sel", label_visibility="collapsed")

        # Rede(s) - com margem negativa para aproximar da caixa anterior
        st.markdown('<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">Rede(s)</div>',
                    unsafe_allow_html=True)
        redes_disp = sorted(df_base["Rede"].dropna().unique())
        default_redes = ["Pública e Privada"]  # 🔥 Valores exatos como estão no DataFrame
        rede_sel = st.multiselect("", redes_disp, default=default_redes, key="rede_sel", label_visibility="collapsed")

    # Lado direito - Ajuste para posicionar Etapa mais à esquerda
    with c_right:
        # Use uma coluna com proporção menor para mover Etapa para a esquerda
        c_right_col1, c_right_col2 = st.columns([0.9, 1])  # Mais espaço para Etapa, menos espaço vazio

        with c_right_col1:
            # Etapa com mínimo de espaço vertical
            st.markdown(
                '<div class="filter-title" style="margin:0;padding:0;display:flex;align-items:center;height:32px">Etapa</div>',
                unsafe_allow_html=True)
            etapas_disp = sorted(df_base["Etapa"].unique())

            # Definir padrão para Educação Infantil
            default_etapas = ["Educação Infantil"] if "Educação Infantil" in etapas_disp else []

            etapa_sel = st.multiselect(
                "",
                etapas_disp,
                default=default_etapas,  # 🔥 USAR A VARIÁVEL CRIADA
                key="etapa_sel",
                label_visibility="collapsed"
            )

            # Para Subetapa
            if etapa_sel:
                st.markdown(
                    '<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">Subetapa</div>',
                    unsafe_allow_html=True)

                # Opções reais daquela(s) etapa(s), excluindo "Total"
                sub_real = sorted(df_base.loc[
                                      df_base["Etapa"].isin(etapa_sel) &
                                      df_base["Subetapa"].ne("") &
                                      df_base["Subetapa"].ne("Total"),  # Exclui "Total"
                                      "Subetapa"
                                  ].unique())

                # Um único "total" agregado, se houver seleção de etapa
                sub_disp = (["Total - Todas as Subetapas"] if etapa_sel else []) + sub_real

                sub_sel = st.multiselect("", sub_disp, default=[], key="sub_sel", label_visibility="collapsed")
            else:
                sub_sel = []

            # Para Séries
            if etapa_sel and sub_sel:
                st.markdown(
                    '<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">Série</div>',
                    unsafe_allow_html=True)

                # Se "Total - Todas as Subetapas" foi selecionado
                if "Total - Todas as Subetapas" in sub_sel:
                    # Não mostra opções de série quando Total está selecionado
                    serie_sel = []
                else:
                    # Séries específicas das subetapas selecionadas, EXCLUINDO os totais
                    serie_real = sorted(df_base.loc[
                                            df_base["Etapa"].isin(etapa_sel) &
                                            df_base["Subetapa"].isin(sub_sel) &
                                            df_base["Série"].ne("") &
                                            ~df_base["Série"].str.startswith("Total -", na=False),  # Exclui totais
                                            "Série"
                                        ].unique())

                    # Adiciona "Total - Todas as Séries" apenas se houver séries específicas
                    serie_disp = ["Total - Todas as Séries"] + serie_real if serie_real else []

                    serie_sel = st.multiselect("", serie_disp, default=[], key="serie_sel",
                                               label_visibility="collapsed")
            else:
                serie_sel = []

    # CORRIGIDO: fechamento do container deve estar fora do bloco c_right_col1
    st.markdown('</div>', unsafe_allow_html=True)  # fecha .panel-filtros

# ─── 8. FUNÇÃO DE FILTRO (sem cache) ────────────────────────────────
# Função de filtro simplificada
def filtrar(df, anos, redes, etapas, subetapas, series):
    m = df["Ano"].isin(anos)
    if redes: m &= df["Rede"].isin(redes)

    if etapas:
        m &= df["Etapa"].isin(etapas)

        # Se uma etapa foi selecionada mas nenhuma subetapa específica
        if not subetapas:
            m &= df["Subetapa"] == "Total"

    # --- SUBETAPA -------------------------------------------------
    if subetapas:
        if "Total - Todas as Subetapas" in subetapas:
            m &= df["Subetapa"] == "Total"
        else:
            m &= df["Subetapa"].isin(subetapas)

    # --- SÉRIE ----------------------------------------------------
    if series:
        if "Total - Todas as Séries" in series:
            # Quando "Total - Todas as Séries" é selecionado com subetapas específicas
            # Mostra o total daquela subetapa específica
            if subetapas and "Total - Todas as Subetapas" not in subetapas:
                # Para cada subetapa selecionada, mostra seu total
                serie_totals = [f"Total - {sub}" for sub in subetapas]
                m &= df["Série"].isin(serie_totals)
            else:
                # Se não há subetapa específica, mostra série vazia ou totais gerais
                m &= df["Série"].eq("")
        else:
            m &= df["Série"].isin(series)

    return df.loc[m]

# 7‑B • CHAMA O FILTRO COM AS ESCOLHAS ATUAIS • gera df_filtrado
df_filtrado = filtrar(
    df_base,
    tuple(ano_sel),
    tuple(rede_sel),
    tuple(etapa_sel),
    tuple(sub_sel),
    tuple(serie_sel),
)

# se não houver linhas depois do filtro, pare logo aqui
if df_filtrado.empty:
    st.warning("Não há dados após os filtros."); st.stop()

# ─── 9. ALTURA DA TABELA (slider) ───────────────────────────────────────
with st.sidebar.expander("Configurações avançadas da tabela", False):
    # Adicionar um estilo personalizado para o texto do slider
    st.markdown("""
    <style>
    /* Seletor mais específico para o texto do slider */
    [data-testid="stExpander"] [data-testid="stSlider"] > div:first-child {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

# ─── 10. TABELA PERSONALIZADA COM FILTROS INTEGRADOS ────────────────

# 1. Colunas visíveis baseadas no nível de agregação
vis_cols = ["Ano"]

if nivel == "Escolas":
    vis_cols += ["Nome do Município", "Nome da Escola"]
elif nivel == "Municípios":
    vis_cols += ["Nome do Município"]

# Adiciona colunas comuns
vis_cols += ["Etapa de Ensino", "Rede", "Número de Matrículas"]

# 2. DataFrame base da tabela
df_tabela = df_filtrado[vis_cols].copy()

# --- Adicionar coluna UF apenas para Pernambuco ---
if nivel == "Pernambuco":
    # 1. Adiciona a coluna "UF" ao DataFrame
    df_tabela["UF"] = "Pernambuco"

    # 2. Atualiza a lista vis_cols ANTES de reordenar o DataFrame
    vis_cols.insert(1, "UF")  # Posição 1 (segunda coluna)

    # 3. Reordena as colunas do DataFrame conforme a nova vis_cols
    df_tabela = df_tabela[vis_cols]  # 🔥 Linha crucial!

if df_tabela.empty:
    st.warning("Não há dados para exibir.")
    st.stop()

# 3. CSS para centralizar coluna numérica
st.markdown("""
<style>
[data-testid="stDataFrame"] table tbody tr td:last-child,
[data-testid="stDataFrame"] table thead tr th:last-child {
    text-align:center !important;
}
</style>
""", unsafe_allow_html=True)

# 4. Cabeçalhos dos Filtros de texto
col_headers = st.columns(len(vis_cols))
for col, slot in zip(vis_cols, col_headers):
    with slot:
        # Use beautify_column_header em vez de beautify para os cabeçalhos
        header_name = beautify_column_header(col)

        extra = " style='text-align:center'" if col == "Número de Matrículas" else ""
        st.markdown(f"<div class='column-header'{extra}>{header_name}</div>",
                    unsafe_allow_html=True)

# 5. Filtros de coluna
col_filters = st.columns(len(vis_cols))
filter_values = {}
for col, slot in zip(vis_cols, col_filters):
    with slot:
        filter_values[col] = st.text_input("Filtro",
                                           key=f"filter_{col}",
                                           label_visibility="collapsed")

mask = pd.Series(True, index=df_tabela.index)
for col, val in filter_values.items():
    if val.strip():
        s = df_tabela[col]
        if col.startswith("Número de") or pd.api.types.is_numeric_dtype(s):
            v = val.replace(",", ".")
            if re.fullmatch(r"-?\d+(\.\d+)?", v):
                mask &= s == float(v)
            else:
                mask &= s.astype(str).str.contains(val, case=False)
        else:
            mask &= s.astype(str).str.contains(val, case=False)

df_texto = df_tabela[mask]

# 6. Paginação -------------------------------------------------------
page_size = st.session_state.get("page_size", 10000)
pag       = Paginator(len(df_texto), page_size=page_size,
                      current=st.session_state.get("current_page", 1))
df_page   = pag.slice(df_texto)

# 7. Formatação numérica (sem warnings)
df_show = df_page.copy()

# Identificar colunas numéricas antes de renomear
colunas_numericas = df_show.filter(like="Número de").columns.tolist()

# Renomear as colunas para os cabeçalhos beautificados
df_show.columns = [beautify_column_header(col) for col in df_show.columns]

# Aplicar formatação às colunas numéricas renomeadas
for col in colunas_numericas:
    col_beautificada = beautify_column_header(col)
    if col_beautificada in df_show.columns:
        df_show[col_beautificada] = df_show[col_beautificada].apply(aplicar_padrao_numerico_brasileiro)

# Configurar largura das colunas proporcionalmente
num_colunas = len(df_show.columns)
largura_base = 150  # Ajuste este valor conforme necessário
config_colunas = {
    col: {"width": f"{largura_base}px"} for col in df_show.columns
}

st.dataframe(
    df_show,
    column_config=config_colunas,
    height=altura_tabela,
    use_container_width=True,  # 🔥 Garante que a tabela use toda a largura
    hide_index=True
)

# 8. Controles de navegação ------------------------------------------
b1, b2, b3, b4 = st.columns([1, 1, 1, 2])

with b1:
    if st.button("◀", disabled=pag.current == 1):
        st.session_state["current_page"] = pag.current - 1
        st.rerun()

with b2:
    if st.button("▶", disabled=pag.current == pag.total_pages):
        st.session_state["current_page"] = pag.current + 1
        st.rerun()

with b3:
    # Opções de paginação com "Mostrar todos"
    page_options = [10, 25, 50, 100, 10000]  # 🔥 10000 = Mostrar todos

    # Função para formatar o rótulo
    def format_page_size(opt):
        return "Mostrar todos" if opt == 10000 else str(opt)

    new_ps = st.selectbox(
        "Itens",
        options=page_options,
        index=page_options.index(10000),  # 🔥 Define "Mostrar todos" como padrão
        format_func=format_page_size,
        label_visibility="collapsed"
    )

    if new_ps != page_size:
        st.session_state["page_size"] = new_ps
        st.session_state["current_page"] = 1
        st.rerun()

with b4:
    st.markdown(
        f"**Página {pag.current}/{pag.total_pages} · "
        f"{format_number_br(len(df_texto))} linhas**"
    )

# ─── 11. DOWNLOADS (on‑click) ───────────────────────────────────────
def gerar_csv():
    # Usar df_texto que já contém os dados filtrados
    st.session_state["csv_bytes"] = df_texto.to_csv(index=False).encode("utf-8")

def gerar_xlsx():
    # Usar df_texto que já contém os dados filtrados
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df_texto.to_excel(w, index=False, sheet_name="Dados")
    st.session_state["xlsx_bytes"] = buf.getvalue()

# Adicionar um título para os botões de download
st.sidebar.markdown("### Download")

# Criar duas colunas na sidebar para os botões
col1, col2 = st.sidebar.columns(2)

# Colocar o botão CSV na primeira coluna
with col1:
    st.download_button(
        "Em CSV",
        data=df_texto.to_csv(index=False).encode("utf-8"),
        key="csv_dl",
        mime="text/csv",
        file_name="dados.csv",
        on_click=gerar_csv
    )

# Colocar o botão Excel na segunda coluna
with col2:
    st.download_button(
        "Em Excel",
        data=io.BytesIO().getvalue() if "xlsx_bytes" not in st.session_state else st.session_state["xlsx_bytes"],
        key="xlsx_dl",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_name="dados.xlsx",
        on_click=gerar_xlsx
    )

# ─── 12. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
delta = time.time() - st.session_state.get("tempo_inicio", time.time())
st.caption(f"Tempo de processamento: {delta:.2f}s")
st.session_state["tempo_inicio"] = time.time()
# ====================================================================
from datetime import datetime
st.caption(f"Build: {datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC")
