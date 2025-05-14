# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import io, re, time, os, psutil
from pathlib import Path
from datetime import datetime
import pyarrow.parquet as pq

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

# ─── 7. FUNÇÃO DE CARREGAMENTO PADRONIZADA ─────────────────────────
@st.cache_resource(show_spinner="⏳ Carregando dados…")
def carregar_parquet_otimizado(arquivo: str, nivel: str | None = None) -> pd.DataFrame:
    """Lê Parquet com dtypes compactos, ignorando colunas ausentes."""

    # 1. schema do arquivo (rápido, não carrega dados)
    schema_cols = set(pq.read_schema(arquivo).names)

    base_cols = [
        "Nível de agregação", "Ano",
        "Cód. Município", "Nome do Município",
        "Cód. da Escola", "Nome da Escola",
        "Etapa", "Subetapa", "Rede",
        "Número de Matrículas",
    ]
    if "Ensino Regular" in arquivo:
        base_cols.append("Ano/Série")

    use_cols = [c for c in base_cols if c in schema_cols]

    # 2. dtypes só para as colunas que realmente existem
    dtype = {
        "Ano": "int16",
        "Cód. Município": "Int32",
        "Cód. da Escola": "Int64",
        "Número de Matrículas": "uint32",
    }
    dtype = {k: v for k, v in dtype.items() if k in use_cols}

    df = pd.read_parquet(arquivo, columns=use_cols, dtype=dtype, engine="pyarrow")

    # 3. textos → category (apenas se a coluna existe)
    for col in ["Nome do Município", "Nome da Escola",
                "Etapa", "Subetapa", "Rede", "Nível de agregação"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    if "Subetapa" in df.columns:
        df["Subetapa"] = df["Subetapa"].fillna("N/A").astype("category")

    return df[df["Nível de agregação"].eq(nivel)] if nivel else df



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
            st.text("Nenhuma subetapa disponível.")
            sub_sel = []

        filtros["subetapa"] = sub_sel

        # Série (somente Ensino Regular)
        if (modalidade_key == "Ensino Regular" and sub_sel
                and "Série" in df.columns
                and not any("Total" in s for s in sub_sel)):
            st.markdown('<div class="filter-title" style="margin-top:-12px;">Série</div>',
                        unsafe_allow_html=True)
            if "Série" in df.columns:
                serie_disp = sorted(
                    df.loc[
                        df["Etapa"].isin(etapa_sel) & df["Subetapa"].isin(sub_sel) & df["Série"].notna(),
                        "Série"
                    ].unique()
                )
            else:
                serie_disp = []
            serie_sel = st.multiselect(
                "Série", serie_disp,
                default=[], label_visibility="collapsed", key="serie_sel"
            )
            filtros["serie"] = serie_sel
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
            not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel) and  # CORREÇÃO AQUI
            subetapa_sel):
            result_df = result_df[result_df["Subetapa"].isin(subetapa_sel)]

    # ─── LÓGICA PARA DEMAIS MODALIDADES ────────────────────────────
    else:
        # Etapa
        etapa_sel = filtros.get("etapa", [])
        if etapa_sel:
            result_df = result_df[result_df["Etapa"].isin(etapa_sel)]
            is_etapa_total = any(e in config.etapa_valores.get("totais", []) for e in etapa_sel)  # CORREÇÃO AQUI

            # Lógica específica para Ensino Regular
            if modalidade_key == "Ensino Regular" and not is_etapa_total and not filtros.get("subetapa"):
                result_df = result_df[result_df["Subetapa"].astype(str).str.contains("Total", na=False)]

        # Subetapa (só aplicar se não for total)
        subetapa_sel = filtros.get("subetapa", [])
        if subetapa_sel and etapa_sel and not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel):  # CORREÇÃO AQUI
            result_df = result_df[result_df["Subetapa"].isin(subetapa_sel)]

        # Série - apenas para Ensino Regular e se não for total
        serie_sel = filtros.get("serie", [])
        if (
            serie_sel
            and modalidade_key == "Ensino Regular"
            and etapa_sel
            and not any(e in config.etapa_valores.get("totais", []) for e in etapa_sel)
            and not any("Total" in sub for sub in subetapa_sel)  # Nova verificação
        ):
            result_df = result_df[result_df["Série"].isin(serie_sel)]

    return result_df

# ─── 11. SELEÇÃO DE MODALIDADE / NÍVEL ─────────────────────────────
st.sidebar.title("Filtros")

tipo_ensino = st.radio(
    "Selecione a modalidade", list(MODALIDADES.keys()),
    index=0, label_visibility="collapsed"
)

nivel_ui = st.sidebar.radio(
    "Nível de Agregação",
    ["Escolas", "Municípios", "Pernambuco"],
    label_visibility="collapsed", key="nivel_sel"
)
nivel_map = {"Escolas": "escola",
             "Municípios": "município",
             "Pernambuco": "estado"}

ARQ = {k: v.arquivo for k, v in MODALIDADES.items()}

with st.spinner("Carregando dados…"):
    df_base = carregar_parquet_otimizado(
        ARQ[tipo_ensino], nivel=nivel_map[nivel_ui]
    )

if df_base.empty:
    st.warning(f"Não há dados para o nível '{nivel_ui}'.")
    st.stop()

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
    st.warning("Por favor, selecione pelo menos um ano."); st.stop()
