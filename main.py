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

# ─── 2. PAGE CONFIG (primeiro comando Streamlit!) ───────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 3. CONFIG GLOBALS (Altair + CSS helpers) ───────────────────────
alt.renderers.set_embed_options({
    "formatLocale": {"decimal": ",", "thousands": ".", "grouping": [3]},
})

PARAMETROS_ESTILO_CONTAINER = {
    "raio_borda": 8,
    "cor_borda": "#dee2e6",
    "cor_titulo": "#364b60",
    "tamanho_fonte_titulo": "1.1rem",
    "tamanho_fonte_conteudo": "1rem",
    "cor_fonte_conteudo": "#364b60",
}

def obter_estilo_css_container(p=PARAMETROS_ESTILO_CONTAINER) -> str:
    return f"""
    <style>
    .container-custom{{padding:0!important;margin:0!important;background:transparent!important}}
    .container-title{{font-size:{p['tamanho_fonte_titulo']};color:{p['cor_titulo']}}}
    .container-text {{font-size:{p['tamanho_fonte_conteudo']};color:{p['cor_fonte_conteudo']}}}
    </style>
    """

CSS_IN_LINE = """
/* ===== PAINEL DE FILTROS ========================================== */
.panel-filtros{
    background:#eef2f7;border:1px solid #dce6f3;border-radius:6px;
    padding:0.7rem 1rem 1rem;margin-bottom:1.1rem;
}
.panel-row{display:flex;flex-wrap:nowrap;gap:0.8rem}      /* NOVO  */
.panel-row>div{flex:1 1 0}

.filter-title{
    font-weight:600;color:#364b60;font-size:0.90rem;margin:0 0 0.15rem /* ↓ */
}

/* ===== SIDEBAR ===================================================== */
[data-testid="stSidebar"]{width:260px!important;min-width:260px!important}
[data-testid="stSidebar"]::before{
    content:"";position:absolute;top:0;left:0;width:100%;height:100%;
    background:#364b60;border-radius:1px;z-index:0}
[data-testid="stSidebar"]>div{position:relative;z-index:1;padding:2rem 1rem!important}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stRadio span:not([role=radio]){color:#fff!important}
[data-testid="stSidebar"] option,[data-testid="stSidebar"] select,
[data-testid="stSidebar"] [data-baseweb=select] div{color:#000!important}
[data-testid="stSidebar"] .stMultiSelect [aria-selected=true]{
    background:#e37777!important;color:#fff!important;border-radius:1px!important}

/* ===== BOTÕES ====================================================== */
.stButton>button,.stDownloadButton>button{
    background:#364b60!important;color:#fff!important;border:none!important;
    border-radius:3px!important;transition:all .3s}
.stButton>button:hover,.stDownloadButton>button:hover{
    background:#25344d!important;transform:translateY(-1px);
    box-shadow:0 2px 5px rgba(0,0,0,.1)}
"""

st.markdown(obter_estilo_css_container(), unsafe_allow_html=True)
st.markdown(f"<style>{CSS_IN_LINE}</style>", unsafe_allow_html=True)

# ─── 4. FUNÇÕES UTIL ────────────────────────────────────────────────
def beautify(col: str) -> str:
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())

def aplicar_padrao_numerico_brasileiro(num):
    if pd.isna(num): return "-"
    n = float(num)
    if n.is_integer():
        return f"{int(n):,}".replace(",", ".")
    inteiro, frac = str(f"{n:,.2f}").split(".")
    return f"{inteiro.replace(',', '.')},{frac}"

def format_number_br(num):
    try:    return f"{int(num):,}".replace(",", ".")
    except: return str(num)

# ─── 5. CARGA DO PARQUET (rápido + tipos category) ──────────────────
@st.cache_data(ttl=None, persist=True, show_spinner="Carregando dados…")
def carregar_dados():
    df = pd.read_parquet("dados.parquet", engine="pyarrow")

    for cod in ["Cód. Município", "Cód. da Escola"]:
        if cod in df.columns:
            df[cod] = (
                pd.to_numeric(df[cod], errors="coerce")
                .astype("Int64").astype(str).replace("<NA>", "")
            )

    def _split(s: str):
        p = s.split(" - ")
        etapa = p[0]
        sub   = p[1] if len(p) > 1 else ""
        serie = " - ".join(p[2:]) if len(p) > 2 else ""
        return etapa, sub, serie

    df[["Etapa", "Subetapa", "Série"]] = df["Etapa de Ensino"].apply(
        lambda x: pd.Series(_split(x))
    )

    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    df["Ano"] = df["Ano"].astype(str)
    df["Número de Matrículas"] = pd.to_numeric(df["Número de Matrículas"], errors="coerce")

    for c in ["Etapa", "Subetapa", "Série", "Rede"]:
        df[c] = df[c].astype("category")

    return (
        df[df["Nível de agregação"] == "escola"].copy(),
        df[df["Nível de agregação"] == "município"].copy(),
        df[df["Nível de agregação"] == "estado"].copy(),
    )

