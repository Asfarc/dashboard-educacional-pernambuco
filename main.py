# =============================  main.py  =============================
# Dashboard • Matrículas (formato longo)
# --------------------------------------------------------------------
#  ► Painel: Ano(s) | Etapa | Subetapa | Série | Rede(s)
#  ► Tabela detalhada com filtros por coluna e paginação
# --------------------------------------------------------------------

# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st, pandas as pd, io, re, time
import altair as alt                 #  ← trazido do layout_primeiros_indicadores

# --------- PARÂMETROS E FUNÇÕES (vinham de layout_primeiros_indicadores)
# 1. Configura locale pt‑BR no Altair (caso você venha a usar gráficos)
alt.renderers.set_embed_options({
    'formatLocale': {
        'decimal': ',',
        'thousands': '.',
        'grouping': [3],
        'currency': ['R$', '']
    }
})

# 2. Parâmetros de estilo do container
PARAMETROS_ESTILO_CONTAINER = {
    "raio_borda": 8,
    "cor_borda": "#dee2e6",
    "cor_titulo": "#364b60",
    "tamanho_fonte_titulo": "1.1rem",
    "tamanho_fonte_conteudo": "1rem",
    "cor_fonte_conteudo": "#364b60",
}

# 3. Função que gera CSS adicional (usada logo após o set_page_config)
def obter_estilo_css_container(params=None) -> str:
    if params is None:
        params = PARAMETROS_ESTILO_CONTAINER
    return f"""
    <style>
    .container-custom {{
        padding:0!important;margin-bottom:0!important;background:transparent!important;
    }}
    .container-title {{
        font-size:{params["tamanho_fonte_titulo"]}!important;color:{params["cor_titulo"]}!important;
    }}
    .container-text {{
        font-size:{params["tamanho_fonte_conteudo"]}!important;color:{params["cor_fonte_conteudo"]}!important;
    }}
    </style>
    """

# 4. (opcional) Função de gráfico — deixe comentada se não usar agora
"""
def construir_grafico_linha_evolucao(df_transformado, **kwargs):
    # …  (código completo igual ao original) …
    return grafico
"""
# --------------------------------------------------------------------

# ─── 2. CONFIGURAÇÃO DA PÁGINA ───────────────────────────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 3 ─── CSS GERAL (container + painel + sidebar) ─────────────────────
CSS_IN_LINE = """
/* ===== PAINEL DE FILTROS NO MAIN ===== */
.panel-filtros{
    background:#eef2f7;border:1px solid #dce6f3;border-radius:6px;
    padding:0.8rem 1rem 1rem;margin-bottom:1.2rem;
}
.filter-title{
    font-weight:600;color:#364b60;font-size:0.92rem;margin:0 0 0.35rem
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"]::before{
    content:"";position:absolute;top:0;left:0;width:100%;height:100%;
    background:#364b60;z-index:0;border-radius:1px;
}
[data-testid="stSidebar"]>div{
    position:relative;z-index:1;padding:2rem 1rem!important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stRadio span:not([role="radio"]){
    color:#fff!important;
}
[data-testid="stSidebar"] option,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] [data-baseweb="select"] div{color:#000!important}
[data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]{
    background:#e37777!important;color:#fff!important;border-radius:1px!important
}

/* ===== BOTÕES ===== */
.stButton>button,.stDownloadButton>button{
    background:#364b60!important;color:#fff!important;border:none!important;
    border-radius:3px!important;transition:all .3s ease;
}
.stButton>button:hover,.stDownloadButton>button:hover{
    background:#25344d!important;transform:translateY(-1px);
    box-shadow:0 2px 5px rgba(0,0,0,0.1);
}

/* ===== PILL RADIOBUTTON ===== */
button[kind="pills"][data-testid="stBaseButton-pills"]{
    background:transparent!important;color:#fff!important;
    border:1px solid #e37777!important;border-radius:1px!important
}
button[kind="pills"][data-testid="stBaseButton-pills"]:hover{
    background:rgba(227,119,119,.2)!important
}
button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"]{
    background:#e37777!important;color:#fff!important;border:none!important;
    border-radius:1px!important
}
button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] p{
    color:#fff!important;font-weight:bold
}

/* ===== RESPONSIVO ===== */
@media screen and (max-width:768px){
    [data-testid="stSidebar"]{width:100%!important;margin:0!important;padding:0!important}
}
"""

