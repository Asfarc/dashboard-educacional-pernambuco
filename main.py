# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import io, re, time
import base64, os
from pathlib import Path
import streamlit.components.v1 as components
import psutil
from datetime import datetime

# ─── 2. PAGE CONFIG (primeiro comando Streamlit!) ───────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 3. ESTILO GLOBAL ──────────────────────────────────────────────
CORES = {
    "primaria": "#6b8190", "secundaria": "#d53e4f", "terciaria": "#0073ba",
    "cinza_claro": "#ffffff", "cinza_medio": "#e0e0e0", "cinza_escuro": "#333333",
    "branco": "#ffffff", "preto": "#000000", "highlight": "#ffdfba",
    "botao_hover": "#fc4e2a", "selecionado": "#08306b",
    "sb_titulo": "#ffffff", "sb_subtitulo": "#ffffff", "sb_radio": "#ffffff",
    "sb_secao": "#ffffff", "sb_texto": "#ffffff", "sb_slider": "#ffffff",
}

CSS_COMPLETO = """
<style>
/* ─── RESET E VARIAVEIS ──────────────────────────────────────────── */
* {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --sb-bg: #6b8190;
    --radio-bg: #0073ba;
    --btn-hover: #fc4e2a;
}

/* ─── AJUSTES GERAIS DA SIDEBAR ───────────────────────────────────── */
/* Configurações da sidebar */
section[data-testid="stSidebar"] {
    min-width: 300px !important;
    width: 300px !important;      /* LARGURA DO SIDEBAR */
    background: linear-gradient(to bottom, #5a6e7e, #7b8e9e) !important;
}
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

/* ─── CONTEUDO PRINCIPAL ─────────────────────────────────────────── */
section.main .block-container {
    padding-top: 0.5rem !important;
}

div.panel-filtros {
    margin: -10px 0 !important;
    padding: 0 !important;
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
/* ─── COMPONENTES ────────────────────────────────────────────────── */
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
    margin: 0.2rem 0 !important;
    background: linear-gradient(to bottom, #0080cc, #0067a3) !important;
    border: 1px solid rgba(0, 0, 0, 0.3) !important;
    border-radius: 5px !important;
    transition: all 0.2s ease !important;
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

/* Efeito hover nos botões */
section[data-testid="stSidebar"] .stButton > button:hover,
section[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background: #444444 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    transition: all 0.2s ease !important;
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

/* Status de carregamento personalizado */
.stSpinner {
    text-align: center;
    padding: 10px;
}
.stSpinner > div {
    display: inline-block;
    width: 18px;
    height: 18px;
    margin-right: 8px;
    border: 3px solid #0073ba;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 1s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Botões de navegação */
.nav-button {
    background-color: #0073ba !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}
.nav-button:hover:not([disabled]) {
    background-color: #005d96 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
}
.nav-button:disabled {
    background-color: #cccccc !important;
    cursor: not-allowed !important;
}

/* Mensagens de alerta */
.stAlert {
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
}

/* Indicador de RAM */
.ram-indicator {
    background: rgba(0,0,0,0.2);
    border-radius: 4px;
    padding: 0.3rem 0.5rem;
    font-size: 0.85rem;
    color: white;
    display: inline-block;
    margin-top: 1rem;
}
</style>
"""

# Aplique o CSS completo uma única vez
st.markdown(CSS_COMPLETO, unsafe_allow_html=True)


# ─── 4. FUNÇÕES UTIL ────────────────────────────────────────────────
def beautify(col: str) -> str:
    """Formata o nome de uma coluna para exibição"""
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())


def beautify_column_header(col: str) -> str:
    """Formata o cabeçalho de uma coluna com abreviações conhecidas"""
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
    """Formata números no padrão brasileiro (1.234,56)"""
    if pd.isna(num):
        return "-"
    n = float(num)
    if n.is_integer():
        return f"{int(n):,}".replace(",", ".")
    inteiro, frac = str(f"{n:,.2f}").split('.')
    return f"{inteiro.replace(',', '.')},{frac}"


