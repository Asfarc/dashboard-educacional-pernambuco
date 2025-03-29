import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import json
import os

# Caso você utilize um arquivo de constantes, importe aqui.
# from constantes import *
# Mas, para exemplo, vamos definir algumas constantes diretamente:
TITULO_DASHBOARD = "Painel de Indicadores PNE"
ROTULO_TOTAL_MATRICULAS = "Total de Matrículas"
ROTULO_MEDIA_POR_ESCOLA = "Média por Escola"
ROTULO_MEDIA_MATRICULAS = "Média de Matrículas"
ROTULO_TOTAL_ESCOLAS = "Total de Escolas"
ROTULO_TOTAL_MUNICIPIOS = "Total de Municípios"
ROTULO_MAXIMO_MATRICULAS = "Máximo de Matrículas"
TITULO_DADOS_DETALHADOS = "Dados Detalhados"
ROTULO_BTN_DOWNLOAD_CSV = "Baixar CSV"
ROTULO_BTN_DOWNLOAD_EXCEL = "Baixar Excel"
RODAPE_NOTA = "© 2025 - Meu Rodapé Personalizado"

ERRO_ARQUIVOS_NAO_ENCONTRADOS = "Não encontrei os arquivos Parquet (escolas, estado, municipio)."
ERRO_CARREGAR_DADOS = "Erro ao carregar dados: {}"
INFO_VERIFICAR_ARQUIVOS = "Verifique se os arquivos .parquet estão no diretório correto."
ERRO_ETAPA_NAO_ENCONTRADA = "Etapa não encontrada: {}"
ERRO_SUBETAPA_NAO_ENCONTRADA = "Subetapa '{}' não encontrada na etapa '{}'"
ERRO_SERIE_NAO_ENCONTRADA = "Série '{}' não encontrada na subetapa '{}'"

# Mensagens de ajuda
ROTULO_AJUSTAR_ALTURA = "Altura Personalizada da Tabela"
DICA_ALTURA_TABELA = "Ajuste a altura da tabela para facilitar a visualização."

# --------------------------------
# Configuração Inicial da Página
# --------------------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para estilizar a barra lateral
css_sidebar = """
<style>
    [data-testid="stSidebar"] {
        background-color: #364b60;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stRadio span:not([role="radio"]) {
        color: white !important;
    }
    [data-testid="stSidebar"] .stSelectbox, 
    [data-testid="stSidebar"] .stSlider, 
    [data-testid="stSidebar"] .stRadio, 
    [data-testid="stSidebar"] .stTextInput, 
    [data-testid="stSidebar"] .stMultiselect {
        color: black;
        background-color: white;
    }
</style>
"""
st.markdown(css_sidebar, unsafe_allow_html=True)

# -------------------------------
# Funções Auxiliares
# -------------------------------
def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR.
    Ex.: 1234567 -> '1.234.567'; 1234.56 -> '1.234,56'
    """
    if pd.isna(numero) or numero == "-":
        return "-"
    try:
        val = float(numero)
        if val.is_integer():
            return f"{int(val):,}".replace(",", ".")
        else:
            parte_inteira = int(val)
            parte_decimal = abs(val - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except:
        return str(numero)

@st.cache_data
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    """
    try:
        diretorios_possiveis = [".", "data", "dados"]
        escolas_df = estado_df = municipio_df = None

        for diretorio in diretorios_possiveis:
            e_path = os.path.join(diretorio, "escolas.parquet")
            uf_path = os.path.join(diretorio, "estado.parquet")
            m_path = os.path.join(diretorio, "municipio.parquet")

            if os.path.exists(e_path) and os.path.exists(uf_path) and os.path.exists(m_path):
                escolas_df = pd.read_parquet(e_path)
                estado_df = pd.read_parquet(uf_path)
                municipio_df = pd.read_parquet(m_path)
                break

        if escolas_df is None or estado_df is None or municipio_df is None:
            raise FileNotFoundError(ERRO_ARQUIVOS_NAO_ENCONTRADOS)

        # Exemplo de conversão para numérico se houver colunas "Número de ..."
        for df_ in [escolas_df, estado_df, municipio_df]:
            for col in df_.columns:
                if col.startswith("Número de"):
                    df_[col] = pd.to_numeric(df_[col], errors='coerce')

        return escolas_df, estado_df, municipio_df

    except Exception as e:
        st.error(ERRO_CARREGAR_DADOS.format(e))
        st.info(INFO_VERIFICAR_ARQUIVOS)
        st.stop()

