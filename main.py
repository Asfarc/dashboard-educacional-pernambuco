# =============================  main.py  =============================
# Dashboard • Matrículas (formato longo) – versão otimizada
# --------------------------------------------------------------------
#  ► Painel: Ano(s) | Etapa | Subetapa | Série | Rede(s)
#  ► Filtros em cascata (Etapa → Subetapa → Série)
#  ► DataFrame paginado + filtros por coluna
# --------------------------------------------------------------------

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

def css_global(c=CORES) -> str:
    return f"""
    <style>
    :root {{--sb-bg:{c['primaria']}; --radio-bg:{c['terciaria']}; --btn-hover:{c['botao_hover']};}}
    section[data-testid="stSidebar"]{{min-width:260px!important;width:260px!important;}}
    section[data-testid="stSidebar"]::before{{content:"";position:absolute;inset:0;background:{c['primaria']};z-index:0}}
    section[data-testid="stSidebar"]>div{{position:relative;z-index:1;padding:2rem 1rem}}
    .column-header{{background:{c['highlight']};text-align:center;font-weight:bold}}
    .stButton>button,.stDownloadButton>button{{background:{c['cinza_escuro']};color:{c['branco']};border:none;border-radius:3px}}
    .stButton>button:hover,.stDownloadButton>button:hover{{background:{c['botao_hover']}}}
    </style>
    """

st.markdown(css_global(), unsafe_allow_html=True)