escolas_df, municipio_df, estado_df = carregar_dados()

# ─── 6. SIDEBAR – nível de agregação ────────────────────────────────
st.sidebar.title("Filtros")
nivel = st.sidebar.radio("Número de Matrículas por:",
                         ["Escola", "Município", "Estado PE"])
df_base = {"Escola": escolas_df, "Município": municipio_df, "Estado PE": estado_df}[nivel]
if df_base.empty:
    st.error("DataFrame vazio"); st.stop()

# largura das 3 colunas usadas no painel
COL_WIDTHS = [1.2, 2.2, 1.6]         # Ano | Rede | Etapa

# ─── 7. PAINEL DE FILTROS ───────────────────────────────────────────
#  ▸  layout fixo: 2 colunas na 1ª linha
#       • c_left  →   Ano(s)  +  Rede(s)
#       • c_right →   Etapa  →  (Subetapa)  →  (Série)
#  ▸  Subetapa e Série são empilhadas dentro do *mesmo* column,
#    por isso nunca “escorregam” mesmo que a caixa de Ano(s) cresça.

# -- CSS extra: distância menor título↔widget + altura baixa dos multiselect
EXTRA_CSS = """
/* ... mantém regras anteriores ... */

/* Remove espaçamento ENTRE os elementos titulo↔caixa */
.panel-filtros [data-testid="element-container"] {
    margin: 0 !important;
    padding: 0 !important;
}

/* Ajusta containers dos títulos */
.panel-filtros .stMarkdown[data-testid="stMarkdown"] {
    margin-bottom: -0.5rem !important;  /* Compensa margem residual */
}

/* Ajuste fino para alinhamento vertical */
.panel-filtros [data-testid="stVerticalBlock"] > div {
    gap: 0 !important;
}
"""
st.markdown(f"<style>{EXTRA_CSS}</style>", unsafe_allow_html=True)



with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)

    # 1ª LINHA ────────────────────────────────────────────────────────
    c_left, c_right = st.columns([3, 5], gap="small")

    # ●–––––  Ano(s) + Rede(s)  (coluna da ESQUERDA) –––––●
    with c_left:
        # Ano(s)
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df_base["Ano"].unique(), reverse=True)
        ano_sel = st.multiselect("", anos_disp, default=anos_disp, key="ano_sel")

        # Rede(s)
        st.markdown('<div class="filter-title" style="margin-top:0.4rem">Rede(s)</div>',
                    unsafe_allow_html=True)
        redes_disp = sorted(df_base["Rede"].dropna().unique())
        rede_sel = st.multiselect("", redes_disp, default=redes_disp, key="rede_sel")

    # ●–––––  Etapa → Subetapa → Série  (coluna da DIREITA) –––––●
    with c_right:
        # Etapa
        st.markdown('<div class="filter-title">Etapa</div>', unsafe_allow_html=True)
        etapas_disp = sorted(df_base["Etapa"].unique())
        etapa_sel = st.multiselect("", etapas_disp, default=[], key="etapa_sel")

        # Subetapa  (só aparece se houver Etapa selecionada)
        if etapa_sel:
            st.markdown('<div class="filter-title">Subetapa</div>', unsafe_allow_html=True)
            sub_disp = sorted(
                df_base.loc[
                    df_base["Etapa"].isin(etapa_sel) & (df_base["Subetapa"] != ""),
                    "Subetapa"
                ].unique()
            )
            sub_sel = st.multiselect("", sub_disp, default=[], key="sub_sel")
        else:
            sub_sel = []  # mantém a variável criada para o restante do script

        # Série  (aparece se houver Etapa + Subetapa)
        if etapa_sel and sub_sel:
            st.markdown('<div class="filter-title">Série</div>', unsafe_allow_html=True)
            serie_disp = sorted(
                df_base.loc[
                    df_base["Etapa"].isin(etapa_sel) &
                    df_base["Subetapa"].isin(sub_sel) &
                    (df_base["Série"] != ""),
                    "Série"
                ].unique()
            )
            serie_sel = st.multiselect("", serie_disp, default=[], key="serie_sel")
        else:
            serie_sel = []

    st.markdown('</div>', unsafe_allow_html=True)   # fecha .panel‑filtros