@st.cache_data
def carregar_mapeamento_colunas():
    """
    Exemplo: Carrega o mapeamento de colunas de um JSON (se existir).
    """
    try:
        diretorios_possiveis = [".", "data", "dados"]
        for diretorio in diretorios_possiveis:
            json_path = os.path.join(diretorio, "mapeamento_colunas.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        raise FileNotFoundError("Arquivo mapeamento_colunas.json não encontrado")
    except Exception as e:
        st.error(f"Erro ao carregar o mapeamento de colunas: {e}")
        st.stop()

def criar_mapeamento_colunas(df):
    """
    Ajusta o mapeamento para garantir que as colunas existem no DataFrame.
    """
    base = carregar_mapeamento_colunas()
    if not base:
        return {}

    colunas_map = {col.lower(): col for col in df.columns}
    def get_real_col(nome):
        if nome in df.columns:
            return nome
        if nome.lower() in colunas_map:
            return colunas_map[nome.lower()]
        return nome

    mapeado = {}
    for etapa, info in base.items():
        mapeado[etapa] = {
            "coluna_principal": get_real_col(info.get("coluna_principal", "")),
            "subetapas": {},
            "series": {}
        }
        for sub, val in info.get("subetapas", {}).items():
            mapeado[etapa]["subetapas"][sub] = get_real_col(val)
        for sub, series_dict in info.get("series", {}).items():
            mapeado[etapa]["series"][sub] = {}
            for serie, col in series_dict.items():
                mapeado[etapa]["series"][sub][serie] = get_real_col(col)
    return mapeado

def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    """
    Retorna o nome da coluna correspondente à etapa/subetapa/série.
    """
    if etapa not in mapeamento:
        st.warning(ERRO_ETAPA_NAO_ENCONTRADA.format(etapa))
        return ""
    if subetapa == "Todas":
        return mapeamento[etapa]["coluna_principal"]
    if subetapa not in mapeamento[etapa]["subetapas"]:
        st.warning(ERRO_SUBETAPA_NAO_ENCONTRADA.format(subetapa, etapa))
        return mapeamento[etapa]["coluna_principal"]
    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]
    # Série específica
    if subetapa in mapeamento[etapa]["series"]:
        if serie in mapeamento[etapa]["series"][subetapa]:
            return mapeamento[etapa]["series"][subetapa][serie]
        else:
            st.warning(ERRO_SERIE_NAO_ENCONTRADA.format(serie, subetapa))
            return mapeamento[etapa]["subetapas"][subetapa]
    return mapeamento[etapa]["subetapas"][subetapa]

def converter_df_para_csv(df):
    if df.empty:
        return "Sem dados".encode('utf-8')
    return df.to_csv(index=False).encode('utf-8')

def converter_df_para_excel(df):
    output = io.BytesIO()
    if df.empty:
        # Cria planilha vazia
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame({"Sem dados": []}).to_excel(writer, index=False, sheet_name='SemDados')
    else:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

