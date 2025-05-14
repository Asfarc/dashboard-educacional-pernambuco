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

css_path = Path(__file__).parent / "static" / "style.css"
st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)


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


# ─── 5. DEFINIÇÃO DE MODELO DE DADOS POR MODALIDADE ─────────────────
class ModalidadeConfig:
    """Configuração específica de cada modalidade"""

    def __init__(
            self, arquivo: str,
            etapa_valores: dict | None = None,
            subetapa_valores: dict | None = None,
            serie_col: str | None = None,
            texto_ajuda: str | None = None,
    ):
        self.arquivo = arquivo
        self.etapa_valores = etapa_valores or {}
        self.subetapa_valores = subetapa_valores or {}
        self.serie_col = serie_col
        self.texto_ajuda = texto_ajuda


# ─── 6. CONFIGURAÇÕES DE MODALIDADE ─────────────────────────────────
MODALIDADES: dict[str, ModalidadeConfig] = {
    "Ensino Regular": ModalidadeConfig(
        arquivo="Ensino Regular.parquet",
        etapa_valores={"padrao": "Educação Infantil"},
        serie_col="Ano/Série",
        texto_ajuda=(
            "No Ensino Regular, selecione primeiro a Etapa "
            "(Infantil, Fundamental ou Médio), depois a Subetapa "
            "e, se desejar, uma Série específica."
        ),
    ),
    "EJA - Educação de Jovens e Adultos": ModalidadeConfig(
        arquivo="EJA - Educação de Jovens e Adultos.parquet",
        etapa_valores={
            "padrao": "EJA - Total",
            "totais": [
                "EJA - Total",
                "EJA Ensino Fundamental - Total",
                "EJA Ensino Médio - Total",
            ],
        },
        subetapa_valores={
            "EJA Ensino Fundamental": [
                "EJA Anos Iniciais",
                "EJA Anos Finais",
                "EJA Ensino Fundamental - Curso FIC",
            ],
            "EJA Ensino Médio": [
                "EJA Ensino Médio - Sem componente profissionalizante",
                "EJA Ensino Médio - Curso FIC",
                "EJA Ensino Médio - Curso Técnico Integrado",
            ],
        },
        texto_ajuda=(
            "Selecione a Etapa (Total ou específica). "
            "Para etapas específicas, escolha a Subetapa."
        ),
    ),
    "Educação Profissional": ModalidadeConfig(
        arquivo="Educação Profissional.parquet",
        etapa_valores={
            "padrao": "Educação Profissional - Total",
            "totais": ["Educação Profissional - Total"],
        },
        texto_ajuda=(
            "Na Educação Profissional, selecione a Etapa "
            "(Total, FIC ou Técnico) e depois a Subetapa específica."
        ),
    ),
}

# Mapeamento comum (define apenas uma vez)
nivel_map = {
    "Escolas": "escola",
    "Municípios": "município",
    "Pernambuco": "estado"
}

# Mapeamento de modalidades para arquivos
ARQ = {k: v.arquivo for k, v in MODALIDADES.items()}


