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


# ─── 2‑B. MÚSICA DE FUNDO ───────────────────────────────────────────
def _musica_de_fundo(arquivo_mp3: str, volume: float = 0.25, flag: str = "musica_atual"):
    musica_atual = st.session_state.get(flag, "")
    if musica_atual == arquivo_mp3:
        return
    if musica_atual:
        components.html(
            """
            <script>
                const oldAudio = document.getElementById('bg-music');
                if (oldAudio) { oldAudio.pause(); oldAudio.remove(); }
                const oldBtn = document.querySelector('button[data-music-btn="true"]');
                if (oldBtn) { oldBtn.remove(); }
            </script>
            """, height=0, width=0
        )
    caminhos = [
        arquivo_mp3,
        f"static/{arquivo_mp3}",
        Path(__file__).parent / "static" / arquivo_mp3
    ]
    arquivo_encontrado = False
    for c in caminhos:
        if os.path.exists(c):
            mp3_bytes = Path(c).read_bytes()
            arquivo_encontrado = True
            st.session_state["ultimo_caminho_usado"] = str(c)
            break
    if not arquivo_encontrado:
        st.sidebar.warning(f"Áudio não encontrado: {arquivo_mp3}")
        st.session_state[flag] = ""
        return
    b64 = base64.b64encode(mp3_bytes).decode()
    components.html(
        f"""
        <audio id="bg-music" loop>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
          const audio = document.getElementById('bg-music');
          audio.volume = {volume};
          audio.play().catch(() => {{
              const btn = document.createElement('button');
              btn.textContent = "▶️ Tocar música";
              btn.setAttribute('data-music-btn', 'true');
              btn.style = `
                  position:fixed; bottom:20px; left:20px; z-index:10000;
                  padding:8px 16px; font-size:16px; cursor:pointer;
              `;
              btn.onclick = () => {{ audio.play(); btn.remove(); }};
              document.body.appendChild(btn);
          }});
        </script>
        """, height=0, width=0
    )
    st.session_state[flag] = arquivo_mp3

def tocar_musica_sidebar():
    musicas = {
        "Sol da Minha Vida": "static/01 ROBERTA MIRANDA SOL DA MINHA VIDA.mp3",
        "Vá Com Deus": "static/02 ROBERTA MIRANDA VA COM DEUS.mp3",
        "O Meu Amor Chorou": "static/07 O Meu Amor Chorou.mp3",
        "Vou-me embora": "static/12 Vou-Me Embora.mp3",
    }
    with st.sidebar:
        st.markdown("### 🎵 Música")
        ativar = st.checkbox("Ativar música", value=True)
        if not ativar:
            components.html(
                """
                <script>
                    const audio = document.getElementById('bg-music');
                    if (audio) audio.pause();
                </script>
                """, height=0, width=0
            )
            return
        musica_sel = st.selectbox("Selecionar música:", list(musicas.keys()))
        if "ultimo_caminho_usado" in st.session_state:
            st.caption(f"Caminho: {st.session_state['ultimo_caminho_usado']}")
    if ativar:
        _musica_de_fundo(musicas[musica_sel])

tocar_musica_sidebar()

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

