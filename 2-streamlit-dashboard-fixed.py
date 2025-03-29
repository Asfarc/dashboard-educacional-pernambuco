import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from pathlib import Path
import io
import json
import re
from constantes import *
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -------------------------------
# Configuração Inicial da Página
# -------------------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para o sidebar esquerdo (inalterado)
css_sidebar = """
<style>
    /* Cria um overlay para toda a sidebar */
    [data-testid="stSidebar"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: #364b60;
        z-index: -1;
        border-radius: 1px;
        margin: 1rem;
        padding: 1rem;
    }
    /* Garante que os controles fiquem visíveis acima do overlay */
    [data-testid="stSidebar"] > div {
        position: relative;
        z-index: 1;
    }
    /* Texto branco para todos os elementos */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stRadio span:not([role="radio"]) {
        color: white !important;
    }
    /* Mantém o texto das opções em preto */
    [data-testid="stSidebar"] option,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] [data-baseweb="select"] div {
        color: black !important;
    }
    /* ------ REGRAS ATUALIZADAS ------ */
    /* Altera TODOS os itens selecionados na sidebar */
    [data-testid="stSidebar"] .stMultiSelect [aria-selected="true"] {
        background-color: #364b60 !important;
        color: white !important;
        border-radius: 1px !important;
    }
    /* Altera o hover */
    [data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:hover {
        background-color: #2a3a4d !important;
        cursor: pointer;
    }
    /* Remove a cor azul padrão do Streamlit */
    [data-testid="stSidebar"] .stMultiSelect [aria-selected="true"]:focus {
        box-shadow: none !important;
    }
</style>
"""
st.markdown(css_sidebar, unsafe_allow_html=True)

css_pills = """
<style>
    /* Estilo específico para os pills na barra lateral */
    [data-testid="stSidebar"] div[data-testid="stPills"] {
        margin-top: 8px;
    }
    /* Botões não selecionados (kind="pills") */
    button[kind="pills"][data-testid="stBaseButton-pills"] {
        background-color: transparent !important;
        color: white !important;
        border: 1px solid #e37777 !important;
        border-radius: 1px !important;
    }
    /* Botões selecionados (kind="pillsActive") */
    button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] {
        background-color: #e37777 !important; 
        color: white !important;          
        border: none !important;
        border-radius: 1px !important;
    }
    /* Estilização do texto nos botões ativos */
    button[kind="pillsActive"][data-testid="stBaseButton-pillsActive"] p {
        color: white !important;
        font-weight: bold;
    }
</style>
"""
st.markdown(css_pills, unsafe_allow_html=True)

# CSS para estilizar o "sidebar direito" (atualizado para seguir o padrão do esquerdo)
right_sidebar_css = """
<style>
    div[data-testid="column"]:nth-of-type(2) {
        background-color: #364b60;
        border-radius: 10px;
        padding: 1rem;
        border-left: 1px solid #e0e0e0;
        color: white;
    }
    div[data-testid="column"]:nth-of-type(2) h3 {
        color: white;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    div[data-testid="column"]:nth-of-type(2) .stButton > button {
        width: 100%;
    }
    /* Ajuste para inputs e selects dentro do painel direito */
    div[data-testid="column"]:nth-of-type(2) .stSelectbox, 
    div[data-testid="column"]:nth-of-type(2) .stSlider, 
    div[data-testid="column"]:nth-of-type(2) .stRadio {
        color: black;
        background-color: white;
    }
</style>
"""
st.markdown(right_sidebar_css, unsafe_allow_html=True)