if not redes_sel:
    st.warning("Por favor, selecione pelo menos uma rede."); st.stop()

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

    page_options = [10, 25, 50, 100, 250, 500, 10000]
    page_size = st.selectbox(
        "Linhas por página", page_options,
        index=page_options.index(10000),
        format_func=lambda x: "Mostrar todos" if x == 10000 else str(x)
    )
    st.session_state["page_size"] = page_size

    ram_mb = psutil.Process(os.getpid()).memory_info().rss / 1024**2
    st.sidebar.markdown(
        f'<div class="ram-indicator">💾 RAM usada: <b>{ram_mb:.0f} MB</b></div>',
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
    vis_cols.append(serie_col)
vis_cols += ["Rede", "Número de Matrículas"]

df_tabela = df_filtrado[vis_cols].copy()

# --- estilização rápida -------------------------------------------------
st.markdown("""<style>
[data-testid="stDataFrame"] tr:hover{background:rgba(107,129,144,.1)!important}
[data-testid="stDataFrame"] td:last-child,[data-testid="stDataFrame"] th:last-child{
 text-align:center!important}
.column-header{background:#daba93;text-align:center;font-weight:bold;
 height:40px;display:flex;align-items:center;justify-content:center;
 padding:5px;margin-bottom:4px}
</style>""", unsafe_allow_html=True)

# 5. Cabeçalhos e filtros alinhados --------------------------------------
col_headers = st.columns(len(vis_cols))
for col, slot in zip(vis_cols, col_headers):
    with slot:
        header = beautify_column_header(col)
        extra = " style='text-align:center'" if col == "Número de Matrículas" else ""
        st.markdown(f"<div class='column-header'{extra}>{header}</div>", unsafe_allow_html=True)

col_filters = st.columns(len(vis_cols))
filter_values = {}
for col, slot in zip(vis_cols, col_filters):
    with slot:
        filter_values[col] = st.text_input(
            "", key=f"filter_{col}",
            placeholder=f"Filtrar {beautify_column_header(col).lower()}...",
            label_visibility="collapsed"
        )

# 6. Aplicação dos filtros ----------------------------------------------
mask = pd.Series(True, index=df_tabela.index)
filtros_ativos = False

for col, val in filter_values.items():
    val = (val or "").strip()
    if val:
        filtros_ativos = True
        s = df_tabela[col]
        mask &= s.astype(str).str.contains(val, case=False)

df_texto = df_tabela[mask]

# 7. Feedback visual dos filtros ativos ----------------------------------
if filtros_ativos:
    st.markdown(
        f"<div style='margin-top:-8px;margin-bottom:8px;'>"
        f"<span style='font-size:0.85rem;color:#555;background:#f5f5f5;"
        f"padding:2px 8px;border-radius:4px'>"
        f"Filtro: <b>{format_number_br(len(df_texto))}</b> de "
        f"<b>{format_number_br(len(df_tabela))}</b> linhas</span></div>",
        unsafe_allow_html=True
    )
    st.session_state["current_page"] = 1  # volta para a 1ª página sempre que digita filtro


# Paginação
pag = Paginator(len(df_texto),
                page_size=st.session_state["page_size"],
                current=st.session_state.get("current_page",1))
df_page = pag.slice(df_texto)

# Exibição
st.dataframe(df_page, height=altura_tabela, use_container_width=True, hide_index=True)

# ─── 16. NAVEGAÇÃO DE PÁGINAS ──────────────────────────────────────
if pag.total_pages > 1:
    b1,b2,b3,b4 = st.columns([1,1,1,2])
    with b1:
        st.button("◀", disabled=pag.current==1, key="prev",
                  on_click=lambda: (st.session_state.update(current_page=pag.current-1), st.rerun()))
    with b2:
        st.button("▶", disabled=pag.current==pag.total_pages, key="next",
                  on_click=lambda: (st.session_state.update(current_page=pag.current+1), st.rerun()))
    with b4:
        st.markdown(f"<div style='text-align:right;padding-top:8px;'>"
                    f"Página {pag.current}/{pag.total_pages} · "
                    f"{format_number_br(len(df_texto))} linhas</div>",
                    unsafe_allow_html=True)

# ─── 17. DOWNLOADS (sob demanda) ───────────────────────────────────
def gerar_csv(df): return df.to_csv(index=False).encode("utf-8")
def gerar_xlsx(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Dados")
    return buf.getvalue()

st.sidebar.markdown("### Download")
st.sidebar.markdown(
    f"<div style='font-size:0.85rem;margin-bottom:8px;color:white;'>"
    f"Download de <b>{format_number_br(len(df_texto))}</b> linhas</div>",
    unsafe_allow_html=True
)

col1,col2 = st.sidebar.columns(2)
with col1:
    if st.button("CSV", disabled=df_texto.empty):
        st.download_button("Baixar CSV", gerar_csv(df_texto),
                           mime="text/csv",
                           file_name=f"dados_{datetime.now():%Y%m%d}.csv")
with col2:
    if st.button("Excel", disabled=df_texto.empty):
        st.download_button("Baixar Excel", gerar_xlsx(df_texto),
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           file_name=f"dados_{datetime.now():%Y%m%d}.xlsx")

# ─── 18. RODAPÉ ────────────────────────────────────────────────────
st.markdown("---")
left,right = st.columns([3,1])
with left:
    st.caption("© Dashboard Educacional – atualização: Mai 2025")
    delta = time.time() - st.session_state["tempo_inicio"]
    st.caption(f"⏱️ Processamento: {delta:.2f}s")
with right:
    st.caption(f"Build: {datetime.now():%Y-%m-%d %H:%M:%S} UTC")

st.session_state["tempo_inicio"] = time.time()
# ===================================================================