# ─── 7. FUNÇÃO DE CARREGAMENTO OTIMIZADA ─────────────────────────
@st.cache_resource(show_spinner="⏳ Carregando dados…")
def carregar_parquet_otimizado(arquivo: str, nivel: str | None = None) -> pd.DataFrame:
    """Lê o Parquet com dtypes compactos e retorna apenas o nível desejado."""
    try:
        # Definir colunas a carregar
        use_cols = [
            "Nível de agregação", "Ano",
            "Cód. Município", "Nome do Município",
            "Cód. da Escola", "Nome da Escola",
            "Etapa", "Subetapa", "Rede",
            "Número de Matrículas",
        ]

        # Adicionar coluna específica para Ensino Regular
        if "Ensino Regular" in arquivo:
            use_cols.append("Ano/Série")

        # Carregamento do Parquet - apenas com colunas selecionadas
        df = pd.read_parquet(
            arquivo,
            columns=use_cols,
            engine="pyarrow"
        )

        # Aplicar conversões de tipo após carregamento
        # Converter números para tipos menores
        if "Ano" in df.columns:
            df["Ano"] = pd.to_numeric(df["Ano"], downcast="integer")

        if "Número de Matrículas" in df.columns:
            df["Número de Matrículas"] = pd.to_numeric(
                df["Número de Matrículas"], downcast="unsigned"
            )

        if "Cód. Município" in df.columns:
            df["Cód. Município"] = pd.to_numeric(df["Cód. Município"], errors="coerce")

        if "Cód. da Escola" in df.columns:
            df["Cód. da Escola"] = pd.to_numeric(df["Cód. da Escola"], errors="coerce")

        # Tratamento de valores nulos em Subetapa ANTES de converter para category
        if "Subetapa" in df.columns:
            # Importante: preencher nulos antes de converter para category
            df["Subetapa"] = df["Subetapa"].fillna("N/A")

        # Converter texto para category para economizar mais RAM
        for col in ["Nome do Município", "Nome da Escola", "Etapa",
                    "Subetapa", "Rede", "Nível de agregação"]:
            if col in df.columns:
                df[col] = df[col].astype("category")

        # Converter Ano/Série para category no caso do Ensino Regular
        if "Ano/Série" in df.columns:
            # Tratar possíveis nulos antes de converter para category
            df["Ano/Série"] = df["Ano/Série"].fillna("N/A").astype("category")

        # Filtrar por nível se especificado
        return df[df["Nível de agregação"].eq(nivel)] if nivel else df

    except Exception as e:
        st.error(f"Erro ao carregar arquivo '{arquivo}': {str(e)}")
        return pd.DataFrame()


# ─── 8. CONSTRUÇÃO DOS FILTROS DINÂMICOS ───────────────────────────
def construir_filtros_ui(df: pd.DataFrame, modalidade_key: str, nivel_ui: str):
    """Cria filtros de ano, rede, etapa, etc., para a modalidade escolhida."""
    config = MODALIDADES[modalidade_key]

    # ---------- coluna esquerda (Ano / Rede) ----------
    c_left, c_right = st.columns([0.4, 0.8], gap="large")
    with c_left:
        # Ano(s)
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df["Ano"].unique(), reverse=True)
        anos_sel = st.multiselect(
            "Ano(s)", anos_disp,
            default=[anos_disp[0]] if anos_disp else [],
            label_visibility="collapsed", key="ano_sel"
        )

        # Rede(s)
        st.markdown('<div class="filter-title" style="margin-top:-12px;">Rede(s)</div>',
                    unsafe_allow_html=True)
        redes_disp = sorted(df["Rede"].dropna().unique())
        default_redes = ["Pública e Privada"] if "Pública e Privada" in redes_disp else []
        redes_sel = st.multiselect(
            "Rede(s)", redes_disp,
            default=default_redes,
            label_visibility="collapsed", key="rede_sel"
        )

    # ---------- coluna direita (Etapa / Subetapa / Série) ----------
    with c_right:
        filtros = {}

        # Etapa
        st.markdown('<div class="filter-title">Etapa</div>', unsafe_allow_html=True)
        etapas_disp = sorted(df["Etapa"].unique())
        padrao = config.etapa_valores.get("padrao", "")
        default_etapas = [padrao] if padrao in etapas_disp else etapas_disp[:1]

        etapa_sel = st.multiselect(
            "Etapa", etapas_disp,
            default=default_etapas,
            label_visibility="collapsed", key="etapa_sel"
        )
        filtros["etapa"] = etapa_sel

        # Subetapa
        st.markdown('<div class="filter-title" style="margin-top:-12px;">Subetapa</div>',
                    unsafe_allow_html=True)
        is_total = etapa_sel and etapa_sel[0] in config.etapa_valores.get("totais", [])

        if etapa_sel and not is_total:
            sub_disp = sorted(
                df.loc[df["Etapa"].isin(etapa_sel) & df["Subetapa"].notna(), "Subetapa"]
                .pipe(lambda s: s[~s.astype(str).str.contains("Total", na=False)])
                .unique()
            )
            sub_sel = st.multiselect(
                "Subetapa", sub_disp,
                default=[], label_visibility="collapsed", key="sub_sel"
            )
        else:
            st.text("Nenhuma subetapa disponível." if etapa_sel else "Selecione uma etapa primeiro.")
            sub_sel = []

        filtros["subetapa"] = sub_sel

        # Série (somente Ensino Regular)
        if modalidade_key == "Ensino Regular" and sub_sel and not any("Total" in s for s in sub_sel):
            st.markdown('<div class="filter-title" style="margin-top:-12px;">Série</div>',
                        unsafe_allow_html=True)

            # Verificar o nome correto da coluna de série
            serie_col = config.serie_col if config.serie_col in df.columns else "Série"

            if serie_col in df.columns:  # Verificar se a coluna existe
                serie_disp = sorted(
                    df.loc[
                        df["Etapa"].isin(etapa_sel) &
                        df["Subetapa"].isin(sub_sel) &
                        df[serie_col].notna(),
                        serie_col
                    ].unique()
                )
                serie_sel = st.multiselect(
                    "Série", serie_disp,
                    default=[], label_visibility="collapsed", key="serie_sel"
                )
                filtros["serie"] = serie_sel
            else:
                st.text(f"Coluna {serie_col} não encontrada nos dados.")
                filtros["serie"] = []
        else:
            filtros["serie"] = []

    return anos_sel, redes_sel, filtros