# -------------------------------
# Funções Auxiliares
# -------------------------------
def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR:
    Ex.: 1234567 -> '1.234.567'
         1234.56 -> '1.234,56'
    Se o número for NaN ou '-', retorna '-'.
    """
    if pd.isna(numero) or numero == "-":
        return "-"
    try:
        if float(numero).is_integer():
            return f"{int(numero):,}".replace(",", ".")
        else:
            parte_inteira = int(float(numero))
            parte_decimal = abs(float(numero) - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except (ValueError, TypeError):
        return str(numero)

@st.cache_data
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    """
    try:
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]

        escolas_df = estado_df = municipio_df = None
        for diretorio in diretorios_possiveis:
            escolas_path = os.path.join(diretorio, "escolas.parquet")
            estado_path = os.path.join(diretorio, "estado.parquet")
            municipio_path = os.path.join(diretorio, "municipio.parquet")

            if os.path.exists(escolas_path) and os.path.exists(estado_path) and os.path.exists(municipio_path):
                escolas_df = pd.read_parquet(escolas_path)
                estado_df = pd.read_parquet(estado_path)
                municipio_df = pd.read_parquet(municipio_path)
                break

        if escolas_df is None or estado_df is None or municipio_df is None:
            raise FileNotFoundError(ERRO_ARQUIVOS_NAO_ENCONTRADOS)

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
    Carrega o mapeamento de colunas a partir do arquivo JSON.
    """
    try:
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]

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
    colunas_map = {col.lower().strip(): col for col in df.columns}

    def obter_coluna_real(nome_padrao):
        if nome_padrao in df.columns:
            return nome_padrao
        nome_normalizado = nome_padrao.lower().strip()
        if nome_normalizado in colunas_map:
            return colunas_map[nome_normalizado]
        return nome_padrao

    mapeamento_base = carregar_mapeamento_colunas()
    mapeamento_ajustado = {}

    for etapa, config in mapeamento_base.items():
        mapeamento_ajustado[etapa] = {
            "coluna_principal": obter_coluna_real(config.get("coluna_principal", "")),
            "subetapas": {},
            "series": {}
        }
        for subetapa, coluna in config.get("subetapas", {}).items():
            mapeamento_ajustado[etapa]["subetapas"][subetapa] = obter_coluna_real(coluna)
        for sub, series_dict in config.get("series", {}).items():
            if sub not in mapeamento_ajustado[etapa]["series"]:
                mapeamento_ajustado[etapa]["series"][sub] = {}
            for serie, col_serie in series_dict.items():
                mapeamento_ajustado[etapa]["series"][sub][serie] = obter_coluna_real(col_serie)
    return mapeamento_ajustado

def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    if etapa not in mapeamento:
        st.error(ERRO_ETAPA_NAO_ENCONTRADA.format(etapa))
        return ""
    if subetapa == "Todas":
        return mapeamento[etapa].get("coluna_principal", "")
    if "subetapas" not in mapeamento[etapa] or subetapa not in mapeamento[etapa]["subetapas"]:
        st.warning(ERRO_SUBETAPA_NAO_ENCONTRADA.format(subetapa, etapa))
        return mapeamento[etapa].get("coluna_principal", "")
    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]
    series_subetapa = mapeamento[etapa].get("series", {}).get(subetapa, {})
    if not series_subetapa or serie not in series_subetapa:
        st.warning(ERRO_SERIE_NAO_ENCONTRADA.format(serie, subetapa))
        return mapeamento[etapa]["subetapas"][subetapa]
    return series_subetapa[serie]

def verificar_coluna_existe(df, coluna_nome):
    if not coluna_nome:
        return False, ""
    if coluna_nome in df.columns:
        return True, coluna_nome
    coluna_normalizada = coluna_nome.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}
    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]
    return False, coluna_nome

def converter_df_para_csv(df):
    if df is None or df.empty:
        return "Não há dados para exportar.".encode('utf-8')
    try:
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Erro ao converter para CSV: {str(e)}")
        return "Erro na conversão".encode('utf-8')

def converter_df_para_excel(df):
    if df is None or df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame({"Sem dados": []}).to_excel(writer, index=False, sheet_name='Sem_Dados')
        return output.getvalue()
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        return output.getvalue()
    except Exception as e:
        st.error(f"Erro ao converter para Excel: {str(e)}")
        output = io.BytesIO()
        output.write("Erro na conversão".encode('utf-8'))
        return output.getvalue()

def exibir_tabela_plotly_avancada(
    df_para_exibir, altura=600, coluna_dados=None, posicao_totais="bottom",
    alinhamento_padrao=None, cores_personalizadas=None,
    pagina_atual=1, itens_por_pagina=50, sort_column=None, sort_asc=True,
    colunas_nao_somadas=None, cache_key=None
):
    """
    Exibe um DataFrame usando Plotly Table com paginação e ordenação.
    As formatações condicionais foram removidas e os números (exceto ano/códigos) são formatados.
    """
    # Ordenação via parâmetro externo
    if sort_column and sort_column in df_para_exibir.columns:
        df_para_exibir = df_para_exibir.sort_values(
            by=sort_column,
            ascending=sort_asc
        )

    if df_para_exibir is None or df_para_exibir.empty:
        st.warning("Não há dados para exibir na tabela.")
        return {
            "data": pd.DataFrame(),
            "pagina_atual": 1,
            "total_paginas": 1,
            "total_linhas": 0
        }

    @st.cache_data(ttl=600)
    def copiar_dataframe(df):
        return df.copy()

    if cache_key:
        df_para_exibir = copiar_dataframe(df_para_exibir)

    total_linhas = len(df_para_exibir)
    total_paginas = max(1, (total_linhas + itens_por_pagina - 1) // itens_por_pagina)
    pagina_atual = min(max(1, pagina_atual), total_paginas)
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = min(inicio + itens_por_pagina, total_linhas)
    df_pagina = df_para_exibir.iloc[inicio:fim].copy()
    df_exibicao = df_pagina.copy()

    # Cores padrão
    cores_padrao = {
        "header_color": "#364b60",
        "even_row_color": "#f9f9f9",
        "odd_row_color": "white",
        "total_row_color": "#e6f2ff",
    }
    if cores_personalizadas:
        cores_padrao.update(cores_personalizadas)
    header_color = cores_padrao["header_color"]
    cell_colors = [cores_padrao["odd_row_color"], cores_padrao["even_row_color"]]
    total_row_color = cores_padrao["total_row_color"]

    if colunas_nao_somadas is None:
        colunas_nao_somadas = [
            "ANO", "CODIGO DA ESCOLA", "NOME DA ESCOLA", "CODIGO DO MUNICIPIO",
            "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"
        ]

    # Cálculo dos totais (mantido, embora não seja exibido abaixo da tabela)
    totais = {}
    if coluna_dados and coluna_dados in df_para_exibir.columns:
        for col in df_para_exibir.columns:
            if any(col_padrao in col for col_padrao in colunas_nao_somadas):
                if col == list(df_para_exibir.columns)[0]:
                    totais[col] = "TOTAL"
                else:
                    totais[col] = ""
            elif col.startswith("Número de") or col == coluna_dados or pd.api.types.is_numeric_dtype(df_para_exibir[col]):
                try:
                    totais[col] = df_para_exibir[col].sum()
                except:
                    totais[col] = ""
            else:
                totais[col] = ""

    # Formatação das colunas: para exceções (ex.: ANO, códigos) não aplicamos formatação
    colunas_excecao = ["ANO", "CODIGO DA ESCOLA", "CODIGO DO MUNICIPIO"]
    for col in df_exibicao.columns:
        if col in colunas_excecao:
            df_exibicao[col] = df_exibicao[col].apply(lambda x: str(x) if pd.notnull(x) else "-")
        elif col.startswith("Número de") or col == coluna_dados or pd.api.types.is_numeric_dtype(df_exibicao[col]):
            df_exibicao[col] = df_exibicao[col].apply(lambda x: formatar_numero(x) if pd.notnull(x) else "-")

    # Alinhamento das células: automático (números à direita, texto à esquerda)
    if alinhamento_padrao is None:
        cell_align = []
        for col in df_exibicao.columns:
            if col in colunas_excecao or col == coluna_dados or (pd.api.types.is_numeric_dtype(df_para_exibir[col])):
                cell_align.append('right')
            else:
                cell_align.append('left')
    elif isinstance(alinhamento_padrao, dict):
        cell_align = []
        for col in df_exibicao.columns:
            if col in alinhamento_padrao:
                cell_align.append(alinhamento_padrao[col])
            else:
                if col in colunas_excecao or col == coluna_dados or pd.api.types.is_numeric_dtype(df_para_exibir[col]):
                    cell_align.append('right')
                else:
                    cell_align.append('left')
    else:
        cell_align = [alinhamento_padrao] * len(df_exibicao.columns)

    header_values = list(df_exibicao.columns)
    cell_values = [df_exibicao[col].tolist() for col in df_exibicao.columns]

    # Criar cores alternadas simples (sem formatação condicional)
    fill_color = []
    if len(df_exibicao) > 0:
        for _ in df_exibicao.columns:
            row_colors = [cell_colors[i % 2] for i in range(len(df_exibicao))]
            fill_color.append(row_colors)
    else:
        fill_color = [cell_colors[0]]

    # Adicionar linha de totais se necessário
    if posicao_totais in ["top", "bottom"] and totais:
        total_row = []
        for col in df_exibicao.columns:
            if col in totais:
                if isinstance(totais[col], (int, float)):
                    total_row.append(formatar_numero(totais[col]))
                else:
                    total_row.append(totais[col])
            else:
                total_row.append("")
        if posicao_totais == "top":
            cell_values = [[total_row[i]] + values for i, values in enumerate(cell_values)]
            fill_color = [[total_row_color] + colors for colors in fill_color]
        else:  # bottom
            cell_values = [values + [total_row[i]] for i, values in enumerate(cell_values)]
            fill_color = [colors + [total_row_color] for colors in fill_color]

    # Preparar dados de hover simples
    hover_data = []
    for i, col in enumerate(df_exibicao.columns):
        col_hover = [""] * len(df_exibicao)
        if posicao_totais == "top":
            col_hover = ["Total"] + col_hover
        elif posicao_totais == "bottom":
            col_hover = col_hover + ["Total"]
        hover_data.append(col_hover)

    # Criação da tabela Plotly (sem updatemenus para ordenação interna)
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=header_values,
            fill_color=header_color,
            align='center',
            font=dict(color='white', size=13, family="Arial"),
            height=40
        ),
        cells=dict(
            values=cell_values,
            fill_color=fill_color,
            align=cell_align,
            font=dict(color='black', size=12, family="Arial"),
            height=35,
            line=dict(color='#d6d6d6', width=1)
        ),
        customdata=hover_data,
        hoverinfo="text"
    )])

    fig.update_layout(
        margin=dict(l=5, r=5, t=5, b=5),
        height=altura,
        hovermode="closest"
    )

    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': True,
        'scrollZoom': True,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'tabela_dados',
            'height': altura,
            'width': 1200,
            'scale': 2
        }
    })

    if total_paginas > 1:
        col1, col2, col3 = st.columns([2, 3, 2])
        with col1:
            if pagina_atual > 1:
                anterior = st.button("« Anterior")
            else:
                anterior = st.button("« Anterior", disabled=True)
        with col2:
            st.write(f"Página {pagina_atual} de {total_paginas} • "
                     f"Mostrando {(pagina_atual - 1) * itens_por_pagina + 1} a "
                     f"{min(pagina_atual * itens_por_pagina, total_linhas)} "
                     f"de {total_linhas} registros")
        with col3:
            if pagina_atual < total_paginas:
                proximo = st.button("Próximo »")
            else:
                proximo = st.button("Próximo »", disabled=True)

    return {
        "data": df_para_exibir,
        "pagina_atual": pagina_atual,
        "total_paginas": total_paginas,
        "total_linhas": total_linhas,
        "itens_por_pagina": itens_por_pagina
    }

# -------------------------------
# Carregamento de Dados
# -------------------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.stop()

# ======================================
# CONFIGURAÇÃO DA BARRA LATERAL ESQUERDA (FILTROS)
# ======================================
st.sidebar.title("Filtros")
tipo_visualizacao = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"]
)
if tipo_visualizacao == "Escola":
    df = escolas_df
elif tipo_visualizacao == "Município":
    df = municipio_df
else:
    df = estado_df

mapeamento_colunas = criar_mapeamento_colunas(df)

# Filtro do Ano
if "ANO" in df.columns:
    anos_disponiveis = sorted(df["ANO"].unique(), reverse=True)
    anos_selecionados = st.sidebar.multiselect(
        "Ano do Censo:",
        options=anos_disponiveis,
        default=[anos_disponiveis[0]],
        key="anos_multiselect"
    )
    if not anos_selecionados:
        st.warning("Por favor, selecione pelo menos um ano.")
        st.stop()
    df_filtrado = df[df["ANO"].isin(anos_selecionados)]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

etapas_disponiveis = list(mapeamento_colunas.keys())
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)
if etapa_selecionada not in mapeamento_colunas:
    st.error(f"A etapa '{etapa_selecionada}' não foi encontrada no mapeamento de colunas.")
    st.stop()

# Filtro de Subetapa
if "subetapas" in mapeamento_colunas[etapa_selecionada] and mapeamento_colunas[etapa_selecionada]["subetapas"]:
    subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

# Filtro de Série
series_disponiveis = []
if (subetapa_selecionada != "Todas"
        and "series" in mapeamento_colunas[etapa_selecionada]
        and subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]):
    series_disponiveis = list(mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada].keys())
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )
else:
    serie_selecionada = "Todas"

if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].unique())
    dependencia_selecionada = st.sidebar.pills(
        "DEPENDENCIA ADMINISTRATIVA:",
        options=dependencias_disponiveis,
        default=dependencias_disponiveis,
        selection_mode="multi",
        label_visibility="visible"
    )
    if dependencia_selecionada:
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
    else:
        df_filtrado = df_filtrado[0:0]
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

coluna_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento_colunas)
coluna_existe, coluna_real = verificar_coluna_existe(df_filtrado, coluna_dados)
if coluna_existe:
    coluna_dados = coluna_real
    df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_dados], errors='coerce') > 0]
else:
    st.warning(f"A coluna '{coluna_dados}' não está disponível nos dados.")
    coluna_principal = mapeamento_colunas[etapa_selecionada].get("coluna_principal", "")
    coluna_existe, coluna_principal_real = verificar_coluna_existe(df_filtrado, coluna_principal)
    if coluna_existe:
        coluna_dados = coluna_principal_real
        st.info(f"Usando '{coluna_dados}' como alternativa")
        df_filtrado = df_filtrado[pd.to_numeric(df_filtrado[coluna_dados], errors='coerce') > 0]
    else:
        st.error("Não foi possível encontrar dados para a etapa selecionada.")
        st.stop()

# -------------------------------
# Cabeçalho e Informações Iniciais
# -------------------------------
st.title(TITULO_DASHBOARD)
anos_texto = ", ".join(map(str, anos_selecionados))
st.markdown(f"**Visualização por {tipo_visualizacao} - Anos: {anos_texto}**")
filtro_texto = f"**Etapa:** {etapa_selecionada}"
if subetapa_selecionada != "Todas":
    filtro_texto += f" | **Subetapa:** {subetapa_selecionada}"
    if serie_selecionada != "Todas" and serie_selecionada in series_disponiveis:
        filtro_texto += f" | **Série:** {serie_selecionada}"
st.markdown(filtro_texto)

# -------------------------------
# Seção de Indicadores (KPIs)
# -------------------------------
col1, col2, col3 = st.columns(3)
try:
    total_matriculas = df_filtrado[coluna_dados].sum()
    with col1:
        st.metric(ROTULO_TOTAL_MATRICULAS, formatar_numero(total_matriculas))
except Exception as e:
    with col1:
        st.metric("Total de Matrículas", "-")
        st.caption(f"Erro ao calcular: {str(e)}")
with col2:
    try:
        if tipo_visualizacao == "Escola":
            if len(df_filtrado) > 0:
                media_por_escola = df_filtrado[coluna_dados].mean()
                st.metric(ROTULO_MEDIA_POR_ESCOLA, formatar_numero(media_por_escola))
            else:
                st.metric("Média de Matrículas por Escola", "-")
        else:
            if "DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns:
                media_por_dependencia = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[coluna_dados].mean()
                if not media_por_dependencia.empty:
                    media_geral = media_por_dependencia.mean()
                    st.metric(ROTULO_MEDIA_MATRICULAS, formatar_numero(media_geral))
                else:
                    st.metric("Média de Matrículas", "-")
            else:
                st.metric("Média de Matrículas", formatar_numero(df_filtrado[coluna_dados].mean()))
    except Exception as e:
        st.metric("Média de Matrículas", "-")
        st.caption(f"Erro ao calcular: {str(e)}")
with col3:
    try:
        if tipo_visualizacao == "Escola":
            total_escolas = len(df_filtrado)
            st.metric(ROTULO_TOTAL_ESCOLAS, formatar_numero(total_escolas))
        elif tipo_visualizacao == "Município":
            total_municipios = len(df_filtrado)
            st.metric(ROTULO_TOTAL_MUNICIPIOS, formatar_numero(total_municipios))
        else:
            max_valor = df_filtrado[coluna_dados].max()
            st.metric(ROTULO_MAXIMO_MATRICULAS, formatar_numero(max_valor))
    except Exception as e:
        if tipo_visualizacao == "Escola":
            st.metric("Total de Escolas", "-")
        elif tipo_visualizacao == "Município":
            st.metric("Total de Municípios", "-")
        else:
            st.metric("Máximo de Matrículas", "-")
        st.caption(f"Erro ao calcular: {str(e)}")

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown(f"## {TITULO_DADOS_DETALHADOS}")
# Layout: 3 colunas para a área principal e 1 coluna para o painel direito
main_area, right_sidebar = st.columns([3, 1])

colunas_tabela = []
if "ANO" in df_filtrado.columns:
    colunas_tabela.append("ANO")
if tipo_visualizacao == "Escola":
    colunas_adicionais = [
        "CODIGO DA ESCOLA",
        "NOME DA ESCOLA",
        "CODIGO DO MUNICIPIO",
        "NOME DO MUNICIPIO",
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]
elif tipo_visualizacao == "Município":
    colunas_adicionais = [
        "CODIGO DO MUNICIPIO",
        "NOME DO MUNICIPIO",
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]
else:
    colunas_adicionais = [
        "CODIGO DA UF",
        "NOME DA UF",
        "DEPENDENCIA ADMINISTRATIVA"
    ]
for col in colunas_adicionais:
    if col in df_filtrado.columns:
        colunas_tabela.append(col)
if coluna_dados in df_filtrado.columns:
    colunas_tabela.append(coluna_dados)
colunas_tabela = [c for c in colunas_tabela if c in df_filtrado.columns]

if coluna_dados in df_filtrado.columns:
    with pd.option_context('mode.chained_assignment', None):
        df_filtrado_tabela = df_filtrado[colunas_tabela].copy()
        df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')
    tabela_dados = df_filtrado_tabela.sort_values(by=coluna_dados, ascending=False)
    tabela_exibicao = tabela_dados.copy()
else:
    tabela_dados = df_filtrado[colunas_tabela].copy()
    tabela_exibicao = tabela_dados.copy()
tabela_filtrada = tabela_exibicao.copy()
tabela_com_totais = tabela_filtrada

if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = 1

# Mapeamento da posição dos totais
posicao_totais_map = {
    "Rodapé": "bottom",
    "Topo": "top",
    "Nenhum": None
}

# Parâmetros padrão para a tabela
alinhamento_valor = None  # Automático
itens_por_pagina = 50
altura_tabela = 600
cores_personalizadas = {
    "header_color": "#364b60",
    "even_row_color": "#f9f9f9",
    "odd_row_color": "white",
    "total_row_color": "#e6f2ff"
}
colunas_nao_somadas = ["ANO", "CODIGO DA ESCOLA", "NOME DA ESCOLA", "CODIGO DO MUNICIPIO",
                        "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]

if coluna_dados and coluna_dados in tabela_com_totais.columns:
    with pd.option_context('mode.chained_assignment', None):
        tabela_com_totais[coluna_dados] = pd.to_numeric(tabela_com_totais[coluna_dados], errors='coerce')
        tabela_com_totais[coluna_dados] = tabela_com_totais[coluna_dados].fillna(0)

# Painel principal com a tabela
with main_area:
    try:
        grid_result = exibir_tabela_plotly_avancada(
            tabela_com_totais,
            altura=altura_tabela,
            coluna_dados=coluna_dados,
            posicao_totais=posicao_totais_map.get("Rodapé"),
            alinhamento_padrao=alinhamento_valor,
            cores_personalizadas=cores_personalizadas,
            pagina_atual=st.session_state.pagina_atual,
            itens_por_pagina=itens_por_pagina,
            sort_column=st.session_state.get("sort_column", None),
            sort_asc=st.session_state.get("sort_asc", True),
            colunas_nao_somadas=colunas_nao_somadas,
            cache_key=f"{tipo_visualizacao}_{etapa_selecionada}_{subetapa_selecionada}_{'-'.join(map(str, anos_selecionados))}"
        )
    except Exception as e:
        st.error(f"Erro ao exibir tabela com Plotly: {str(e)}")
        st.dataframe(tabela_com_totais, height=altura_tabela)

# (Bloco de estatísticas abaixo da tabela removido para evitar repetição)

# Painel direito: Configurações da Tabela e Ordenação
with right_sidebar:
    st.markdown("### Configurações da Tabela")
    # Altura da tabela
    altura_personalizada = st.checkbox(ROTULO_AJUSTAR_ALTURA, value=False, help=DICA_ALTURA_TABELA)
    if altura_personalizada:
        altura_tabela = st.slider("Altura (pixels)", 200, 1000, 600, 50)
    # Linha de totais
    posicao_totais = st.radio(
        "Linha de totais:",
        ["Rodapé", "Topo", "Nenhum"],
        index=0
    )
    # Alinhamento
    alinhamento_opcoes = {
        "Automático": None,
        "Esquerda": "left",
        "Centro": "center",
        "Direita": "right"
    }
    alinhamento_selecionado = st.selectbox(
        "Alinhamento:",
        options=list(alinhamento_opcoes.keys()),
        index=0
    )
    alinhamento_valor = alinhamento_opcoes[alinhamento_selecionado]
    # Paginação
    itens_por_pagina = st.select_slider(
        "Itens por página:",
        options=[10, 25, 50, 100, 200, 500],
        value=50
    )
    # Esquema de cores
    esquema_cor = st.selectbox(
        "Esquema de cores:",
        ["Padrão", "Alto contraste", "Tons de azul", "Monocromático"]
    )
    if esquema_cor == "Padrão":
        cores_personalizadas = {
            "header_color": "#364b60",
            "even_row_color": "#f9f9f9",
            "odd_row_color": "white",
            "total_row_color": "#e6f2ff"
        }
    elif esquema_cor == "Alto contraste":
        cores_personalizadas = {
            "header_color": "#000000",
            "even_row_color": "#ffffff",
            "odd_row_color": "#f0f0f0",
            "total_row_color": "#dddddd"
        }
    elif esquema_cor == "Tons de azul":
        cores_personalizadas = {
            "header_color": "#1a5276",
            "even_row_color": "#ebf5fb",
            "odd_row_color": "#d6eaf8",
            "total_row_color": "#aed6f1"
        }
    else:  # Monocromático
        cores_personalizadas = {
            "header_color": "#4a4a4a",
            "even_row_color": "#f5f5f5",
            "odd_row_color": "#e0e0e0",
            "total_row_color": "#bdbdbd"
        }

    st.markdown("### Ordenação da Tabela")
    colunas_para_ordenar = list(df_filtrado.columns)
    # Seleciona a coluna de ordenação; se possível, usa a coluna_dados como padrão
    default_idx = colunas_para_ordenar.index(coluna_dados) if coluna_dados in colunas_para_ordenar else 0
    sort_column = st.selectbox("Ordenar por:", options=colunas_para_ordenar, index=default_idx)
    sort_order = st.radio("Ordem:", ["Crescente", "Decrescente"], index=1)
    sort_asc = True if sort_order == "Crescente" else False
    st.session_state.sort_column = sort_column
    st.session_state.sort_asc = sort_asc

    st.markdown("### Colunas para exibição")
    todas_colunas = [col for col in df_filtrado.columns if col not in colunas_tabela]
    if todas_colunas:
        colunas_adicionais = st.multiselect(
            "Colunas adicionais:",
            todas_colunas,
            placeholder="Selecionar colunas..."
        )
        if colunas_adicionais:
            novas_colunas = colunas_tabela.copy()
            novas_colunas.extend(colunas_adicionais)
            st.session_state.colunas_escolhidas = novas_colunas
    # Botão para aplicar configurações
    if st.button("Aplicar configurações", type="primary"):
        st.session_state.pagina_atual = 1  # Reset página ao aplicar novas configurações
        # Se houver novas colunas adicionadas, atualizar a tabela
        if 'colunas_escolhidas' in st.session_state:
            try:
                tabela_dados = df_filtrado[st.session_state.colunas_escolhidas].sort_values(by=coluna_dados,
                                                                                            ascending=False)
                tabela_com_totais = tabela_dados.copy()
            except Exception as e:
                st.error(f"Erro ao atualizar colunas: {str(e)}")

        # Usar a versão atualizada do rerun para garantir compatibilidade com todas as versões do Streamlit
        try:
            st.rerun()  # Versão mais recente do Streamlit
        except:
            try:
                st.experimental_rerun()  # Versão mais antiga do Streamlit
            except:
                st.warning(
                    "Não foi possível recarregar a aplicação automaticamente. Por favor, atualize a página manualmente.")

    st.markdown("---")
    st.markdown("### Exportar dados")
    try:
        csv_data = converter_df_para_csv(tabela_dados)
        st.download_button(
            label=ROTULO_BTN_DOWNLOAD_CSV,
            data=csv_data,
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.csv',
            mime='text/csv',
        )
    except Exception as e:
        st.error(f"Erro ao preparar CSV: {str(e)}")
    try:
        excel_data = converter_df_para_excel(tabela_dados)
        st.download_button(
            label=ROTULO_BTN_DOWNLOAD_EXCEL,
            data=excel_data,
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{"-".join(map(str, anos_selecionados))}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    except Exception as e:
        st.error(f"Erro ao preparar Excel: {str(e)}")
    st.markdown("### Resumo Estatístico")
    if coluna_dados and coluna_dados in df_filtrado.columns:
        try:
            descricao = df_filtrado[coluna_dados].describe()
            estatisticas = {
                "Mediana": formatar_numero(descricao["50%"]),
                "Desv. Padrão": formatar_numero(descricao["std"]),
                "Mínimo": formatar_numero(descricao["min"]),
                "25%": formatar_numero(descricao["25%"]),
                "75%": formatar_numero(descricao["75%"]),
                "Contagem": formatar_numero(descricao["count"])
            }
            stats_df = pd.DataFrame(list(estatisticas.items()), columns=["Estatística", "Valor"])
            st.dataframe(stats_df, hide_index=True, use_container_width=True)
            if st.checkbox("Mostrar gráfico de distribuição", value=False):
                fig = px.histogram(
                    df_filtrado,
                    x=coluna_dados,
                    nbins=20,
                    title=f"Distribuição de {coluna_dados}",
                    labels={coluna_dados: coluna_dados},
                    height=250
                )
                fig.update_layout(margin=dict(l=5, r=5, t=30, b=5), bargap=0.05)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar estatísticas: {str(e)}")
    else:
        st.info("Sem dados para estatísticas")

# Rodapé
st.markdown("---")
st.markdown(RODAPE_NOTA)
