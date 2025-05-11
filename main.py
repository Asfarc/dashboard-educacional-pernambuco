# dashboard_pne.py

# ─── 1. IMPORTS ──────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import io
import re
import time
import os
import psutil
from pathlib import Path

# ─── 2. PAGE CONFIG ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ─── FIM DA CONFIG ──────────────────────────────────────────────────

# ─── 3. CARREGA E APLICA CSS EXTERNO ────────────────────────────────

css_path = Path("static/style.css")
if css_path.exists():
    css = css_path.read_text()
    # Envolve em <style> aqui para o navegador interpretar como CSS
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
else:
    st.error("static/style.css não encontrado")

# ─── FIM DO CSS ─────────────────────────────────────────────────────

# ─── 4. FUNÇÕES DE UTILIDADE ────────────────────────────────────────

def beautify_header(col: str) -> str:
    """Unifica beautify e abreviações num único lugar."""
    abbreviations = {
        "Número de Matrículas": "Matrículas",
        "Nome do Município": "Município",
        "Nome da Escola": "Escola",
        "Etapa de Ensino": "Etapa",
        "Cód. Município": "Cód. Mun.",
        "Cód. da Escola": "Cód. Esc.",
        "UF": "UF"
    }
    if col in abbreviations:
        return abbreviations[col]
    parts = col.replace("\n", " ").lower().split()
    return " ".join(p.capitalize() for p in parts)

def format_num_br(x):
    """Formata inteiros e decimais no padrão brasileiro."""
    if pd.isna(x):
        return "-"
    try:
        n = float(x)
    except:
        return str(x)
    # se for inteiro
    if n.is_integer():
        return f"{int(n):,}".replace(",", ".")
    s = f"{n:,.2f}".split(".")
    return f"{s[0].replace(',', '.')},{s[1]}"