# primeiro: CSS específico dos “containers” (KPI etc.)
st.markdown(
    obter_estilo_css_container(PARAMETROS_ESTILO_CONTAINER),
    unsafe_allow_html=True,
)

# depois: todo o restante do estilo
st.markdown(f"<style>{CSS_IN_LINE}</style>", unsafe_allow_html=True)

# ─── 4. FUNÇÕES AUXILIARES ───────────────────────────────────────────
def beautify(col: str) -> str:
    return " ".join(p.capitalize() for p in col.replace("\n", " ").lower().split())

def aplicar_padrao_numerico_brasileiro(num):
    if pd.isna(num) or num == "-":
        return "-"
    try:
        n = float(num)
        if n.is_integer():
            return f"{int(n):,}".replace(",", ".")
        inteiro, frac = str(f"{n:,.2f}").split(".")
        return f"{inteiro.replace(',', '.')},{frac}"
    except Exception:  # noqa: E722
        return str(num)

def format_number_br(num):
    try:
        return f"{int(num):,}".replace(",", ".")
    except Exception:  # noqa: E722
        return str(num)

# ─── 5. LEITURA DO PARQUET ───────────────────────────────────────────
@st.cache_resource(show_spinner="Carregando dados.parquet…")
def importar_parquet_unico():
    df = pd.read_parquet("dados.parquet")

    # converte códigos para texto
    for cod in ["Cód. Município", "Cód. da Escola"]:
        if cod in df.columns:
            df[cod] = (
                pd.to_numeric(df[cod], errors="coerce")
                .astype("Int64")
                .astype(str)
                .replace("<NA>", "")
            )

    # cria Etapa / Subetapa / Série
    def _split(s):
        p = s.split(" - ")
        etapa = p[0]
        sub   = p[1] if len(p) > 1 else "—"
        serie = " - ".join(p[2:]) if len(p) > 2 else "—"
        return etapa, sub, serie
    df[["Etapa", "Subetapa", "Série"]] = df["Etapa de Ensino"].apply(
        lambda x: pd.Series(_split(x))
    )

    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    df["Ano"] = df["Ano"].astype(str)
    df["Número de Matrículas"] = pd.to_numeric(df["Número de Matrículas"], errors="coerce")

    return (
        df[df["Nível de agregação"] == "escola"].copy(),
        df[df["Nível de agregação"] == "estado"].copy(),
        df[df["Nível de agregação"] == "município"].copy(),
    )

escolas_df, estado_df, municipio_df = importar_parquet_unico()

# ─── 6. SIDEBAR (nível de agregação) ─────────────────────────────────
st.sidebar.title("Filtros")
nivel = st.sidebar.radio("Número de Matrículas por:",
                         ["Escola", "Município", "Estado PE"])
df = {"Escola": escolas_df, "Município": municipio_df, "Estado PE": estado_df}[nivel]
if df.empty:
    st.error("DataFrame vazio"); st.stop()