# ─── 8. FUNÇÃO DE FILTRO CACHEADA ───────────────────────────────────
@st.cache_data
def filtrar(base_df,
            anos: tuple,
            redes: tuple,
            etapas: tuple,
            subetapas: tuple,
            series: tuple) -> pd.DataFrame:
    m = base_df["Ano"].isin(anos)
    if redes:      m &= base_df["Rede"].isin(redes)
    if etapas:     m &= base_df["Etapa"].isin(etapas)
    if subetapas:  m &= base_df["Subetapa"].isin(subetapas)
    if series:     m &= base_df["Série"].isin(series)
    return base_df.loc[m]

df_filt = filtrar(
    df_base,
    tuple(ano_sel),
    tuple(rede_sel),
    tuple(etapa_sel),
    tuple(sub_sel),
    tuple(serie_sel),
)

# ─── 9. ALTURA DA TABELA (slider) ───────────────────────────────────
with st.sidebar.expander("Configurações avançadas da tabela", False):
    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

# ─── 10. TABELA + FILTROS LOCAIS + PAGINAÇÃO ────────────────────────
vis_cols = ["Ano", "Etapa", "Subetapa", "Série", "Número de Matrículas"]
if nivel == "Escola":
    vis_cols += ["Cód. da Escola", "Nome da Escola", "Cód. Município",
                 "Nome do Município", "Rede"]
elif nivel == "Município":
    vis_cols += ["Cód. Município", "Nome do Município", "Rede"]
else:
    vis_cols += ["Rede"]

df_tabela = df_filt[vis_cols].copy()
if df_tabela.empty:
    st.warning("Não há dados para exibir."); st.stop()

# cabeçalho + filtros
header_cols  = st.columns([1]*len(vis_cols), gap="small")
filter_cols  = st.columns([1]*len(vis_cols), gap="small")
mask = pd.Series(True, index=df_tabela.index)

for col, h_col, f_col in zip(vis_cols, header_cols, filter_cols):
    with h_col:
        st.markdown(f"<b>{beautify(col)}</b>", unsafe_allow_html=True)
    with f_col:
        f = st.text_input("", key=f"filter_{col}", label_visibility="collapsed").strip()
    if f:
        col_s = df_tabela[col]
        if col.startswith("Número de") or pd.api.types.is_numeric_dtype(col_s):
            f_val = f.replace(",", ".")
            if re.fullmatch(r"-?\d+(\.\d+)?", f_val):
                mask &= col_s == float(f_val)
            else:
                mask &= col_s.astype(str).str.contains(f, case=False, regex=False)
        else:
            mask &= col_s.astype(str).str.contains(f, case=False, regex=False)

df_texto = df_tabela[mask]

# paginação
PAGE_SIZE = st.session_state.get("page_size", 25)
total_pg  = max(1, (len(df_texto)-1)//PAGE_SIZE + 1)
pg_atual  = min(st.session_state.get("current_page", 1), total_pg)
start = (pg_atual-1)*PAGE_SIZE
df_page = df_texto.iloc[start:start+PAGE_SIZE]

for c in df_page.columns:
    if c.startswith("Número de"):
        df_page[c] = df_page[c].apply(aplicar_padrao_numerico_brasileiro)

st.dataframe(df_page, height=altura_tabela, use_container_width=True, hide_index=True)

# botões
b1, b2, b3, b4 = st.columns([1,1,1,2])
with b1:
    if st.button("◀", disabled=pg_atual==1):
        st.session_state["current_page"] = pg_atual-1; st.rerun()
with b2:
    if st.button("▶", disabled=pg_atual==total_pg):
        st.session_state["current_page"] = pg_atual+1; st.rerun()
with b3:
    new_ps = st.selectbox("Itens", [10,25,50,100],
                          index=[10,25,50,100].index(PAGE_SIZE),
                          label_visibility="collapsed")
    if new_ps != PAGE_SIZE:
        st.session_state["page_size"] = new_ps
        st.session_state["current_page"] = 1; st.rerun()
with b4:
    st.markdown(f"**Página {pg_atual}/{total_pg} · "
                f"{format_number_br(len(df_texto))} registros**")

# ─── 11. DOWNLOADS (on‑click) ───────────────────────────────────────
def gerar_csv():  st.session_state["csv_bytes"]  = df_texto.to_csv(index=False).encode("utf-8")
def gerar_xlsx():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df_texto.to_excel(w, index=False, sheet_name="Dados")
    st.session_state["xlsx_bytes"] = buf.getvalue()

st.sidebar.download_button("CSV",   data=None, key="csv_dl",
                           mime="text/csv", file_name="dados.csv",
                           on_click=gerar_csv)
st.sidebar.download_button("Excel", data=None, key="xlsx_dl",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           file_name="dados.xlsx", on_click=gerar_xlsx)

# ─── 12. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
delta = time.time() - st.session_state.get("tempo_inicio", time.time())
st.caption(f"Tempo de processamento: {delta:.2f}s")
st.session_state["tempo_inicio"] = time.time()
# ====================================================================