# ─── 9. FUNÇÃO DE FILTRO UNIFICADA ─────────────────────────────────
def filtrar_dados(df, modalidade_key, anos, redes, filtros):
    """Filtra dados de forma unificada para qualquer modalidade"""
    config = MODALIDADES[modalidade_key]

    # Aplicamos os filtros sequencialmente
    result_df = df.copy()

    # Filtros básicos (comuns a todas as modalidades)
    result_df = result_df[result_df["Ano"].isin(anos)]

    if redes:
        result_df = result_df[result_df["Rede"].isin(redes)]

    # ─── LÓGICA ESPECÍFICA PARA EJA ────────────────────────────────
    if modalidade_key == "EJA - Educação de Jovens e Adultos":
        etapa_sel = filtros.get("etapa", [])
        subetapa_sel = filtros.get("subetapa", [])

        # Aplica filtro de etapa
        if etapa_sel:
            result_df = result_df[result_df["Etapa"].isin(etapa_sel)]

        # Aplica subetapa apenas se não for total
        if (etapa_sel and
                not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel) and
                subetapa_sel):
            result_df = result_df[result_df["Subetapa"].isin(subetapa_sel)]

    # ─── LÓGICA PARA DEMAIS MODALIDADES ────────────────────────────
    else:
        # Etapa
        etapa_sel = filtros.get("etapa", [])
        if etapa_sel:
            result_df = result_df[result_df["Etapa"].isin(etapa_sel)]
            is_etapa_total = any(e in config.etapa_valores.get("totais", []) for e in etapa_sel)

            # Lógica específica para Ensino Regular
            if modalidade_key == "Ensino Regular" and not is_etapa_total and not filtros.get("subetapa"):
                result_df = result_df[result_df["Subetapa"].astype(str).str.contains("Total", na=False)]

        # Subetapa (só aplicar se não for total)
        subetapa_sel = filtros.get("subetapa", [])
        if subetapa_sel and etapa_sel and not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel):
            result_df = result_df[result_df["Subetapa"].isin(subetapa_sel)]

        # Série - apenas para Ensino Regular e se não for total
        serie_sel = filtros.get("serie", [])
        if (
                serie_sel
                and modalidade_key == "Ensino Regular"
                and etapa_sel
                and not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel)
                and not any("Total" in sub for sub in subetapa_sel)
        ):
            # Verificar o nome correto da coluna de série
            serie_col = config.serie_col if config.serie_col in result_df.columns else "Série"

            if serie_col in result_df.columns:  # Verificar se a coluna existe
                result_df = result_df[result_df[serie_col].isin(serie_sel)]

    return result_df