# ─── 5. PAGINAÇÃO SIMPLIFICADA ───────────────────────────────────────
class Paginator:
    def __init__(self, total, page_size=0, current=1):
        """
        page_size = 0 significa 'mostrar tudo'.
        """
        self.total = total
        self.page_size = total if page_size in (0, None) else page_size
        self.total_pages = max(1, (total - 1) // self.page_size + 1)
        self.current = max(1, min(current, self.total_pages))
        self.start = (self.current - 1) * self.page_size
        self.end = min(self.start + self.page_size, total)

    def slice(self, df):
        return df.iloc[self.start : self.end]

# ─── 6. CONSTS E DADOS ──────────────────────────────────────────────
MODALIDADES = {
    "Ensino Regular":                     "Ensino Regular.parquet",
    "Educação Profissional":              "Educação Profissional.parquet",
    "EJA - Educação de Jovens e Adultos": "EJA - Educação de Jovens e Adultos.parquet",
}

# Define colunas mínimas por esquema
COMMON_COLS = ["Ano", "Rede", "Nível de agregação", "Número de Matrículas"]
NEW_SCHEMA_COLS = COMMON_COLS + ["Etapa agregada", "Nome da Etapa de ensino/Nome do painel de filtro"]
OLD_SCHEMA_COLS = COMMON_COLS + ["Etapa de Ensino"]

@st.cache_resource(show_spinner="⏳ Carregando dados…")
def carregar_dados(modalidade: str):

    path = MODALIDADES[modalidade]
    # Escolhe colunas conforme presença de coluna 'Etapa agregada'
    sample = pd.read_parquet(path, engine="pyarrow", columns=[COMMON_COLS[0]])
    use_cols = NEW_SCHEMA_COLS if "Etapa agregada" in pd.read_parquet(path, engine="pyarrow", columns=["Etapa agregada"]).columns else OLD_SCHEMA_COLS
    df = pd.read_parquet(path, engine="pyarrow", columns=use_cols)

    # Otimiza tipos
    for c in ["Ano", "Rede", "Nível de agregação"]:
        if c in df.columns:
            df[c] = df[c].astype("category")

    # Normaliza códigos (se existirem)
    for cod in ["Cód. Município", "Cód. da Escola"]:
        if cod in df.columns:
            df[cod] = (pd.to_numeric(df[cod], errors="coerce")
                          .astype("Int64").astype(str)
                          .replace("<NA>", ""))

    # Unifica Etapa / Subetapa / Série
    if "Etapa agregada" in df.columns:
        df["Etapa"] = df["Etapa agregada"].astype("category")
        df["Subetapa"] = (df["Nome da Etapa de ensino/Nome do painel de filtro"]
                             .fillna("Total")
                             .astype("category"))
        df["Série"] = pd.Categorical(
            df.get("Ano/Série", pd.Series([""]*len(df))).fillna(""),
            categories=[""]
        )
    else:
        # esquema antigo
        def _split(s):
            p = s.split(" - ")
            return p[0], p[1] if len(p)>1 else "", " - ".join(p[2:]) if len(p)>2 else ""
        tmp = df["Etapa de Ensino"].str.split(" - ", expand=True)
        df["Etapa"]   = tmp[0].astype("category")
        df["Subetapa"]= tmp[1].fillna("").astype("category")
        df["Série"]   = tmp[2].fillna("").astype("category")

    # Reduz cardinalidade
    df["Nível de agregação"] = df["Nível de agregação"].str.lower()
    return {
        "escolas":    df[df["Nível de agregação"] == "escola"],
        "municípios": df[df["Nível de agregação"] == "município"],
        "pernambuco": df[df["Nível de agregação"] == "estado"],
    }

# ─── 7. SIDEBAR – Escolha de modalidade e nível ──────────────────────
with st.sidebar:
    st.markdown("## Modalidade", unsafe_allow_html=True)
    tipo_ensino = st.radio(
        "", list(MODALIDADES.keys()),
        index=0, label_visibility="collapsed"
    )
    ram_mb = psutil.Process(os.getpid()).memory_info().rss / 1024**2
    st.markdown(f"💾 RAM usada: **{ram_mb:.0f} MB**")
    st.markdown("---")
    st.title("Filtros")
    nivel = st.radio(
        "", ["Escolas","Municípios","Pernambuco"],
        index=0, label_visibility="collapsed", key="nivel_sel"
    )

dados_por_nivel = carregar_dados(tipo_ensino)
df_base = dados_por_nivel[nivel.lower()]
if df_base.empty:
    st.error("DataFrame vazio para esse nível")
    st.stop()

# ─── 8. PAINEL DE FILTROS ────────────────────────────────────────────
with st.container():
    st.markdown('<div class="panel-filtros">', unsafe_allow_html=True)
    c1, c2 = st.columns([0.5, 0.7], gap="large")
    # Ano e Rede
    with c1:
        st.markdown('<div class="filter-title">Ano(s)</div>', unsafe_allow_html=True)
        anos = sorted(df_base["Ano"].unique(), reverse=True)
        ano_sel = st.multiselect("", anos, default=[anos[0]] if anos else [], key="ano_sel", label_visibility="collapsed")

        st.markdown('<div class="filter-title">Rede(s)</div>', unsafe_allow_html=True)
        redes = sorted(df_base["Rede"].dropna().unique())
        rede_sel = st.multiselect("", redes, default=redes, key="rede_sel", label_visibility="collapsed")

    # Etapa / Subetapa / Série
    with c2:
        st.markdown('<div class="filter-title">Etapa</div>', unsafe_allow_html=True)
        etapas = sorted(df_base["Etapa"].unique())
        etapa_sel = st.multiselect("", etapas, default=etapas, key="etapa_sel", label_visibility="collapsed")

        st.markdown('<div class="filter-title">Subetapa</div>', unsafe_allow_html=True)
        subs = sorted(df_base.loc[df_base["Etapa"].isin(etapa_sel), "Subetapa"].unique())
        sub_disp = ["Total"] + [s for s in subs if s and s!="Total"]
        sub_sel = st.multiselect("", sub_disp, default=["Total"], key="sub_sel", label_visibility="collapsed")

        st.markdown('<div class="filter-title">Série</div>', unsafe_allow_html=True)
        if "Total" in sub_sel:
            serie_sel = []
        else:
            series = sorted(df_base.loc[df_base["Subetapa"].isin(sub_sel), "Série"].unique())
            serie_sel = st.multiselect("", series, default=series, key="serie_sel", label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)
# ─── FIM DO PAINEL ──────────────────────────────────────────────────

# ─── 9. FUNÇÃO DE FILTRO VETORIZADO ─────────────────────────────────
def filtrar(df, anos, redes, etapas, subetapas, series):
    masks = []
    masks.append(df["Ano"].isin(anos))

    if redes:
        masks.append(df["Rede"].isin(redes))

    if etapas:
        mask_e = df["Etapa"].isin(etapas)
        if not subetapas:
            mask_e &= df["Subetapa"]=="Total"
        masks.append(mask_e)

    if subetapas and "Total" not in subetapas:
        masks.append(df["Subetapa"].isin(subetapas))
    elif subetapas and "Total" in subetapas:
        masks.append(df["Subetapa"]=="Total")

    if series:
        masks.append(df["Série"].isin(series))

    # Combina todas as máscaras
    from functools import reduce
    import operator
    mask = reduce(operator.and_, masks, pd.Series(True, index=df.index))
    return df.loc[mask]

df_filtrado = filtrar(df_base, ano_sel, rede_sel, etapa_sel, sub_sel, serie_sel)
if df_filtrado.empty:
    st.warning("Não há dados após os filtros.")
    st.stop()

# ─── 10. CONTROLES AVANÇADOS (altura da tabela) ──────────────────────
with st.sidebar.expander("Configurações tabela", False):
    altura_tabela = st.slider("Altura (px)", 200, 1000, 600, 50)

# ─── 11. PREPARA TABELA PARA EXIBIÇÃO ────────────────────────────────
vis = ["Ano"]
if nivel=="Escolas":      vis += ["Nome do Município","Nome da Escola"]
elif nivel=="Municípios": vis += ["Nome do Município"]
vis += ["Etapa de Ensino","Rede","Número de Matrículas"]

df_tab = df_filtrado[vis].copy()
if nivel=="Pernambuco":
    df_tab.insert(1,"UF","Pernambuco")

# cabeçalhos
st.markdown("""
<style>
[data-testid="stDataFrame"] th, td { padding:4px 8px !important; }
[data-testid="stDataFrame"] td:last-child, th:last-child { text-align:center !important; }
</style>
""", unsafe_allow_html=True)

# linha de cabeçalhos customizados
cols = df_tab.columns.tolist()
hcols = st.columns(len(cols))
for name, col in zip(cols, hcols):
    with col:
        st.markdown(f"<div class='column-header'>{beautify_header(name)}</div>", unsafe_allow_html=True)

# filtros por coluna
vals = {}
fcols = st.columns(len(cols))
for name, col in zip(cols, fcols):
    with col:
        vals[name] = st.text_input("", key=f"f_{name}", label_visibility="collapsed")

mask = pd.Series(True, index=df_tab.index)
for c, v in vals.items():
    if v:
        s = df_tab[c]
        if pd.api.types.is_numeric_dtype(s):
            mask &= s == float(v.replace(",",".")) if re.fullmatch(r"-?\d+(\.\d+)?", v) else s.astype(str).str.contains(v, case=False)
        else:
            mask &= s.astype(str).str.contains(v, case=False)
df_tab2 = df_tab.loc[mask]

# paginação
ps = st.session_state.get("page_size", 0)
pg = Paginator(len(df_tab2), page_size=ps, current=st.session_state.get("current_page",1))
df_page = pg.slice(df_tab2)

# formatação numérica
for col in [c for c in df_page.columns if "Número de" in c]:
    df_page[col] = df_page[col].apply(format_num_br)

# exibe
st.dataframe(df_page, height=altura_tabela, use_container_width=True, hide_index=True)

# navegação
c1,c2,c3,c4 = st.columns([1,1,1,2])
with c1:
    if st.button("◀", disabled=pg.current==1):
        st.session_state["current_page"] = pg.current-1; st.rerun()
with c2:
    if st.button("▶", disabled=pg.current==pg.total_pages):
        st.session_state["current_page"] = pg.current+1; st.rerun()
with c3:
    opts = [10,25,50,100,0]
    sel = st.selectbox("Itens", opts, index=opts.index(ps), format_func=lambda x: "Todos" if x==0 else str(x), label_visibility="collapsed")
    if sel!=ps:
        st.session_state["page_size"]=sel; st.session_state["current_page"]=1; st.rerun()
with c4:
    st.markdown(f"**Página {pg.current}/{pg.total_pages} · {len(df_tab2):,} linhas**")

# ─── 12. BOTÕES DE DOWNLOAD ─────────────────────────────────────────
st.sidebar.markdown("### Download")
c1, c2 = st.sidebar.columns(2)
with c1:
    st.download_button("CSV", data=df_tab2.to_csv(index=False).encode("utf-8"),
                       file_name="dados.csv", mime="text/csv")
with c2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_tab2.to_excel(writer, index=False, sheet_name="Dados")
    st.download_button("Excel", data=buf.getvalue(),
                       file_name="dados.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─── 13. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")
delta = time.time() - st.session_state.get("tempo_inicio", time.time())
st.caption(f"Processamento: {delta:.2f}s")
st.session_state["tempo_inicio"] = time.time()
from datetime import datetime
st.caption(f"Build: {datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC")