def exibir_tabela_plotly(
    df,
    altura=600,
    coluna_dados=None,
    posicao_totais=None,
    alinhamento="left",
    cores=None
):
    """
    Exibe uma tabela Plotly sem paginação e sem formatação condicional.
    - posicao_totais: 'top', 'bottom' ou None
    - alinhamento: 'left', 'center' ou 'right'
    - cores: dicionário com cores personalizadas
    """
    if df.empty:
        st.warning("Não há dados para exibir.")
        return

    # Ajuste de cores
    cores_padrao = {
        "header_color": "#364b60",
        "even_row_color": "#f9f9f9",
        "odd_row_color": "white",
        "total_row_color": "#e6f2ff",
    }
    if cores:
        cores_padrao.update(cores)

    # Monta a linha de totais (se solicitado)
    totais = {}
    if posicao_totais in ("top", "bottom") and coluna_dados in df.columns:
        colunas_nao_somadas = [
            "ANO", "CODIGO DA ESCOLA", "NOME DA ESCOLA",
            "CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO",
            "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"
        ]
        for col in df.columns:
            if col in colunas_nao_somadas:
                if col == df.columns[0]:
                    totais[col] = "TOTAL"
                else:
                    totais[col] = ""
            else:
                try:
                    soma = df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else ""
                    totais[col] = soma
                except:
                    totais[col] = ""

    # Formatação de colunas: remove pontos em ANO e Códigos
    colunas_excecao = ["ANO", "CODIGO DA ESCOLA", "CODIGO DO MUNICIPIO"]
    df_formatado = df.copy()
    for c in df_formatado.columns:
        if c in colunas_excecao:
            df_formatado[c] = df_formatado[c].apply(lambda x: str(int(x)) if pd.notnull(x) else "-")
        else:
            if pd.api.types.is_numeric_dtype(df_formatado[c]):
                df_formatado[c] = df_formatado[c].apply(lambda x: formatar_numero(x) if pd.notnull(x) else "-")

    # Constrói Table do Plotly
    header_values = list(df_formatado.columns)
    cell_values = [df_formatado[col].tolist() for col in df_formatado.columns]

    # Alternância de cor (linhas pares/ímpares)
    fill_color = []
    for _ in df_formatado.columns:
        fill_color.append([
            cores_padrao["odd_row_color"] if i % 2 == 0 else cores_padrao["even_row_color"]
            for i in range(len(df_formatado))
        ])

    # Se for pra ter linha de totais
    if posicao_totais in ("top", "bottom") and totais:
        total_row = []
        for col in df_formatado.columns:
            val = totais.get(col, "")
            if isinstance(val, (int, float)):
                val = formatar_numero(val)
            total_row.append(val)
        if posicao_totais == "top":
            for i in range(len(cell_values)):
                cell_values[i].insert(0, total_row[i])
            for i in range(len(fill_color)):
                fill_color[i].insert(0, cores_padrao["total_row_color"])
        else:  # bottom
            for i in range(len(cell_values)):
                cell_values[i].append(total_row[i])
            for i in range(len(fill_color)):
                fill_color[i].append(cores_padrao["total_row_color"])

    # Alinhamento
    if alinhamento not in ("left", "center", "right"):
        alinhamento = "left"
    align_list = [alinhamento] * len(df_formatado.columns)

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=header_values,
            fill_color=cores_padrao["header_color"],
            align="center",
            font=dict(color='white', size=14)
        ),
        cells=dict(
            values=cell_values,
            fill_color=fill_color,
            align=align_list,
            font=dict(color='black', size=12)
        )
    )])
    fig.update_layout(
        height=altura,
        margin=dict(l=5, r=5, t=5, b=5)
    )
    st.plotly_chart(fig, use_container_width=True)


# -------------------------------
# Carregamento dos Dados
# -------------------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# -------------------------------
# Barra Lateral (Única)
# -------------------------------
st.sidebar.title("Filtros e Configurações")

# Seletor de Nível de Agregação
tipo_visualizacao = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"],
    index=0
)

if tipo_visualizacao == "Escola":
    df_base = escolas_df
elif tipo_visualizacao == "Município":
    df_base = municipio_df
else:
    df_base = estado_df

# Cria mapeamento
mapeamento = criar_mapeamento_colunas(df_base)