# ─── 10. INICIALIZAÇÃO E CARREGAMENTO ──────────────────────────────
if "tempo_inicio" not in st.session_state:
    st.session_state["tempo_inicio"] = time.time()

# ─── 11. SELEÇÃO DE MODALIDADE / NÍVEL ─────────────────────────────
with st.sidebar:
    st.sidebar.title("Modalidade")
    tipo_ensino = st.radio(
        "Selecione a modalidade",
        list(MODALIDADES.keys()),
        index=0,
        label_visibility="collapsed"
    )

    st.sidebar.title("Filtros")
    nivel_ui = st.radio(
        "Nível de Agregação",
        ["Escolas", "Municípios", "Pernambuco"],
        label_visibility="collapsed",
        key="nivel_sel"
    )

# Carregamento com spinner de progresso
with st.spinner("Carregando dados otimizados…"):
    # Medir RAM antes
    ram_antes = psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2

    # Carregar dados
    df_base = carregar_parquet_otimizado(
        ARQ[tipo_ensino],
        nivel=nivel_map[nivel_ui]
    )

    # Medir RAM depois
    ram_depois = psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2

if df_base.empty:
    st.warning(f"Não há dados disponíveis para o nível '{nivel_ui}'.")
    st.stop()

# Mostrar diagnóstico de memória
with st.sidebar:
    with st.expander("Diagnóstico de Memória", False):
        st.markdown(f"**Antes do carregamento**: {ram_antes:.1f} MB")
        st.markdown(f"**Após carregamento**: {ram_depois:.1f} MB")
        st.markdown(f"**Diferença**: {ram_depois - ram_antes:.1f} MB")
        st.markdown(f"**Registros carregados**: {format_number_br(len(df_base))}")

