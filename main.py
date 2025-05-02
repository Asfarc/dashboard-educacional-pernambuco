# =======================  main.py  =======================
# 1 ── IMPORTS BÁSICOS
import time, re, io, os, json, base64
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt

# utilitários próprios
from utils import beautify, format_number_br
from data_io import load_parquets, df_to_csv, df_to_excel          # se preferir, use importar_arquivos_parquet()
from constantes import *                                           # textos / rótulos
from layout_primeiros_indicadores import (
    obter_estilo_css_container,
    construir_grafico_linha_evolucao,
    PARAMETROS_ESTILO_CONTAINER,
)

# 2 ── CONFIG DA PÁGINA
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 3 ── CSS: container + arquivo externo (NÃO coloque css_unificado aqui!)
st.markdown(
    obter_estilo_css_container(PARAMETROS_ESTILO_CONTAINER),
    unsafe_allow_html=True
)

css_file = Path("static/style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css_file}</style>", unsafe_allow_html=True)

# 4 ── CARREGA DADOS (parquet) -----------------------------------------
try:
    escolas_df, estado_df, municipio_df = load_parquets()          # sua função no data_io
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# 5 ── SIDEBAR  -------------------------------------------------------
st.sidebar.title("Filtros")

tipo_nivel_agregacao = st.sidebar.radio(
    "Número de Matrículas por:",
    ["Escola", "Município", "Estado PE"]
)

df = {
    "Escola": escolas_df,
    "Município": municipio_df,
    "Estado PE": estado_df,
}[tipo_nivel_agregacao].copy()

if df.empty:
    st.warning(f"DataFrame de {tipo_nivel_agregacao} está vazio."); st.stop()

# 6 ── PREPARA LISTAS PARA WIDGETS ------------------------------------
anos_disp   = sorted(df["ANO"].unique(), reverse=True)
redes_disp  = sorted(df["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())

# -------- dicionário de etapas (json) ----------------
def ler_dicionario():
    path = "dicionario_das_etapas_de_ensino.json"
    if not os.path.exists(path):
        st.error("Arquivo dicionario_das_etapas_de_ensino.json não encontrado"); st.stop()
    return json.loads(Path(path).read_text(encoding="utf-8"))

def padronizar_dict(df_):
    base = ler_dicionario()
    norm = {c.replace('\n', '').lower(): c for c in df_.columns}
    def real(n): return norm.get(n.replace('\n', '').lower(), n)
    out = {}
    for etapa, cfg in base.items():
        out[etapa] = {
            "coluna_principal": real(cfg.get("coluna_principal", "")),
            "subetapas": {k: real(v) for k, v in cfg.get("subetapas", {}).items()},
            "series": {k: {s: real(c) for s, c in sd.items()} for k, sd in cfg.get("series", {}).items()},
        }
    return out

dict_etapas   = padronizar_dict(df)
lista_etapas  = list(dict_etapas.keys())
serie_padrao  = "Todas"                                             # filtro Série fixo

# 7 ── PAINEL SUPERIOR DE FILTROS  -----------------------------------
st.markdown(
    """
    <style>
        .panel-filtros{
            background:#eef2f7;border:1px solid #dce6f3;border-radius:6px;
            padding:0.7rem 1rem 1rem;margin-bottom:1.2rem;
        }
        .filter-title{font-weight:600;color:#364b60;font-size:0.92rem;margin-bottom:0.25rem}
        .stSelectbox > div, .stMultiSelect > div{min-height:38px}
    </style>
    """,
    unsafe_allow_html=True
)

with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)
    c_ano, c_etapa, c_rede = st.columns([1.3, 2.2, 1.8], gap="small")

    # --- ANOS ---
    with c_ano:
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos_check = st.checkbox(
            "Selecionar tudo",
            key="anos_select_all",
            value=True
        )
        default_anos = anos_disp if anos_check else anos_disp[:1]
        st.session_state["anos_multiselect"] = st.multiselect(
            "", anos_disp, default=default_anos, key="anos_multiselect"
        )
        if anos_check and len(st.session_state["anos_multiselect"]) != len(anos_disp):
            st.session_state["anos_select_all"] = False

    # --- ETAPA / SUBETAPA ---
    with c_etapa:
        st.markdown('<div class="filter-title">Etapa / Subetapa</div>', unsafe_allow_html=True)
        etapa_sel = st.selectbox("", lista_etapas, key="etapa_ensino", label_visibility="collapsed")
        sub_opts  = ["Todas"] + list(dict_etapas[etapa_sel]["subetapas"].keys())
        sub_sel   = st.selectbox("", sub_opts, key="subetapa", label_visibility="collapsed")

    # --- REDE ---
    with c_rede:
        st.markdown('<div class="filter-title">Rede(s)</div>', unsafe_allow_html=True)
        rede_check = st.checkbox("Selecionar tudo", key="rede_select_all", value=True)
        default_redes = redes_disp if rede_check else redes_disp[:]
        st.session_state["dep_selection"] = st.multiselect(
            "", redes_disp, default=default_redes, key="dep_selection"
        )
        if rede_check and len(st.session_state["dep_selection"]) != len(redes_disp):
            st.session_state["rede_select_all"] = False

    st.markdown('</div>', unsafe_allow_html=True)

# 8 ── APLICA FILTROS AO DATAFRAME ----------------------------------
df_filtrado = df[df["ANO"].isin(st.session_state["anos_multiselect"])]

if st.session_state["dep_selection"]:
    df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"]
                              .isin(st.session_state["dep_selection"])]