# Filtro de Ano
if "ANO" in df_base.columns:
    anos_disponiveis = sorted(df_base["ANO"].unique())
    anos_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Ano(s):",
        options=anos_disponiveis,
        default=anos_disponiveis[:1]  # primeiro ano como default
    )
    if not anos_selecionados:
        st.warning("Selecione pelo menos um ano.")
        st.stop()
    df_filtrado = df_base[df_base["ANO"].isin(anos_selecionados)]
else:
    st.error("Coluna 'ANO' não encontrada.")
    st.stop()

# Filtro de Etapa
etapas_disponiveis = list(mapeamento.keys())
if not etapas_disponiveis:
    st.error("Nenhuma etapa configurada no mapeamento.")
    st.stop()
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)

# Filtro de Subetapa
subetapas = mapeamento[etapa_selecionada]["subetapas"].keys() if etapa_selecionada in mapeamento else []
subetapa_selecionada = "Todas"
if subetapas:
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + list(subetapas)
    )

# Filtro de Série
series_disponiveis = []
if subetapa_selecionada != "Todas":
    series_disponiveis = list(mapeamento[etapa_selecionada]["series"].get(subetapa_selecionada, {}).keys())
serie_selecionada = "Todas"
if series_disponiveis:
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )

# Filtro de Dependência
if "DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns:
    deps = sorted(df_filtrado["DEPENDENCIA ADMINISTRATIVA"].dropna().unique())
    deps_selecionadas = st.sidebar.multiselect(
        "Dependência Administrativa:",
        options=deps,
        default=deps
    )
    df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(deps_selecionadas)]
else:
    st.warning("Coluna 'DEPENDENCIA ADMINISTRATIVA' não encontrada nos dados.")

# Define coluna de dados principal
col_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento)
if col_dados not in df_filtrado.columns:
    st.warning(f"Coluna '{col_dados}' não encontrada. Usando 'coluna_principal' como fallback.")
    col_dados = mapeamento[etapa_selecionada]["coluna_principal"]

# Filtra para > 0, se fizer sentido
if col_dados in df_filtrado.columns:
    df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[col_dados], errors='coerce') > 0]

st.sidebar.markdown("---")
st.sidebar.markdown("### Configurações da Tabela")

# Altura
altura_personalizada = st.sidebar.checkbox("Altura personalizada?", value=False)
if altura_personalizada:
    altura_tabela = st.sidebar.slider("Altura da Tabela (px)", 200, 1200, 600, 50)
else:
    altura_tabela = 600

# Linha de Totais
pos_totais = st.sidebar.radio(
    "Linha de Totais:",
    ["Nenhum", "Topo", "Rodapé"],
    index=2
)
pos_totais_mapeado = None
if pos_totais == "Topo":
    pos_totais_mapeado = "top"
elif pos_totais == "Rodapé":
    pos_totais_mapeado = "bottom"

# Alinhamento
alinhamento = st.sidebar.selectbox("Alinhamento:", ["left", "center", "right"], index=0)

# Ordenação
colunas_para_ordenar = list(df_filtrado.columns)
if col_dados in colunas_para_ordenar:
    idx_default = colunas_para_ordenar.index(col_dados)
else:
    idx_default = 0
coluna_ordenacao = st.sidebar.selectbox("Ordenar por:", colunas_para_ordenar, index=idx_default)
ordem = st.sidebar.radio("Ordem:", ["Crescente", "Decrescente"], index=1)
asc = True if ordem == "Crescente" else False

# Limitar quantidade de linhas (substituindo a paginação)
max_linhas = st.sidebar.slider("Máximo de linhas exibidas:", 5, 2000, 50, 5)