# ─── 7. PAINEL DE FILTROS ────────────────────────────────────────────
with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)

    # 7.1 Ano(s) + Etapa
    c_ano, c_etapa = st.columns([1.2, 3], gap="small")

    with c_ano:
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df["Ano"].unique(), reverse=True)
        all_anos  = st.checkbox("Tudo", value=True, key="anos_all")
        anos_sel = st.multiselect("", anos_disp,
                                  default=(anos_disp if all_anos else anos_disp[:1]),
                                  key="anos_multiselect")
        if all_anos and len(anos_sel) != len(anos_disp):
            st.session_state["anos_all"] = False

    with c_etapa:
        st.markdown('<div class="filter-title">Etapa</div>', unsafe_allow_html=True)
        etapas_disp = sorted(df["Etapa"].unique())
        etapa_sel = st.selectbox("", ["Todas"] + etapas_disp, key="etapa_sel")

    # 7.2 Subetapa
    if etapa_sel != "Todas" and df[df["Etapa"] == etapa_sel]["Subetapa"].nunique() > 1:
        st.markdown('<div class="filter-title">Subetapa</div>', unsafe_allow_html=True)
        sub_disp = sorted(df[df["Etapa"] == etapa_sel]["Subetapa"].unique())
        sub_sel = st.selectbox("", ["Todas"] + sub_disp, key="sub_sel")
    else:
        sub_sel = "Todas"

    # 7.3 Série
    if (sub_sel != "Todas"
        and df[(df["Etapa"] == etapa_sel) & (df["Subetapa"] == sub_sel)]["Série"].nunique() > 1):
        st.markdown('<div class="filter-title">Série</div>', unsafe_allow_html=True)
        serie_disp = sorted(
            df[(df["Etapa"] == etapa_sel) & (df["Subetapa"] == sub_sel)]["Série"].unique()
        )
        serie_sel = st.selectbox("", ["Todas"] + serie_disp, key="serie_sel")
    else:
        serie_sel = "Todas"

    # 7.4 Rede(s)
    st.markdown('<div class="filter-title" style="margin-top:0.6rem">Rede(s)</div>',
                unsafe_allow_html=True)
    redes_disp = sorted(df["Rede"].dropna().unique())
    all_rede   = st.checkbox("Tudo", value=True, key="rede_all")
    rede_sel = st.multiselect("", redes_disp,
                              default=(redes_disp if all_rede else []),
                              key="dep_selection")
    if all_rede and len(rede_sel) != len(redes_disp):
        st.session_state["rede_all"] = False

    st.markdown('</div>', unsafe_allow_html=True)

# ─── 8. APLICA FILTROS AO DATAFRAME ─────────────────────────────────
df_filt = df[df["Ano"].isin(anos_sel)]
if rede_sel:
    df_filt = df_filt[df_filt["Rede"].isin(rede_sel)]
if etapa_sel != "Todas":
    df_filt = df_filt[df_filt["Etapa"] == etapa_sel]
if sub_sel != "Todas":
    df_filt = df_filt[df_filt["Subetapa"] == sub_sel]
if serie_sel != "Todas":
    df_filt = df_filt[df_filt["Série"] == serie_sel]

# ─── 9. CONFIG. AVANÇADAS DA TABELA ─────────────────────────────────
with st.sidebar.expander("Configurações avançadas da tabela", False):
    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

# ─── 10. PREPARA TABELA (colunas) ───────────────────────────────────
base_cols = ["Ano", "Etapa", "Subetapa", "Série", "Número de Matrículas"]
if nivel == "Escola":
    base_cols += ["Cód. da Escola", "Nome da Escola", "Cód. Município",
                  "Nome do Município", "Rede"]
elif nivel == "Município":
    base_cols += ["Cód. Município", "Nome do Município", "Rede"]
else:  # Estado
    base_cols += ["Rede"]

df_para_tabela = df_filt[[c for c in base_cols if c in df_filt.columns]].copy()
if df_para_tabela.empty:
    st.warning("Não há dados para exibir."); st.stop()

# ─── 11. FILTROS LOCAIS + PAGINAÇÃO ────────────────────────────────
num_cols = len(df_para_tabela.columns)
header_cols = st.columns([1] * num_cols, gap="small")
filter_cols = st.columns([1] * num_cols, gap="small")