def format_number_br(num):
    """Formata inteiros no padrão brasileiro (1.234)"""
    try:
        return f"{int(num):,}".replace(",", ".")
    except:
        return str(num)


# ─── 4‑B. PAGINAÇÃO ────────────────────────────────────────────────
class Paginator:
    """Classe para gerenciar a paginação de DataFrames"""

    def __init__(self, total, page_size=25, current=1):
        # Limita o page_size a 10.000 se for maior
        self.page_size = min(page_size, 10000)
        self.total_pages = max(1, (total - 1) // self.page_size + 1)
        self.current = max(1, min(current, self.total_pages))
        self.start = (self.current - 1) * self.page_size
        self.end = min(self.start + self.page_size, total)

    def slice(self, df: pd.DataFrame) -> pd.DataFrame:
        """Retorna uma fatia do DataFrame correspondente à página atual"""
        return df.iloc[self.start:self.end]


# ─── 5. DEFINIÇÃO DE MODELO DE DADOS POR MODALIDADE ──────────────────────
class ModalidadeConfig:
    """Configuração por tipo de modalidade de ensino"""

    def __init__(self, arquivo, etapa_valores=None, subetapa_valores=None, serie_col=None, texto_ajuda=None):
        self.arquivo = arquivo
        self.etapa_valores = etapa_valores or {}  # valores de etapa para facilitar seleção padrão
        self.subetapa_valores = subetapa_valores or {}  # valores de subetapa específicos
        self.serie_col = serie_col  # nome da coluna de série, se existir
        self.texto_ajuda = texto_ajuda  # texto de ajuda contextual para esta modalidade


# ─── 6. CONFIGURAÇÕES DE MODALIDADE ────────────────────────────────────
MODALIDADES = {
    "Ensino Regular": ModalidadeConfig(
        arquivo="Ensino Regular.parquet",
        etapa_valores={
            "padrao": "Educação Infantil"  # valor padrão para seleção inicial
        },
        serie_col="Ano/Série",
        texto_ajuda="No Ensino Regular, selecione primeiro a Etapa (Infantil, Fundamental ou Médio), depois a Subetapa e, se desejar, uma Série específica."
    ),
    "EJA - Educação de Jovens e Adultos": ModalidadeConfig(
        arquivo="EJA - Educação de Jovens e Adultos.parquet",
        etapa_valores={
            "padrao": "EJA - Total",
            "totais": ["EJA - Total"]  # identifica valores que representam totais
        },
        texto_ajuda="Na modalidade EJA, selecione primeiro o tipo de ensino (EJA - Total, EJA - Ensino Fundamental ou EJA - Ensino Médio) e depois a subetapa específica, quando disponível."
    ),
    "Educação Profissional": ModalidadeConfig(
        arquivo="Educação Profissional.parquet",
        etapa_valores={
            "padrao": "Educação Profissional - Total",
            "totais": ["Educação Profissional - Total"]  # identifica valores que representam totais
        },
        texto_ajuda="Na Educação Profissional, selecione primeiro a Etapa (Educação Profissional - Total, Formação Inicial Continuada (FIC) ou Educação profissional técnica de nível médio) e depois a subetapa específica, quando disponível."
    )
}


# ─── 7. FUNÇÃO DE CARREGAMENTO PADRONIZADA ────────────────────────────
@st.cache_resource(show_spinner="⏳ Carregando dados…")
def carregar_dados(modalidade_key):
    """Carrega e normaliza os dados para a modalidade selecionada"""
    config = MODALIDADES[modalidade_key]
    caminho = config.arquivo

    try:
        df = pd.read_parquet(caminho, engine="pyarrow")
    except Exception as e:
        st.error(f"Erro ao carregar arquivo '{caminho}': {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    tempo_inicio = time.time()

    # Normalização comum a todas as modalidades
    for cod in ["Cód. Município", "Cód. da Escola"]:
        if cod in df.columns:
            df[cod] = (pd.to_numeric(df[cod], errors="coerce")
                       .astype("Int64").astype(str)
                       .replace("<NA>", ""))

    df["Ano"] = df["Ano"].astype(str)
    df["Número de Matrículas"] = pd.to_numeric(
        df["Número de Matrículas"], errors="coerce"
    )

    # Garantir que todas as colunas necessárias existam
    if "Etapa" not in df.columns:
        df["Etapa"] = ""

    if "Subetapa" not in df.columns:
        df["Subetapa"] = ""

    # Adicionar coluna de Série para modalidades que não a possuem
    if config.serie_col is None and "Série" not in df.columns:
        df["Série"] = ""
    elif config.serie_col is not None and config.serie_col in df.columns:
        # Renomear a coluna de série conforme configuração
        df["Série"] = df[config.serie_col]

    # Converter para categóricos para economia de memória
    for col in ["Etapa", "Subetapa", "Série", "Rede"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # Formato padrão para nível de agregação
    df["Nível de agregação"] = df["Nível de agregação"].str.lower()

    # Registra a métrica de tempo de carregamento
    tempo_carga = time.time() - tempo_inicio
    st.session_state["tempo_carga"] = tempo_carga

    # Retorna views
    return (
        df[df["Nível de agregação"].eq("escola")],
        df[df["Nível de agregação"].eq("município")],
        df[df["Nível de agregação"].eq("estado")],
    )


# ─── 8. CONSTRUÇÃO DOS FILTROS DINÂMICOS ─────────────────────────────
def construir_filtros_ui(df, modalidade_key, nivel):
    """Constrói os filtros de UI baseados na modalidade e dados disponíveis"""
    config = MODALIDADES[modalidade_key]

    # Layout em duas colunas
    c_left, c_right = st.columns([0.5, 0.7], gap="large")

    # Detectar modalidade para compatibilidade
    is_eja = modalidade_key == "EJA - Educação de Jovens e Adultos"
    is_prof = modalidade_key == "Educação Profissional"

    # Filtros comuns a todas as modalidades (coluna esquerda)
    with c_left:
        # Ano(s)
        st.markdown(
            '<div class="filter-title" '
            'style="margin:0;padding:0;display:flex;align-items:center;height:32px">'
            'Ano(s)</div>',
            unsafe_allow_html=True
        )
        anos_disp = sorted(df["Ano"].unique(), reverse=True)
        default_anos = [anos_disp[0]] if anos_disp else []
        anos_sel = st.multiselect(
            "Ano(s)",
            anos_disp,
            default=default_anos,
            key="ano_sel",
            label_visibility="collapsed"
        )

        # Rede(s)
        st.markdown(
            '<div class="filter-title" '
            'style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">'
            'Rede(s)</div>',
            unsafe_allow_html=True
        )
        redes_disp = sorted(df["Rede"].dropna().unique())
        default_redes = ["Pública e Privada"] if "Pública e Privada" in redes_disp else []
        redes_sel = st.multiselect(
            "Rede(s)",
            redes_disp,
            default=default_redes,
            key="rede_sel",
            label_visibility="collapsed"
        )

    # Filtros específicos por modalidade (coluna direita)
    with c_right:
        filtros = {}

        # Etapa
        st.markdown(
            '<div class="filter-title" '
            'style="margin:0;padding:0;display:flex;align-items:center;height:32px">'
            'Etapa</div>',
            unsafe_allow_html=True
        )

        # Recupera valores de Etapa e valor padrão
        etapas_disp = sorted(df["Etapa"].unique())
        padrao = config.etapa_valores.get("padrao", "")
        default_etapas = [padrao] if padrao in etapas_disp else [etapas_disp[0]] if etapas_disp else []

        etapa_sel = st.multiselect(
            "Etapa",
            etapas_disp,
            default=default_etapas,
            key="etapa_sel",
            label_visibility="collapsed"
        )
        filtros["etapa"] = etapa_sel

        # Subetapa - mostrar apenas se Etapa foi selecionada
        st.markdown(
            '<div class="filter-title" '
            'style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">'
            'Subetapa</div>',
            unsafe_allow_html=True
        )

        # Verificar se o valor selecionado de Etapa é um "Total"
        is_etapa_total = etapa_sel and etapa_sel[0] in config.etapa_valores.get("totais", [])

        if etapa_sel and not is_etapa_total:
            # CORREÇÃO AQUI: Evitar operações diretas com tipos categoria
            # Criar máscaras booleanas separadamente
            etapa_mask = df["Etapa"].isin(etapa_sel)
            notna_mask = df["Subetapa"].notna()

            # Para o filtro de "Total", usamos string methods que funcionam com categorias
            if "Subetapa" in df.columns and isinstance(df["Subetapa"].dtype, pd.CategoricalDtype):
                # Converter para string antes de usar str.contains
                total_mask = ~df["Subetapa"].astype(str).str.contains("Total", na=False)
            else:
                total_mask = ~df["Subetapa"].str.contains("Total", na=False)

            # Aplicar os filtros sequencialmente
            temp_df = df[etapa_mask]
            temp_df = temp_df[temp_df["Subetapa"].notna()]
            temp_df = temp_df[~temp_df["Subetapa"].astype(str).str.contains("Total", na=False)]

            sub_disp = sorted(temp_df["Subetapa"].unique())

            if sub_disp:
                sub_sel = st.multiselect(
                    "Subetapa",
                    sub_disp,
                    default=[],
                    key="sub_sel",
                    label_visibility="collapsed"
                )
            else:
                st.text("Nenhuma subetapa disponível para esta etapa.")
                sub_sel = []
        else:
            # Para etapas "Total" ou quando nenhuma etapa está selecionada
            if is_etapa_total:
                st.text(f"Nenhuma subetapa para {etapa_sel[0]}.")
            else:
                st.text("Selecione uma etapa primeiro.")
            sub_sel = []

        filtros["subetapa"] = sub_sel

        # Série - apenas para Ensino Regular e se subetapa foi selecionada
        if modalidade_key == "Ensino Regular" and etapa_sel and sub_sel:
            st.markdown(
                '<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">'
                'Série</div>',
                unsafe_allow_html=True
            )

            # CORREÇÃO AQUI: Evitar operações diretas com tipos categoria
            # Aplicamos os filtros sequencialmente
            temp_df = df[df["Etapa"].isin(etapa_sel)]
            temp_df = temp_df[temp_df["Subetapa"].isin(sub_sel)]
            temp_df = temp_df[temp_df["Série"].notna()]
            temp_df = temp_df[temp_df["Série"] != ""]

            serie_disp = sorted(temp_df["Série"].unique())

            if serie_disp:
                serie_sel = st.multiselect(
                    "Série",
                    serie_disp,
                    default=[],
                    key="serie_sel",
                    label_visibility="collapsed"
                )
            else:
                st.text("Nenhuma série disponível para esta subetapa.")
                serie_sel = []

            filtros["serie"] = serie_sel
        else:
            filtros["serie"] = []

    return anos_sel, redes_sel, filtros


# ─── 9. FUNÇÃO DE FILTRO UNIFICADA ─────────────────────────────────
def filtrar_dados(df, modalidade_key, anos, redes, filtros):
    """Filtra dados de forma unificada para qualquer modalidade"""
    config = MODALIDADES[modalidade_key]

    # Aplicamos os filtros sequencialmente em vez de usar operadores lógicos
    # diretamente com categorias
    result_df = df.copy()

    # Filtros básicos (comuns a todas as modalidades)
    result_df = result_df[result_df["Ano"].isin(anos)]

    if redes:
        result_df = result_df[result_df["Rede"].isin(redes)]

    # Etapa
    etapa_sel = filtros.get("etapa", [])
    if etapa_sel:
        result_df = result_df[result_df["Etapa"].isin(etapa_sel)]

        # Se não há subetapa selecionada, verificar se precisamos mostrar apenas totais
        if not filtros.get("subetapa") and modalidade_key == "Ensino Regular":
            # Para Ensino Regular, quando selecionamos apenas a Etapa sem Subetapa,
            # mostramos apenas as linhas com Subetapa = "Total"
            result_df = result_df[result_df["Subetapa"].astype(str).str.contains("Total", na=False)]

    # Subetapa
    subetapa_sel = filtros.get("subetapa", [])
    if subetapa_sel:
        result_df = result_df[result_df["Subetapa"].isin(subetapa_sel)]

    # Série - apenas para Ensino Regular
    serie_sel = filtros.get("serie", [])
    if serie_sel and modalidade_key == "Ensino Regular":
        result_df = result_df[result_df["Série"].isin(serie_sel)]

    return result_df

# ─── 10. INICIALIZAÇÃO E CARREGAMENTO ─────────────────────────────────
# Inicializa o cronômetro da sessão se não existir
if "tempo_inicio" not in st.session_state:
    st.session_state["tempo_inicio"] = time.time()

# ----- Seleção de modalidade e chamada protegida ---------------------
try:
    with st.sidebar:
        st.markdown(
            '<p style="color:#FFFFFF;font-weight:600;font-size:1.8rem;margin-top:0.5rem">'
            'Modalidade</p>', unsafe_allow_html=True
        )
        tipo_ensino = st.radio(
            "Selecione a modalidade",
            list(MODALIDADES.keys()),
            index=0,
            label_visibility="collapsed"
        )

    # Mostrar spinner personalizado enquanto carrega
    with st.spinner("Carregando dados..."):
        escolas_df, municipio_df, estado_df = carregar_dados(tipo_ensino)

    # Verificar se os DataFrames estão vazios
    if escolas_df.empty and municipio_df.empty and estado_df.empty:
        st.error(f"Não foi possível carregar os dados para '{tipo_ensino}'. Verifique se os arquivos parquet existem.")
        st.stop()

except Exception as e:
    st.error(f"Erro ao carregar '{tipo_ensino}': {str(e)}")
    st.stop()

# Uso de memória
ram_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2
st.sidebar.markdown(
    f'<div class="ram-indicator">💾 RAM usada: <b>{ram_mb:.0f} MB</b></div>',
    unsafe_allow_html=True
)

# ─── 11. SELEÇÃO DE NÍVEL DE AGREGAÇÃO ─────────────────────────────
st.sidebar.title("Filtros")
nivel = st.sidebar.radio(
    "Nível de Agregação",
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
    st.warning(f"Não há dados disponíveis para o nível de agregação '{nivel}'.")
    st.stop()

# ─── 12. PAINEL DE FILTROS DINÂMICOS ─────────────────────────────
with st.container():
    st.markdown('<div class="panel-filtros" style="margin-top:-30px">', unsafe_allow_html=True)

    # Construir a interface de filtros com base na modalidade
    anos_sel, redes_sel, filtros_especificos = construir_filtros_ui(
        df_base,
        tipo_ensino,
        nivel
    )

    # Fechar o painel de filtros
    st.markdown('</div>', unsafe_allow_html=True)

# ─── 13. VALIDAÇÃO E APLICAÇÃO DE FILTROS ─────────────────────────
# Verificação de filtros obrigatórios
if not anos_sel:
    st.warning("Por favor, selecione pelo menos um ano.")
    st.stop()

if not redes_sel:
    st.warning("Por favor, selecione pelo menos uma rede de ensino.")
    st.stop()

# Aplicar filtros unificados
df_filtrado = filtrar_dados(
    df_base,
    tipo_ensino,
    anos_sel,
    redes_sel,
    filtros_especificos
)

# Indicador visual de resultados
num_total = len(df_base)
num_filtrado = len(df_filtrado)

if num_filtrado > 0:
    percent = (num_filtrado / num_total) * 100
    st.markdown(
        f"<div style='margin-bottom:10px;'>"
        f"<span style='font-size:0.9rem;color:#666;'>"
        f"Exibindo <b>{format_number_br(num_filtrado)}</b> de "
        f"<b>{format_number_br(num_total)}</b> registros "
        f"(<b>{percent:.1f}%</b>)"
        f"</span></div>",
        unsafe_allow_html=True
    )
else:
    # Mensagens específicas por modalidade quando não há dados
    config = MODALIDADES[tipo_ensino]
    if config.texto_ajuda:
        st.warning(f"""
        Não há dados para esta combinação de filtros.

        {config.texto_ajuda}
        """)
    else:
        st.warning("Não há dados após os filtros aplicados. Por favor, ajuste os critérios de seleção.")
    st.stop()

# ─── 14. ALTURA DA TABELA (slider) ───────────────────────────────────────
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

    # Adicionando opção para definir o número de linhas por página
    options_paginacao = [10, 25, 50, 100, 250, 500, 10000]
    default_index = options_paginacao.index(10000) if 10000 in options_paginacao else 0


    def format_page_size(opt):
        return "Mostrar todos" if opt == 10000 else str(opt)


    page_size = st.selectbox(
        "Linhas por página",
        options=options_paginacao,
        index=default_index,
        format_func=format_page_size
    )

    st.session_state["page_size"] = page_size

# ─── 15. TABELA PERSONALIZADA COM FILTROS INTEGRADOS ────────────────
# 1. Colunas visíveis baseadas no nível de agregação
vis_cols = ["Ano"]
if nivel == "Escolas":
    vis_cols += ["Nome do Município", "Nome da Escola"]
elif nivel == "Municípios":
    vis_cols += ["Nome do Município"]

# 2. Escolhe qual coluna vai aparecer como "Etapa":
is_eja = tipo_ensino == "EJA - Educação de Jovens e Adultos"
is_prof = tipo_ensino == "Educação Profissional"

# Adicionamos a coluna Etapa sem renomear
vis_cols += ["Etapa"]

# Adicionamos a coluna Subetapa aqui
vis_cols += ["Subetapa"]

# Adiciona Rede e Matrículas
vis_cols += ["Rede", "Número de Matrículas"]

# 3. Puxa só as colunas selecionadas (não precisamos mais renomear Etapa)
df_tabela = df_filtrado[vis_cols].copy()

# Não é mais necessário renomear a coluna, pois estamos usando o nome original "Etapa"
# df_tabela = df_tabela.rename(columns={etapa_col: "Etapa"})

# 4. CSS para centralizar coluna numérica
st.markdown("""
<style>
/* Centraliza a coluna de matrículas */
[data-testid="stDataFrame"] table tbody tr td:last-child,
[data-testid="stDataFrame"] table thead tr th:last-child {
    text-align:center !important;
}

/* Destaca linhas ao passar o mouse */
[data-testid="stDataFrame"] table tbody tr:hover {
    background-color: rgba(107, 129, 144, 0.1) !important;
}

/* Bordas mais claras e estilo mais limpo */
[data-testid="stDataFrame"] table {
    border-collapse: collapse !important;
}

[data-testid="stDataFrame"] table th {
    background-color: #f0f0f0 !important;
    border-bottom: 2px solid #ddd !important;
    font-weight: 600 !important;
}

[data-testid="stDataFrame"] table td {
    border-bottom: 1px solid #eee !important;
}
</style>
""", unsafe_allow_html=True)

# 5. Cabeçalhos dos Filtros de texto
col_headers = st.columns(len(vis_cols))
for col, slot in zip(vis_cols, col_headers):
    with slot:
        # Use beautify_column_header em vez de beautify para os cabeçalhos
        header_name = beautify_column_header(col)

        extra = " style='text-align:center'" if col == "Número de Matrículas" else ""
        st.markdown(f"<div class='column-header'{extra}>{header_name}</div>",
                    unsafe_allow_html=True)

# 6. Filtros de coluna
col_filters = st.columns(len(vis_cols))
filter_values = {}
for col, slot in zip(vis_cols, col_filters):
    with slot:
        filter_values[col] = st.text_input(
            f"Filtro para {beautify_column_header(col)}",
            key=f"filter_{col}",
            label_visibility="collapsed",
            placeholder=f"Filtrar {beautify_column_header(col).lower()}..."
        )

# 7. Aplicação dos filtros de texto com feedback visual
mask = pd.Series(True, index=df_tabela.index)
filtros_ativos = False

for col, val in filter_values.items():
    if val.strip():
        filtros_ativos = True
        s = df_tabela[col]
        if col.startswith("Número de") or pd.api.types.is_numeric_dtype(s):
            v = val.replace(",", ".")
            if re.fullmatch(r"-?\d+(\.\d+)?", v):
                # Filtro exato para números
                mask &= s == float(v)
            else:
                # Filtro por texto em valores numéricos convertidos
                mask &= s.astype(str).str.contains(val, case=False)
        else:
            # Filtro por texto em colunas de texto
            mask &= s.astype(str).str.contains(val, case=False)

df_texto = df_tabela[mask]

# 8. Mostrar feedback de filtros ativos
if filtros_ativos:
    num_filtrados = len(df_texto)
    num_total = len(df_tabela)
    st.markdown(
        f"<div style='margin-top:-10px;margin-bottom:10px;'>"
        f"<span style='font-size:0.85rem;color:#666;background:#f5f5f5;padding:2px 8px;border-radius:4px;'>"
        f"Filtro de texto: <b>{format_number_br(num_filtrados)}</b> de "
        f"<b>{format_number_br(num_total)}</b> linhas"
        f"</span></div>",
        unsafe_allow_html=True
    )

# 9. Paginação
page_size = st.session_state.get("page_size", 10000)
pag = Paginator(len(df_texto), page_size=page_size,
                current=st.session_state.get("current_page", 1))
df_page = pag.slice(df_texto)

# 10. Formatação numérica
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

# 11. Configurar largura das colunas proporcionalmente
num_colunas = len(df_show.columns)
largura_base = 150  # Ajuste este valor conforme necessário
config_colunas = {
    col: {"width": f"{largura_base}px"} for col in df_show.columns
}

# Configuração especial para a coluna de matrículas (mais estreita)
col_matriculas = beautify_column_header("Número de Matrículas")
if col_matriculas in config_colunas:
    config_colunas[col_matriculas] = {"width": "120px"}

# 12. Exibir a tabela com todas as configurações
st.dataframe(
    df_show,
    column_config=config_colunas,
    height=altura_tabela,
    use_container_width=True,
    hide_index=True
)

# ─── 16. CONTROLES DE NAVEGAÇÃO ────────────────────────────────────
if pag.total_pages > 1:  # Só mostra controles se houver mais de uma página
    b1, b2, b3, b4 = st.columns([1, 1, 1, 2])

    with b1:
        if st.button("◀", disabled=pag.current == 1, key="prev_page",
                     help="Página anterior", use_container_width=True):
            st.session_state["current_page"] = pag.current - 1
            st.rerun()
    with b2:
        if st.button("▶", disabled=pag.current == pag.total_pages, key="next_page",
                     help="Próxima página", use_container_width=True):
            st.session_state["current_page"] = pag.current + 1
            st.rerun()

    with b3:
        # Opções de paginação com "Mostrar todos"
        page_options = [10, 25, 50, 100, 250, 500, 10000]


        # Função para formatar o rótulo
        def format_page_size(opt):
            return "Mostrar todos" if opt == 10000 else str(opt)


        new_ps = st.selectbox(
            "Itens por página",
            options=page_options,
            index=page_options.index(page_size),
            format_func=format_page_size,
            label_visibility="collapsed",
            key="page_size_select"
        )

        if new_ps != page_size:
            st.session_state["page_size"] = new_ps
            st.session_state["current_page"] = 1
            st.rerun()

    with b4:
        st.markdown(
            f"<div style='text-align:right;padding-top:8px;'>"
            f"<span style='font-weight:500;'>"
            f"Página {pag.current}/{pag.total_pages} · "
            f"{format_number_br(len(df_texto))} linhas</span></div>",
            unsafe_allow_html=True
        )
else:
    # Se houver apenas uma página, mostra apenas o total de linhas
    st.markdown(
        f"<div style='text-align:right;padding:8px 0;'>"
        f"<span style='font-weight:500;'>"
        f"Total: {format_number_br(len(df_texto))} linhas</span></div>",
        unsafe_allow_html=True
    )


# ─── 17. DOWNLOADS (on‑click) ───────────────────────────────────────
def gerar_csv():
    """Prepara os dados para download em formato CSV"""
    # Usar df_texto que já contém os dados filtrados
    try:
        csv_data = df_texto.to_csv(index=False).encode("utf-8")
        st.session_state["csv_bytes"] = csv_data
        st.session_state["download_pronto"] = True
        return csv_data
    except Exception as e:
        st.error(f"Erro ao gerar CSV: {str(e)}")
        return None


def gerar_xlsx():
    """Prepara os dados para download em formato Excel"""
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
            # Configura a planilha com formatação melhorada
            df_texto.to_excel(w, index=False, sheet_name="Dados")
            # Acessa a planilha para formatar
            worksheet = w.sheets["Dados"]
            # Formata os cabeçalhos
            header_format = w.book.add_format({
                'bold': True,
                'bg_color': '#FFDFBA',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            for col_num, value in enumerate(df_texto.columns.values):
                worksheet.write(0, col_num, value, header_format)
            # Ajusta largura das colunas
            for i, col in enumerate(df_texto.columns):
                max_len = max(
                    df_texto[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2  # adiciona um pouco de espaço
                worksheet.set_column(i, i, max_len)

        st.session_state["xlsx_bytes"] = buf.getvalue()
        st.session_state["download_pronto"] = True
        return buf.getvalue()
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {str(e)}")
        return None


# Adicionar um título para os botões de download
st.sidebar.markdown("### Download")

# Informação sobre os dados que serão baixados
num_linhas_download = len(df_texto)
st.sidebar.markdown(
    f"<div style='font-size:0.85rem;margin-bottom:8px;'>"
    f"Download de <b>{format_number_br(num_linhas_download)}</b> linhas"
    f"</div>",
    unsafe_allow_html=True
)

# Criar duas colunas na sidebar para os botões
col1, col2 = st.sidebar.columns(2)

# Colocar o botão CSV na primeira coluna
with col1:
    st.download_button(
        "Em CSV",
        data=gerar_csv() if "csv_bytes" not in st.session_state else st.session_state["csv_bytes"],
        key="csv_dl",
        mime="text/csv",
        file_name=f"dados_{datetime.now().strftime('%Y%m%d')}.csv",
        on_click=gerar_csv,
        disabled=len(df_texto) == 0
    )

# Colocar o botão Excel na segunda coluna
with col2:
    st.download_button(
        "Em Excel",
        data=io.BytesIO().getvalue() if "xlsx_bytes" not in st.session_state else st.session_state["xlsx_bytes"],
        key="xlsx_dl",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_name=f"dados_{datetime.now().strftime('%Y%m%d')}.xlsx",
        on_click=gerar_xlsx,
        disabled=len(df_texto) == 0
    )

# ─── 18. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")

# Layout de rodapé em colunas
footer_left, footer_right = st.columns([3, 1])

with footer_left:
    st.caption("© Dashboard Educacional – atualização: Mai 2025")

    # Informações de desempenho
    delta = time.time() - st.session_state.get("tempo_inicio", time.time())
    tempo_carga = st.session_state.get("tempo_carga", 0)

    st.caption(
        f"⏱️ Tempo de processamento: {delta:.2f}s (carga: {tempo_carga:.2f}s)"
    )

with footer_right:
    # Build info mais visível
    st.caption(f"Build: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

# Reinicia o timer para a próxima atualização
st.session_state["tempo_inicio"] = time.time()
# ====================================================================