# ─── 4. FUNÇÕES UTIL ────────────────────────────────────────────────
def beautify(col: str) -> str:
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
        self.page_size = page_size
        self.total_pages = max(1, (total - 1) // page_size + 1)
        self.current = max(1, min(current, self.total_pages))
        self.start = (self.current - 1) * page_size
        self.end = self.start + page_size

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
            '<p style="color:#FFFFFF;font-weight:600;font-size:1.1rem;margin-top:0.5rem">'
            'Modalidade:</p>', unsafe_allow_html=True
        )
        tipo_ensino = st.radio(
            "", list(MODALIDADES.keys()), index=0,
            label_visibility="collapsed"
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

# CSS COMBINED já com as correções
COMBINED_CSS = """
/* Estilo para os cabeçalhos das colunas */
.column-header {
    height: 50px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 5px !important;
    margin-bottom: 8px !important;
    text-align: center !important;
}

/* Estilo para os filtros de coluna */
[data-testid="stDataFrame"] + div [data-baseweb="input"] {
    height: 40px !important;
}

/* Certificando-se que o container dos filtros também tenha altura consistente */
[data-testid="stDataFrame"] + div [data-testid="column"] {
    min-height: 40px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
}

/* Input interno do filtro */
[data-testid="stDataFrame"] + div [data-baseweb="input"] input {
    height: 100% !important;
}

/* Diminuir o recuo do texto na sidebar */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
    padding-left: 0.5rem !important;
}

/* Ajustar os botões de download para evitar quebra de linha */
section[data-testid="stSidebar"] .stDownloadButton > button,
section[data-testid="stSidebar"] .stButton > button {
    white-space: nowrap;
    width: 100%;
    padding: 0.3rem 0.5rem;
    font-size: 0.9rem;
}

/* Mais espaço para a área dos botões de download */
section[data-testid="stSidebar"] h3 + div [data-testid="column"] {
    padding: 0 0.3rem;
}

/* Estilos gerais para a sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(to bottom, #5a6e7e, #7b8e9e) !important;
}

/* CORRIGIDO: Título principal da sidebar em BRANCO */
section[data-testid="stSidebar"] h1 {
    color: #FFFFFF !important;  /* Agora está branco */
    font-size: 1.8rem !important;
    margin-bottom: 1.2rem !important;
    border-bottom: 2px solid rgba(255, 255, 255, 0.3) !important;
    padding-bottom: 0.5rem !important;
}

/* Informação de RAM - movida para cima e estilizada */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p:has(svg) {
    position: absolute !important;
    top: 0.8rem !important;
    right: 1rem !important;
    font-size: 0.8rem !important;
    background-color: rgba(0, 0, 0, 0.2) !important;
    padding: 0.3rem 0.6rem !important;
    border-radius: 4px !important;
    margin: 0 !important;
}

/* CORRIGIDO: Título "Número de Matrículas por:" em BRANCO */
section[data-testid="stSidebar"] p[style*="color:#FFFFFF"] {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    margin: 1.2rem 0 0.8rem 0 !important;
    padding-left: 0.3rem !important;
    color: #FFFFFF !important;  /* Garantir que fique branco */
}

/* CORRIGIDO: Botões rádio uniformes com texto centralizado */
section[data-testid="stSidebar"] .stRadio > div > label {
    height: 3rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    margin: 0.4rem 0 !important;
    background: linear-gradient(to bottom, #0080cc, #0067a3) !important;
    border: 1px solid rgba(0, 0, 0, 0.3) !important;
    border-radius: 5px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    transition: all 0.2s ease !important;
    padding: 0 !important;  /* Remove padding interno para melhor centralização */
}

/* CORRIGIDO: Centralizar texto dentro das caixas azuis */
section[data-testid="stSidebar"] .stRadio > div > label > div {
    width: 100% !important;
    text-align: center !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

section[data-testid="stSidebar"] .stRadio > div > label p {
    margin: 0 !important;
    text-align: center !important;
    color: #FFFFFF !important;
}

/* Estilo para hover nos botões */
section[data-testid="stSidebar"] .stRadio > div > label:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    background: linear-gradient(to bottom, #0090e0, #0073b3) !important;
}

/* Estilo para botão selecionado */
section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: linear-gradient(to bottom, #005c99, #004b7d) !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2) !important;
    transform: translateY(0) !important;
    border: 1px solid rgba(0, 0, 0, 0.5) !important;
}

/* Configurações avançadas - estilo consistente */
section[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(0, 0, 0, 0.15) !important;
    border: 1px solid rgba(0, 0, 0, 0.3) !important;
    border-radius: 5px !important;
    margin: 1.5rem 0 !important;
}

section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    padding: 0.8rem 1rem !important;
    font-weight: 500 !important;
}

/* Estilo para a seção de Download */
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;  /* Download em branco também */
    font-size: 1.2rem !important;
    margin: 1.5rem 0 0.8rem 0 !important;
    padding-left: 0.3rem !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding-bottom: 0.4rem !important;
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
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    transition: all 0.2s ease !important;
    font-weight: 500 !important;
}

section[data-testid="stSidebar"] .stButton > button:hover,
section[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background: #555555 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

/* Espaçamento nas colunas dos botões de download */
section[data-testid="stSidebar"] h3 + div [data-testid="column"] {
    padding: 0 0.3rem !important;
}
"""

st.markdown(f"<style>{COMBINED_CSS}</style>", unsafe_allow_html=True)

# CORRIGIDO: Título "Número de Matrículas por:" após "Filtros"
st.sidebar.markdown(
    '<p style="color:#FFFFFF;font-weight:600;font-size:1.1rem;margin-top:1.2rem">'
    'Número de Matrículas por:</p>',
    unsafe_allow_html=True
)

# CORRIGIDO: Radio sem duplicação
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
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)

    # 1ª LINHA - Ajuste na proporção para o lado direito ter menos espaço
    c_left, c_right = st.columns([0.5, 0.7], gap="large")

    # Lado esquerdo permanece o mesmo
    with c_left:
        # Ano(s) - com espaço vertical mínimo
        st.markdown('<div class="filter-title" style="margin:0;padding:0;display:flex;align-items:center;height:32px">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df_base["Ano"].unique(), reverse=True)
        ano_sel = st.multiselect("Ano(s)", anos_disp, default=anos_disp,
                                 key="ano_sel", label_visibility="collapsed")

        # Rede(s) - com margem negativa para aproximar da caixa anterior
        st.markdown('<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">Rede(s)</div>',
                    unsafe_allow_html=True)
        redes_disp = sorted(df_base["Rede"].dropna().unique())
        rede_sel = st.multiselect("", redes_disp, default=redes_disp, key="rede_sel", label_visibility="collapsed")

    # Lado direito - Ajuste para posicionar Etapa mais à esquerda
    with c_right:
        # Use uma coluna com proporção menor para mover Etapa para a esquerda
        c_right_col1, c_right_col2 = st.columns([0.9, 1])  # Mais espaço para Etapa, menos espaço vazio

        with c_right_col1:
            # Etapa com mínimo de espaço vertical
            st.markdown('<div class="filter-title" style="margin:0;padding:0;display:flex;align-items:center;height:32px">Etapa</div>', unsafe_allow_html=True)
            etapas_disp = sorted(df_base["Etapa"].unique())
            etapa_sel = st.multiselect("", etapas_disp, default=[], key="etapa_sel", label_visibility="collapsed")

            # Para Subetapa
            if etapa_sel:
                st.markdown(
                    '<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">Subetapa</div>',
                    unsafe_allow_html=True)

                # Opções reais daquela(s) etapa(s)
                sub_real = sorted(df_base.loc[
                                      df_base["Etapa"].isin(etapa_sel) & df_base["Subetapa"].ne(""),
                                      "Subetapa"
                                  ].unique())

                # Um único "total" agregado, se houver seleção de etapa
                sub_disp = (["Total - Todas as Subetapas"] if etapa_sel else []) + sub_real

                sub_sel = st.multiselect("", sub_disp, default=[], key="sub_sel", label_visibility="collapsed")
            else:
                sub_sel = []

            # Para Séries - CORRIGIDA A INDENTAÇÃO DESTE BLOCO
            if etapa_sel and sub_sel:
                st.markdown(
                    '<div class="filter-title" style="margin-top:-12px;padding:0;display:flex;align-items:center;height:32px">Série</div>',
                    unsafe_allow_html=True)

                # Séries normais
                serie_real = sorted(df_base.loc[
                                        df_base["Etapa"].isin(etapa_sel) &
                                        df_base["Subetapa"].isin(
                                            [s for s in sub_sel if not s.startswith("Total")]) &
                                        df_base["Série"].ne(""),
                                        "Série"
                                    ].unique())

                # Se escolheu QUALQUER subetapa, sempre ofereça o "total"
                serie_disp = (["Total - Todas as Séries"] if sub_sel else []) + serie_real

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
    if etapas: m &= df["Etapa"].isin(etapas)

    # --- SUBETAPA -------------------------------------------------
    if subetapas:
        if "Total - Todas as Subetapas" in subetapas:
            pass  # já cobre tudo da etapa escolhida
        else:
            m &= df["Subetapa"].isin([s for s in subetapas if not s.startswith("Total")])

    # --- SÉRIE ----------------------------------------------------
    if series:
        if "Total - Todas as Séries" in series:
            pass  # já cobre todas as séries da subetapa
        else:
            m &= df["Série"].isin([s for s in series if not s.startswith("Total")])

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

# 1. Colunas visíveis
vis_cols = ["Ano", "Etapa", "Subetapa", "Série"]
if nivel == "Escola":
    vis_cols += ["Cód. da Escola", "Nome da Escola",
                 "Cód. Município", "Nome do Município", "Rede"]
elif nivel == "Município":
    vis_cols += ["Cód. Município", "Nome do Município", "Rede"]
else:
    vis_cols += ["Rede"]
vis_cols.append("Número de Matrículas")      # sempre por último

# 2. DataFrame base da tabela
df_tabela = df_filtrado[vis_cols]
if df_tabela.empty:
    st.warning("Não há dados para exibir."); st.stop()

# 3. CSS para centralizar coluna numérica
st.markdown("""
<style>
[data-testid="stDataFrame"] table tbody tr td:last-child,
[data-testid="stDataFrame"] table thead tr th:last-child {
    text-align:center !important;
}
</style>
""", unsafe_allow_html=True)

# 4. Cabeçalhos
col_headers = st.columns(len(vis_cols))
for col, slot in zip(vis_cols, col_headers):
    with slot:
        extra = " style='text-align:center'" if col == "Número de Matrículas" else ""
        st.markdown(f"<div class='column-header'{extra}>{beautify(col)}</div>",
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
page_size = st.session_state.get("page_size", 25)
pag       = Paginator(len(df_texto), page_size=page_size,
                      current=st.session_state.get("current_page", 1))
df_page   = pag.slice(df_texto)

# 7. Formatação numérica (sem warnings)
df_show = df_page.copy()
for c in df_show.filter(like="Número de").columns:
    df_show.loc[:, c] = df_show[c].apply(aplicar_padrao_numerico_brasileiro)

st.dataframe(df_show, height=altura_tabela, use_container_width=True,
             hide_index=True)

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
    new_ps = st.selectbox("Itens", [10, 25, 50, 100],
                          index=[10, 25, 50, 100].index(page_size),
                          label_visibility="collapsed")
    if new_ps != page_size:
        st.session_state["page_size"]   = new_ps
        st.session_state["current_page"] = 1
        st.rerun()

with b4:
    st.markdown(
        f"**Página {pag.current}/{pag.total_pages} · "
        f"{format_number_br(len(df_texto))} registros**"
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