# ─── 12. PAINEL DE FILTROS DINÂMICOS ─────────────────────────────
with st.container():
    st.markdown(
        '<div class="panel-filtros" style="margin-top:-30px">',
        unsafe_allow_html=True
    )

    anos_sel, redes_sel, filtros_especificos = construir_filtros_ui(
        df_base, tipo_ensino, nivel_ui
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ─── 13. VALIDAÇÃO E FILTRAGEM ────────────────────────────────────
if not anos_sel:
    st.warning("Por favor, selecione pelo menos um ano.")
    st.stop()
if not redes_sel:
    st.warning("Por favor, selecione pelo menos uma rede.")
    st.stop()

df_filtrado = filtrar_dados(
    df_base, tipo_ensino, anos_sel, redes_sel, filtros_especificos
)

num_total, num_filtrado = len(df_base), len(df_filtrado)
if num_filtrado == 0:
    ajuda = MODALIDADES[tipo_ensino].texto_ajuda or ""
    st.warning("Não há dados para essa combinação de filtros.\n\n" + ajuda)
    st.stop()

percent = (num_filtrado / num_total) * 100
st.markdown(
    f"""<div class="stats-container">
        Exibindo <strong class="stats-count">{format_number_br(num_filtrado)}</strong>
        de <strong class="stats-total">{format_number_br(num_total)}</strong> registros
        (<span class="stats-percent">{percent:.1f}%</span>)
    </div>""", unsafe_allow_html=True
)

# ─── 14. CONFIGURAÇÕES (altura + linhas por página) ───────────────
with st.sidebar.expander("Configurações", False):
    st.markdown("""<style>
    [data-testid="stExpander"] [data-testid="stSlider"] > div:first-child,
    [data-testid="stExpander"] [data-testid="stSlider"] > div:nth-child(2){
        color:#FFFFFF!important;font-weight:500!important}
    </style>""", unsafe_allow_html=True)

    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

    page_size = st.selectbox(
        "Linhas por página", [10, 25, 50, 100, 250, 500, 10000],
        index=5, format_func=lambda x: "Mostrar todos" if x == 10000 else str(x)
    )
    st.session_state["page_size"] = page_size

    ram_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2
    st.sidebar.markdown(
        f'<div class="ram-indicator">💾 RAM usada: <b>{ram_mb:.0f} MB</b></div>',
        unsafe_allow_html=True
    )

# ─── 15. PREPARAÇÃO DA TABELA ──────────────────────────────────────
vis_cols = ["Ano"]
if nivel_ui == "Pernambuco":
    df_filtrado = df_filtrado.copy()
    df_filtrado["UF"] = "Pernambuco"
    vis_cols += ["UF"]
if nivel_ui == "Escolas":
    vis_cols += ["Nome do Município", "Nome da Escola"]
elif nivel_ui == "Municípios":
    vis_cols += ["Nome do Município"]

vis_cols += ["Etapa", "Subetapa"]
if tipo_ensino == "Ensino Regular":
    serie_col = MODALIDADES[tipo_ensino].serie_col or "Série"
    if serie_col in df_filtrado.columns:
        vis_cols.append(serie_col)
vis_cols += ["Rede", "Número de Matrículas"]

df_tabela = df_filtrado[vis_cols].copy()

# --- estilização da tabela ---
st.markdown("""<style>
[data-testid="stDataFrame"] table tbody tr td:last-child,
[data-testid="stDataFrame"] table thead tr th:last-child {
    text-align:center !important;
}
[data-testid="stDataFrame"] table tbody tr:hover {
    background-color: rgba(107, 129, 144, 0.1) !important;
}
</style>""", unsafe_allow_html=True)

# Cabeçalhos dos filtros em colunas
filter_cols = st.columns(len(vis_cols))
filter_values = {}

for i, col in enumerate(vis_cols):
    with filter_cols[i]:
        # Cabeçalho formatado
        header_name = beautify_column_header(col)
        extra = " style='text-align:center'" if col == "Número de Matrículas" else ""
        st.markdown(f"<div class='column-header'{extra}>{header_name}</div>",
                    unsafe_allow_html=True)

        # Campo de filtro
        filter_values[col] = st.text_input(
            f"Filtro para {header_name}",
            key=f"filter_{col}",
            label_visibility="collapsed",
            placeholder=f"Filtrar {header_name.lower()}..."
        )

# Aplicação dos filtros de texto
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

# Feedback visual para filtros ativos
if filtros_ativos:
    num_filtrados = len(df_texto)
    num_total = len(df_tabela)
    st.markdown(
        f"<div style='margin-top:-10px;margin-bottom:10px;'>"
        f"<span style='font-size:0.85rem;color:#666;background:#f5f5f5;padding:2px 8px;border-radius:4px;'>"
        f"Filtro: <b>{format_number_br(num_filtrados)}</b> de "
        f"<b>{format_number_br(num_total)}</b> linhas"
        f"</span></div>",
        unsafe_allow_html=True
    )

# Paginação
pag = Paginator(
    len(df_texto),
    page_size=st.session_state["page_size"],
    current=st.session_state.get("current_page", 1)
)
df_page = pag.slice(df_texto)

# Formatar colunas numéricas
df_show = df_page.copy()
colunas_numericas = df_show.filter(like="Número de").columns.tolist()
df_show.columns = [beautify_column_header(col) for col in df_show.columns]

for col in colunas_numericas:
    col_beautificada = beautify_column_header(col)
    if col_beautificada in df_show.columns:
        df_show[col_beautificada] = df_show[col_beautificada].apply(aplicar_padrao_numerico_brasileiro)

# Configuração de larguras de coluna
num_colunas = len(df_show.columns)
largura_base = 150
config_colunas = {
    col: {"width": f"{largura_base}px"} for col in df_show.columns
}

# Coluna de matrículas mais estreita
col_matriculas = beautify_column_header("Número de Matrículas")
if col_matriculas in config_colunas:
    config_colunas[col_matriculas] = {"width": "120px"}

# ─── PLACEHOLDER do somatório ──────────────────────────────────────
# (criado ANTES da tabela para que apareça acima dela)
soma_placeholder = st.empty()

# ─── TABELA PRINCIPAL ──────────────────────────────────────────────
event = st.dataframe(
    df_page,                          # ainda numérico, sem formatação
    height=altura_tabela,
    use_container_width=True,
    hide_index=True,
    selection_mode=["multi-row", "multi-column"],
    on_select="rerun",
    key="tabela_principal"
)

# ─── SOMA DOS ITENS SELECIONADOS ───────────────────────────────────
sel_rows = event.selection.rows
sel_cols = event.selection.columns

if sel_rows and sel_cols:
    sub  = df_page.iloc[sel_rows][sel_cols]
    soma = pd.to_numeric(sub.select_dtypes('number').stack()).sum()

    soma_placeholder.markdown(
        f"""
        <div style="
            text-align:right;                /* alinha à direita */
            margin-bottom:8px;               /* separa da tabela */
            background:#dff0d8;
            border:1px solid #3c763d;
            padding:12px 16px;
            border-radius:6px;
            font-size:1rem;">
            ➕ <b>Soma das células numéricas selecionadas:</b>
            {aplicar_padrao_numerico_brasileiro(soma)}
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # se nada estiver selecionado, esvazia o banner
    soma_placeholder.empty()


# ─── 16. NAVEGAÇÃO DE PÁGINAS ──────────────────────────────────────
if pag.total_pages > 1:
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
        # Opções de paginação
        page_options = [10, 25, 50, 100, 250, 500, 10000]
        new_ps = st.selectbox(
            "Itens por página",
            options=page_options,
            index=page_options.index(pag.page_size),
            format_func=lambda opt: "Mostrar todos" if opt == 10000 else str(opt),
            label_visibility="collapsed",
            key="page_size_select"
        )
        if new_ps != pag.page_size:
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
        f"""
        <div style="text-align: right; padding: 8px 0;">
            <span style="font-family: Arial, sans-serif; font-weight: 600;">Total:</span>
            <span>{format_number_br(len(df_texto))} linhas</span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ─── 17. DOWNLOADS (sob demanda) ───────────────────────────────────
def gerar_csv(df):
    """Prepara os dados para download em formato CSV"""
    return df.to_csv(index=False).encode("utf-8")


def gerar_xlsx(df):
    """Prepara os dados para download em formato Excel"""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Dados")
        worksheet = w.sheets["Dados"]
        header_format = w.book.add_format({
            'bold': True,
            'bg_color': '#FFDFBA',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        for i, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).apply(len).max(),
                len(str(col))
            ) + 2
            worksheet.set_column(i, i, max_len)
    return buf.getvalue()


# ------ SEÇÃO DE DOWNLOAD AJUSTADA ------
with st.sidebar:
    # Container para agrupar os elementos de download
    with st.container():
        st.markdown("### Download")

        # Texto informativo com margem aumentada
        st.markdown(
            f'<div class="download-info" style="margin-bottom:25px">'
            f'Download de <b>{format_number_br(len(df_texto))}</b> linhas</div>',
            unsafe_allow_html=True
        )

        # Botões em colunas com margem superior
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Em CSV", disabled=len(df_texto) == 0, key="csv_btn"):
                csv_data = gerar_csv(df_texto)
                st.download_button(
                    "Baixar CSV",
                    data=csv_data,
                    mime="text/csv",
                    file_name=f"dados_{datetime.now().strftime('%Y%m%d')}.csv",
                    key="csv_download"
                )
                del csv_data

        with col2:
            if st.button("Em Excel", disabled=len(df_texto) == 0, key="xlsx_btn"):
                xlsx_data = gerar_xlsx(df_texto)
                st.download_button(
                    "Baixar Excel",
                    data=xlsx_data,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    file_name=f"dados_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    key="xlsx_download"
                )
                del xlsx_data

# ─── 18. RODAPÉ ────────────────────────────────────────────────────
st.markdown("---")

# Layout de rodapé em colunas
footer_left, footer_right = st.columns([3, 1])

with footer_left:
    st.caption("© Dashboard Educacional – atualização: Mai 2025")

    # Informações de desempenho
    delta = time.time() - st.session_state.get("tempo_inicio", time.time())
    st.caption(f"⏱️ Tempo de processamento: {delta:.2f}s")

with footer_right:
    # Build info mais visível
    st.caption(f"Build: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

# Reinicia o timer para a próxima atualização
st.session_state["tempo_inicio"] = time.time()