# Adicionar estilo para melhorar a aparência dos botões rádio
st.markdown("""
<style>
/* Estilo para os botões rádio de nível */
.stRadio > div {
    padding: 10px 0;
}
.stRadio > div > label {
    background-color: #0073ba;
    border: 1px solid #000000;
    border-radius: 6px;
    padding: 10px;
    margin: 5px 0;
    display: flex;
    align-items: center;
    transition: all 0.2s ease;
}
.stRadio > div > label:hover {
    background-color: #dce6f3;
    transform: translateY(-2px);
}
.stRadio > div [data-testid="stMarkdownContainer"] p {
    margin: 0;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# Radio sem rótulo para escolha de nível
nivel = st.sidebar.radio(
    "",
    ["Escolas", "Municípios", "Pernambuco"],
    label_visibility="collapsed",
    key="nivel_sel"
)

# Mapeia para o DataFrame correto
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
    c_left, c_right = st.columns([0.5, 0.7], gap="large")

    with c_left:
        st.markdown('<div class="filter-title" style="height:32px">Ano(s)</div>', unsafe_allow_html=True)
        anos_disp = sorted(df_base["Ano"].unique(), reverse=True)
        ano_sel = st.multiselect("Ano(s)", anos_disp, default=anos_disp,
                                 key="ano_sel", label_visibility="collapsed")
        st.markdown('<div class="filter-title" style="margin-top:-12px;height:32px">Rede(s)</div>', unsafe_allow_html=True)
        redes_disp = sorted(df_base["Rede"].dropna().unique())
        rede_sel = st.multiselect("", redes_disp, default=redes_disp, key="rede_sel", label_visibility="collapsed")

    with c_right:
        c_r1, c_r2 = st.columns([0.9,1])
        with c_r1:
            st.markdown('<div class="filter-title" style="height:32px">Etapa</div>', unsafe_allow_html=True)
            etapas_disp = sorted(df_base["Etapa"].unique())
            etapa_sel = st.multiselect("", etapas_disp, default=[], key="etapa_sel", label_visibility="collapsed")

            if etapa_sel:
                st.markdown('<div class="filter-title" style="margin-top:-12px;height:32px">Subetapa</div>', unsafe_allow_html=True)
                sub_real = sorted(df_base.loc[
                                      df_base["Etapa"].isin(etapa_sel) & df_base["Subetapa"].ne(""),
                                      "Subetapa"
                                  ].unique())
                sub_disp = (["Total - Todas as Subetapas"] if etapa_sel else []) + sub_real
                sub_sel = st.multiselect("", sub_disp, default=[], key="sub_sel", label_visibility="collapsed")
            else:
                sub_sel = []

            if etapa_sel and sub_sel:
                st.markdown('<div class="filter-title" style="margin-top:-12px;height:32px">Série</div>', unsafe_allow_html=True)
                serie_real = sorted(df_base.loc[
                                        df_base["Etapa"].isin(etapa_sel) &
                                        df_base["Subetapa"].isin([s for s in sub_sel if not s.startswith("Total")]) &
                                        df_base["Série"].ne(""),
                                        "Série"
                                    ].unique())
                serie_disp = (["Total - Todas as Séries"] if sub_sel else []) + serie_real
                serie_sel = st.multiselect("", serie_disp, default=[], key="serie_sel", label_visibility="collapsed")
            else:
                serie_sel = []

    st.markdown('</div>', unsafe_allow_html=True)

# ─── 8. FUNÇÃO DE FILTRO (sem cache) ────────────────────────────────
def filtrar(df, anos, redes, etapas, subetapas, series):
    m = df["Ano"].isin(anos)
    if redes: m &= df["Rede"].isin(redes)
    if etapas: m &= df["Etapa"].isin(etapas)
    if subetapas:
        if "Total - Todas as Subetapas" not in subetapas:
            m &= df["Subetapa"].isin([s for s in subetapas if not s.startswith("Total")])
    if series:
        if "Total - Todas as Séries" not in series:
            m &= df["Série"].isin([s for s in series if not s.startswith("Total")])
    return df.loc[m]

# gera df_filtrado
df_filtrado = filtrar(
    df_base,
    tuple(ano_sel), tuple(rede_sel),
    tuple(etapa_sel), tuple(sub_sel), tuple(serie_sel),
)
if df_filtrado.empty:
    st.warning("Não há dados após os filtros."); st.stop()

# ─── 9. ALTURA DA TABELA (slider) ─────────────────────────────────
with st.sidebar.expander("Configurações avançadas da tabela", False):
    st.markdown("""
    <style>
    [data-testid="stExpander"] [data-testid="stSlider"] > div:first-child {
        color: #000000 !important; font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    altura_tabela = st.slider("Altura da tabela (px)", 200, 1000, 600, 50)

# ─── 10. TABELA COM FILTROS INTEGRADOS ─────────────────────────────
vis_cols = ["Ano","Etapa","Subetapa","Série"]
if nivel == "Escola":
    vis_cols += ["Cód. da Escola","Nome da Escola","Cód. Município","Nome do Município","Rede"]
elif nivel == "Município":
    vis_cols += ["Cód. Município","Nome do Município","Rede"]
else:
    vis_cols += ["Rede"]
vis_cols.append("Número de Matrículas")

df_tabela = df_filtrado[vis_cols]
if df_tabela.empty:
    st.warning("Não há dados para exibir."); st.stop()

# centraliza última coluna
st.markdown("""
<style>
[data-testid="stDataFrame"] table tbody tr td:last-child,
[data-testid="stDataFrame"] table thead tr th:last-child {
    text-align:center !important;
}
</style>
""", unsafe_allow_html=True)

# cabeçalhos
col_headers = st.columns(len(vis_cols))
for col, slot in zip(vis_cols, col_headers):
    with slot:
        extra = " style='text-align:center'" if col == "Número de Matrículas" else ""
        st.markdown(f"<div class='column-header'{extra}>{beautify(col)}</div>", unsafe_allow_html=True)

# filtros de coluna
col_filters = st.columns(len(vis_cols))
filter_values = {}
for col, slot in zip(vis_cols, col_filters):
    with slot:
        filter_values[col] = st.text_input("Filtro", key=f"filter_{col}", label_visibility="collapsed")

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

# paginação
dpage = Paginator(len(df_texto), page_size=st.session_state.get("page_size",25), current=st.session_state.get("current_page",1))
df_page = dpage.slice(df_texto)

# formatação numérica
for c in df_page.filter(like="Número de").columns:
    df_page[c] = df_page[c].apply(aplicar_padrao_numerico_brasileiro)

st.dataframe(df_page, height=altura_tabela, use_container_width=True, hide_index=True)

# controles de navegação
b1,b2,b3,b4 = st.columns([1,1,1,2])
with b1:
    if st.button("◀", disabled=dpage.current==1):
        st.session_state["current_page"] = dpage.current-1
        st.rerun()
with b2:
    if st.button("▶", disabled=dpage.current==dpage.total_pages):
        st.session_state["current_page"] = dpage.current+1
        st.rerun()
with b3:
    new_ps = st.selectbox("Itens",[10,25,50,100], index=[10,25,50,100].index(st.session_state.get("page_size",25)), label_visibility="collapsed")
    if new_ps != st.session_state.get("page_size",25):
        st.session_state["page_size"] = new_ps
        st.session_state["current_page"] = 1
        st.rerun()
with b4:
    st.markdown(f"**Página {dpage.current}/{dpage.total_pages} · {format_number_br(len(df_texto))} registros**")

# ─── 11. DOWNLOADS ──────────────────────────────────────────────────
def gerar_csv(): st.session_state["csv_bytes"] = df_texto.to_csv(index=False).encode("utf-8")
def gerar_xlsx():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df_texto.to_excel(w, index=False, sheet_name="Dados")
    st.session_state["xlsx_bytes"] = buf.getvalue()

st.sidebar.markdown("### Download")
col1,col2 = st.sidebar.columns(2)
with col1:
    st.download_button("Em CSV", data=df_texto.to_csv(index=False).encode("utf-8"), key="csv_dl", mime="text/csv", file_name="dados.csv", on_click=gerar_csv)
with col2:
    st.download_button("Em Excel", data=st.session_state.get("xlsx_bytes", io.BytesIO().getvalue()), key="xlsx_dl", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", file_name="dados.xlsx", on_click=gerar_xlsx)

# ─── 12. RODAPÉ ─────────────────────────────────────────────────────
st.markdown("---")
st.caption("© Dashboard Educacional – atualização: Mar 2025")
delta = time.time() - st.session_state.get("tempo_inicio", time.time())
st.caption(f"Tempo de processamento: {delta:.2f}s")
st.session_state["tempo_inicio"] = time.time()
from datetime import datetime
st.caption(f"Build: {datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC")