col_filters = {}
for i, col_name in enumerate(df_para_tabela.columns):
    with header_cols[i]:
        st.markdown(f"<div style='font-weight:600'>{beautify(col_name)}</div>",
                    unsafe_allow_html=True)
    with filter_cols[i]:
        col_filters[col_name] = st.text_input("",
                                              key=f"filter_{i}_{col_name}",
                                              placeholder=f"Filtrar {beautify(col_name)}…",
                                              label_visibility="collapsed")

df_texto_filtrado = df_para_tabela.copy()
for col_name, filtro in col_filters.items():
    if not filtro:
        continue
    expr = re.escape(filtro)
    try:
        if col_name.startswith("Número de") or pd.api.types.is_numeric_dtype(df_texto_filtrado[col_name]):
            ponto = filtro.replace(",", ".")
            if ponto.replace(".", "", 1).isdigit() and ponto.count(".") <= 1:
                df_texto_filtrado = df_texto_filtrado[df_texto_filtrado[col_name] == float(ponto)]
            else:
                df_texto_filtrado = df_texto_filtrado[
                    df_texto_filtrado[col_name].astype(str).str.contains(expr, case=False, regex=True)]
        else:
            df_texto_filtrado = df_texto_filtrado[
                df_texto_filtrado[col_name].astype(str).str.contains(expr, case=False, regex=True)]
    except Exception as e:  # noqa: E722
        st.warning(f"Erro ao filtrar {col_name}: {e}")

# Paginação
PAGE_SIZE = st.session_state.get("page_size", 50)
chunks = [df_texto_filtrado[i:i+PAGE_SIZE]
          for i in range(0, len(df_texto_filtrado), PAGE_SIZE)] or [df_texto_filtrado]
total_pg = len(chunks)
pg_atual = st.session_state.get("current_page", 1)
pg_atual = max(1, min(pg_atual, total_pg))
st.session_state["current_page"] = pg_atual
df_pagina = chunks[pg_atual-1].reset_index(drop=True)

# Exibe
for c in df_pagina.columns:
    if c.startswith("Número de"):
        df_pagina[c] = df_pagina[c].apply(aplicar_padrao_numerico_brasileiro)
st.dataframe(df_pagina, height=altura_tabela, use_container_width=True, hide_index=True)

# Navegação
b1, b2, b3, b4 = st.columns([1, 1, 1, 2])
with b1:
    if st.button("◀ Anterior", disabled=pg_atual == 1):
        st.session_state["current_page"] = pg_atual - 1; st.rerun()
with b2:
    if st.button("Próximo ▶", disabled=pg_atual == total_pg):
        st.session_state["current_page"] = pg_atual + 1; st.rerun()
with b3:
    novo_psz = st.selectbox("Itens", [10, 25, 50, 100],
                            index=[10, 25, 50, 100].index(PAGE_SIZE),
                            label_visibility="collapsed")
    if novo_psz != PAGE_SIZE:
        st.session_state["page_size"] = novo_psz
        st.session_state["current_page"] = 1
        st.rerun()
with b4:
    st.markdown(f"**Página {pg_atual}/{total_pg} • "
                f"Total {format_number_br(len(df_texto_filtrado))} registros**")

# ─── 12. DOWNLOADS ───────────────────────────────────────────────────
csv_bytes = df_texto_filtrado.to_csv(index=False).encode("utf-8")
xlsx_buf = io.BytesIO()
with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as w:
    df_texto_filtrado.to_excel(w, index=False, sheet_name="Dados")
st.sidebar.download_button("CSV", csv_bytes, "dados.csv", "text/csv")
st.sidebar.download_button("Excel", xlsx_buf.getvalue(),
                           "dados.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─── 13. KPI / GRÁFICOS (placeholder) ───────────────────────────────
# aqui você pode usar df_filt para KPIs ou gráficos

# ─── 14. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
st.caption(f"Tempo de processamento: {time.time() - st.session_state.get('tempo_inicio', time.time()):.2f}s")
st.session_state['tempo_inicio'] = time.time()
# ====================================================================