# Esquema de cores
opcoes_cores = ["Padrão", "Alto contraste", "Tons de azul", "Monocromático"]
esquema_escolhido = st.sidebar.selectbox("Esquema de cores:", opcoes_cores, index=0)
cores_personalizadas = {
    "Padrão": {
        "header_color": "#364b60",
        "even_row_color": "#f9f9f9",
        "odd_row_color": "white",
        "total_row_color": "#e6f2ff"
    },
    "Alto contraste": {
        "header_color": "#000000",
        "even_row_color": "#ffffff",
        "odd_row_color": "#f0f0f0",
        "total_row_color": "#dddddd"
    },
    "Tons de azul": {
        "header_color": "#1a5276",
        "even_row_color": "#ebf5fb",
        "odd_row_color": "#d6eaf8",
        "total_row_color": "#aed6f1"
    },
    "Monocromático": {
        "header_color": "#4a4a4a",
        "even_row_color": "#f5f5f5",
        "odd_row_color": "#e0e0e0",
        "total_row_color": "#bdbdbd"
    },
}
cores_escolhidas = cores_personalizadas[esquema_escolhido]

# Botões de download
st.sidebar.markdown("### Exportar Dados")
def baixar_csv():
    csv_data = converter_df_para_csv(df_ordenado)
    st.download_button(
        label=ROTULO_BTN_DOWNLOAD_CSV,
        data=csv_data,
        file_name="dados_export.csv",
        mime="text/csv"
    )

def baixar_excel():
    excel_data = converter_df_para_excel(df_ordenado)
    st.download_button(
        label=ROTULO_BTN_DOWNLOAD_EXCEL,
        data=excel_data,
        file_name="dados_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------------
# Área Principal
# -------------------------------
st.title(TITULO_DASHBOARD)

# Exibe Filtros Selecionados
anos_texto = ", ".join(map(str, anos_selecionados))
st.markdown(f"**Visualização:** {tipo_visualizacao} | **Anos:** {anos_texto}")
info_etapa = f"**Etapa:** {etapa_selecionada}"
if subetapa_selecionada != "Todas":
    info_etapa += f" | **Subetapa:** {subetapa_selecionada}"
if serie_selecionada != "Todas":
    info_etapa += f" | **Série:** {serie_selecionada}"
st.markdown(info_etapa)

# KPIs
col1, col2, col3 = st.columns(3)
try:
    total_matriculas = df_filtrado[col_dados].sum()
    col1.metric(ROTULO_TOTAL_MATRICULAS, formatar_numero(total_matriculas))
except:
    col1.metric(ROTULO_TOTAL_MATRICULAS, "-")

try:
    if tipo_visualizacao == "Escola":
        media = df_filtrado[col_dados].mean()
        col2.metric(ROTULO_MEDIA_POR_ESCOLA, formatar_numero(media))
    else:
        media = df_filtrado[col_dados].mean()
        col2.metric(ROTULO_MEDIA_MATRICULAS, formatar_numero(media))
except:
    col2.metric("Média", "-")

try:
    if tipo_visualizacao == "Escola":
        total_escolas = len(df_filtrado)
        col3.metric(ROTULO_TOTAL_ESCOLAS, formatar_numero(total_escolas))
    elif tipo_visualizacao == "Município":
        total_municipios = len(df_filtrado)
        col3.metric(ROTULO_TOTAL_MUNICIPIOS, formatar_numero(total_municipios))
    else:
        max_valor = df_filtrado[col_dados].max()
        col3.metric(ROTULO_MAXIMO_MATRICULAS, formatar_numero(max_valor))
except:
    col3.metric("Indicador", "-")

st.markdown(f"## {TITULO_DADOS_DETALHADOS}")

# Ordena e limita linhas
df_ordenado = df_filtrado.sort_values(by=coluna_ordenacao, ascending=asc).head(max_linhas)

# Exibir a tabela Plotly
exibir_tabela_plotly(
    df_ordenado,
    altura=altura_tabela,
    coluna_dados=col_dados,
    posicao_totais=pos_totais_mapeado,
    alinhamento=alinhamento,
    cores=cores_escolhidas
)

# Botões de download (aqui embaixo, mas você pode deixar na sidebar se preferir)
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    baixar_csv()
with col_btn2:
    baixar_excel()

st.markdown("---")
st.markdown(RODAPE_NOTA)
