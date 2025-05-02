# ─── 1. IMPORTS ─────────────────────────────────────────
import streamlit as st, pandas as pd, re, time
from pathlib import Path
from utils import beautify, format_number_br
from data_io import load_parquets, df_to_csv, df_to_excel
from constantes import *  # rótulos e textos externos
from layout_primeiros_indicadores import (
    obter_estilo_css_container,
    PARAMETROS_ESTILO_CONTAINER,
)

# ─── 2. CONFIG. DA PÁGINA ───────────────────────────────
st.set_page_config(page_title="Dashboard PNE", page_icon="📊", layout="wide")

# ─── 3. INJETAR TODO O CSS ANTES DE QUALQUER COISA VISUAL
# 3-A) bloco que JÁ vem com <style>...</style>
st.markdown(
    obter_estilo_css_container(PARAMETROS_ESTILO_CONTAINER),
    unsafe_allow_html=True
)

# 3-B) seu arquivo static/style.css (apenas CSS puro, sem aspas!)
css_file = Path("static/style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css_file}</style>", unsafe_allow_html=True)

# ─── 4. DADOS (AGORA sobe pra cá!) ─────────────────────
escolas_df, estado_df, municipio_df = load_parquets()

opcoes_anos   = sorted(escolas_df["ANO"].unique(), reverse=True)
etapas        = sorted([c for c in escolas_df.columns
                        if c.startswith("Número de Matrículas")])
opcoes_redes  = sorted(escolas_df["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())

# ─── 5. TOPO DO DASHBOARD ──────────────────────────────
with st.container():
    st.markdown("""<div class="top-bar">🏫 Dashboard Educacional – Pernambuco</div>""",
                unsafe_allow_html=True)

# ─── 6. (opcional) PRIMEIRO bloco de widgets (pode remover) ───────
# Se quiser manter os 3 widgets iniciais, eles já vão ter as listas certas:
col1, col2, col3 = st.columns([3, 2, 2])
with col1:
    anos = st.multiselect("Ano(s)", opcoes_anos, default=opcoes_anos[-10:])
with col2:
    etapa = st.selectbox("Etapa / Subetapa", etapas)
with col3:
    redes = st.multiselect("Rede(s)", opcoes_redes, default=["Estadual","Municipal"])


# (1) Opções para os filtros, extraídas dos próprios dados
opcoes_anos   = sorted(escolas_df["ANO"].unique(), reverse=True)
etapas        = sorted([c for c in escolas_df.columns
                        if c.startswith("Número de Matrículas")])
opcoes_redes  = sorted(escolas_df["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())

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