# --- identifica coluna de matrículas para a etapa ---
def coluna_matriculas(et, sub):
    cfg = dict_etapas[et]
    if sub == "Todas":
        return cfg["coluna_principal"]
    return cfg["subetapas"].get(sub, cfg["coluna_principal"])

COL_MATR = coluna_matriculas(etapa_sel, sub_sel)
if COL_MATR not in df_filtrado.columns:
    st.error("Coluna de matrículas não encontrada."); st.stop()

df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[COL_MATR], errors="coerce") > 0]

# 9 ── TABELA PAGINADA (versão resumida) -----------------------------
PAGE_SZ = st.session_state.get("page_size", 50)
chunks  = [df_filtrado[i:i+PAGE_SZ] for i in range(0, len(df_filtrado), PAGE_SZ)] or [df_filtrado]
tot_pg  = len(chunks)
pg_at   = st.session_state.get("current_page", 1)
pg_at   = max(1, min(pg_at, tot_pg))
st.session_state["current_page"] = pg_at
df_page = chunks[pg_at-1].reset_index(drop=True)

# numéricas → formatação BR
for col in df_page.columns:
    if col.startswith("Número de"):
        df_page[col] = df_page[col].apply(format_number_br)

st.dataframe(df_page, height=600, use_container_width=True, hide_index=True)

col_prev, col_next = st.columns(2)
with col_prev:
    if st.button("◀", disabled=pg_at==1):
        st.session_state.current_page -= 1; st.rerun()
with col_next:
    if st.button("▶", disabled=pg_at==tot_pg):
        st.session_state.current_page += 1; st.rerun()

# 10 ── BOTÕES DE DOWNLOAD ------------------------------------------
st.sidebar.markdown("### Download dos dados")
with st.sidebar.columns(2)[0]:
    st.download_button("CSV", df_to_csv(df_filtrado),
                       f"dados_{etapa_sel}_{'-'.join(map(str, st.session_state['anos_multiselect']))}.csv",
                       mime="text/csv")
with st.sidebar.columns(2)[1]:
    st.download_button("Excel", df_to_excel(df_filtrado),
                       f"dados_{etapa_sel}_{'-'.join(map(str, st.session_state['anos_multiselect']))}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 11 ── KPIs e GRÁFICO DEMO -----------------------------------------
# (bloco idêntico ao seu antigo, mantido para referência)
dados_absolutos = {
    "Rede": ["Federal", "Estadual", "Municipal", "Privada"],
    "Escolas": [26, 1053, 4759, 2157],
    "Matrículas": [16377, 539212, 1082028, 512022],
    "Professores": [1609, 21845, 46454, 26575]
}
df_abs = pd.DataFrame(dados_absolutos)

col_esq, col_dir = st.columns(2)
with col_esq:
    total_escolas = format_number_br(df_abs["Escolas"].sum())
    st.metric("Total de Escolas", total_escolas)

with col_dir:
    df_evol = pd.DataFrame({
        "Ano": list(range(2015, 2024)),
        "Matrículas": [2295215, 2275551, 2263728, 2251952, 2232556,
                       2206605, 2139772, 2159399, 2149639]
    })
    chart = alt.Chart(df_evol).mark_line(point=True).encode(
        x="Ano:O", y="Matrículas:Q"
    )
    st.altair_chart(chart, use_container_width=True)

# 12 ── RODAPÉ -------------------------------------------------------
st.markdown("---")
st.caption("© Dashboard Educacional – Atualizado: 2025")

st.caption(f"Tempo de processamento: {time.time() - st.session_state.get('tempo_inicio', time.time()):.2f}s")
# ===============================================================
