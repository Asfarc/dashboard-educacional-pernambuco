import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from pathlib import Path
import io

# Biblioteca do AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# -------------------------------
# Configuração Inicial da Página
# -------------------------------
st.set_page_config(
    page_title="Dashboard PNE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Funções Auxiliares
# -------------------------------

def formatar_numero(numero):
    """
    Formata números grandes adicionando separadores de milhar.
    Se o número for NaN ou '-', retorna '-'.
    """
    if pd.isna(numero) or numero == "-":
        return "-"
    return f"{int(numero):,}".replace(",", ".")

@st.cache_data
def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    - Lê os arquivos: escolas.parquet, estado.parquet e municipio.parquet.
    - Converte colunas que começam com 'Número de' para tipo numérico.
    Em caso de erro, exibe uma mensagem e interrompe a execução.
    """
    try:
        # Definir possíveis localizações dos arquivos
        diretorios_possiveis = [".", "data", "dados", os.path.join(os.path.dirname(__file__), "data")]

        # Tentar encontrar os arquivos em diferentes localizações
        escolas_df = None
        estado_df = None
        municipio_df = None

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
            raise FileNotFoundError("Não foi possível encontrar os arquivos Parquet necessários.")

        # Converter colunas numéricas para o tipo correto
        for df in [escolas_df, estado_df, municipio_df]:
            for col in df.columns:
                if col.startswith("Número de"):
                    df[col] = pd.to_numeric(df[col], errors='coerce')

        return escolas_df, estado_df, municipio_df

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        st.info("Verifique se os arquivos Parquet estão disponíveis no repositório.")
        st.stop()


def criar_mapeamento_colunas(df):
    """
    Cria um dicionário que mapeia as etapas de ensino para os nomes das colunas.
    Esse mapeamento inclui a coluna principal, subetapas e séries, facilitando a seleção
    dos dados conforme os filtros do usuário.

    Parâmetros:
    df (DataFrame): DataFrame a ser usado como referência para verificar colunas existentes
    """
    # Criar mapeamento de colunas (case-insensitive) apenas uma vez
    colunas_map = {col.lower().strip(): col for col in df.columns}

    # Função auxiliar para verificar e obter o nome correto da coluna
    def obter_coluna_real(nome_padrao):
        # Verifica se a coluna existe exatamente como foi especificada
        if nome_padrao in df.columns:
            return nome_padrao

        # Verifica se existe uma versão case-insensitive da coluna
        nome_normalizado = nome_padrao.lower().strip()
        if nome_normalizado in colunas_map:
            return colunas_map[nome_normalizado]

        # Se não encontrar, retorna o nome original
        return nome_padrao

    mapeamento = {
        "Educação Infantil": {
            "coluna_principal": obter_coluna_real("Número de Matrículas da Educação Infantil"),
            "subetapas": {
                "Creche": obter_coluna_real("Número de Matrículas da Educação Infantil - Creche"),
                "Pré-Escola": obter_coluna_real("Número de Matrículas da Educação Infantil - Pré-Escola")
            },
            "series": {}
        },
        "Ensino Fundamental": {
            "coluna_principal": obter_coluna_real("Número de Matrículas do Ensino Fundamental"),
            "subetapas": {
                "Anos Iniciais": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais"),
                "Anos Finais": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais")
            },
            "series": {
                "Anos Iniciais": {
                    "1º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 1º Ano"),
                    "2º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 2º Ano"),
                    "3º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 3º Ano"),
                    "4º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 4º Ano"),
                    "5º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Iniciais - 5º Ano")
                },
                "Anos Finais": {
                    "6º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 6º Ano"),
                    "7º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 7º Ano"),
                    "8º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 8º Ano"),
                    "9º Ano": obter_coluna_real("Número de Matrículas do Ensino Fundamental - Anos Finais - 9º Ano")
                }
            }
        },
        "Ensino Médio": {
            "coluna_principal": obter_coluna_real("Número de Matrículas do Ensino Médio"),
            "subetapas": {
                "Propedêutico": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico"),
                "Curso Técnico Integrado": obter_coluna_real(
                    "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional"),
                "Normal/Magistério": obter_coluna_real(
                    "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério")
            },
            "series": {
                "Propedêutico": {
                    "1ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Propedêutico - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Propedêutico - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Propedêutico - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Propedêutico - 4º ano/4ª Série"),
                    "Não Seriado": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Propedêutico - Não Seriado")
                },
                "Curso Técnico Integrado": {
                    "1ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 4º ano/4ª Série"),
                    "Não Seriado": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - Não Seriado")
                },
                "Normal/Magistério": {
                    "1ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real(
                        "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 4º ano/4ª Série")
                }
            }
        },
        "EJA": {
            "coluna_principal": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA)"),
            "subetapas": {
                "Ensino Fundamental": obter_coluna_real(
                    "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental"),
                "Ensino Médio": obter_coluna_real(
                    "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Médio")
            },
            "series": {
                "Ensino Fundamental": {
                    "Anos Iniciais": obter_coluna_real(
                        "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Iniciais"),
                    "Anos Finais": obter_coluna_real(
                        "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Finais")
                }
            }
        },
        "Educação Profissional": {
            "coluna_principal": obter_coluna_real("Número de Matrículas da Educação Profissional"),
            "subetapas": {
                "Técnica": obter_coluna_real("Número de Matrículas da Educação Profissional Técnica"),
                "Curso FIC": obter_coluna_real("Número de Matrículas da Educação Profissional - Curso FIC Concomitante")
            },
            "series": {
                "Técnica": {
                    "Concomitante": obter_coluna_real(
                        "Número de Matrículas da Educação Profissional Técnica - Curso Técnico Concomitante"),
                    "Subsequente": obter_coluna_real(
                        "Número de Matrículas da Educação Profissional Técnica - Curso Técnico Subsequente")
                }
            }
        }
    }

    return mapeamento


def obter_coluna_dados(etapa, subetapa, serie, mapeamento):
    """
    Determina a coluna de dados com base na etapa, subetapa e série selecionadas.

    Parâmetros:
    etapa (str): Etapa de ensino selecionada
    subetapa (str): Subetapa selecionada ("Todas" ou nome específico)
    serie (str): Série selecionada ("Todas" ou nome específico)
    mapeamento (dict): Mapeamento de colunas

    Retorna:
    str: Nome da coluna de dados
    """
    # Verificar se a etapa existe no mapeamento
    if etapa not in mapeamento:
        st.error(f"A etapa '{etapa}' não foi encontrada no mapeamento de colunas.")
        return ""

    # Caso 1: Nenhuma subetapa selecionada, usa coluna principal da etapa
    if subetapa == "Todas":
        return mapeamento[etapa].get("coluna_principal", "")

    # Verificar se a subetapa existe
    if "subetapas" not in mapeamento[etapa] or subetapa not in mapeamento[etapa]["subetapas"]:
        st.warning(f"A subetapa '{subetapa}' não foi encontrada para a etapa '{etapa}'.")
        return mapeamento[etapa].get("coluna_principal", "")

    # Caso 2: Nenhuma série específica selecionada, usa coluna da subetapa
    if serie == "Todas":
        return mapeamento[etapa]["subetapas"][subetapa]

    # Verificar se a subetapa tem séries e se a série selecionada existe
    series_subetapa = mapeamento[etapa].get("series", {}).get(subetapa, {})
    if not series_subetapa or serie not in series_subetapa:
        st.warning(f"A série '{serie}' não foi encontrada para a subetapa '{subetapa}'.")
        return mapeamento[etapa]["subetapas"][subetapa]

    # Caso 3: Série específica selecionada
    return series_subetapa[serie]


def verificar_coluna_existe(df, coluna_nome):
    """
    Verifica se uma coluna existe no DataFrame, tentando encontrar uma correspondência
    exata ou insensível a maiúsculas/minúsculas.

    Parâmetros:
    df (DataFrame): DataFrame a ser verificado
    coluna_nome (str): Nome da coluna a procurar

    Retorna:
    tuple: (coluna_existe, coluna_real)
        coluna_existe (bool): Indica se a coluna foi encontrada.
        coluna_real (str): Nome real da coluna encontrada ou nome original
    """
    # Verifica se a coluna existe exatamente como especificada
    if coluna_nome in df.columns:
        return True, coluna_nome

    # Verifica se existe uma versão case-insensitive
    coluna_normalizada = coluna_nome.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}

    if coluna_normalizada in colunas_normalizadas:
        return True, colunas_normalizadas[coluna_normalizada]

    # Não encontrou a coluna
    return False, coluna_nome


def adicionar_linha_totais(df, coluna_dados):
    """
    Adiciona uma linha de totais ao DataFrame.

    Parâmetros:
    df (DataFrame): DataFrame a ser processado
    coluna_dados (str): Nome da coluna de dados numéricos

    Retorna:
    DataFrame: DataFrame com a linha de totais adicionada
    """
    # Criar uma linha de totais
    totais = {}

    # Inicializar todas as colunas como vazias
    for col in df.columns:
        totais[col] = ""

    # Primeira coluna como "TOTAL"
    if len(df.columns) > 0:
        totais[df.columns[0]] = "TOTAL"

    # Calcular total para a coluna de dados
    if coluna_dados in df.columns:
        valor_total = pd.to_numeric(df[coluna_dados], errors='coerce').sum()
        totais[coluna_dados] = formatar_numero(valor_total)

    # Definir percentual como 100%
    if '% do Total' in df.columns:
        totais['% do Total'] = "100.00%"

    # Criar DataFrame com a linha de totais
    linha_totais = pd.DataFrame([totais], index=['TOTAL'])

    # Concatenar com o DataFrame original
    return pd.concat([df, linha_totais])


def aplicar_estilo_tabela(df, modo_desempenho=False):
    """
    Aplica estilos à tabela conforme o modo de desempenho.
    (Não será usada diretamente no AgGrid, mas mantemos aqui para não remover código).
    """
    if modo_desempenho or len(df) > 1000:
        # Estilo mínimo para melhor desempenho
        return df.style.set_properties(**{'text-align': 'center'})
    else:
        # Estilo completo para tabelas menores
        return df.style \
            .set_properties(**{'text-align': 'center'}) \
            .set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center')]},
            {'selector': 'td', 'props': [('text-align', 'center')]},
            # Destacar a linha de totais
            {'selector': 'tr:last-child', 'props': [
                ('font-weight', 'bold'),
                ('background-color', '#e6f2ff'),
                ('border-top', '2px solid #b3d9ff'),
                ('color', '#0066cc')
            ]}
        ])


def converter_df_para_csv(df):
    """Converte DataFrame para formato CSV"""
    return df.to_csv(index=False).encode('utf-8')


def converter_df_para_excel(df):
    """Converte DataFrame para formato Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()


# Função para exibir a tabela com AgGrid
def exibir_tabela_com_aggrid(df_para_exibir, altura=600):
    """
    Exibe o DataFrame usando AgGrid, agora SEM paginação manual e com rolagem vertical real.
    Convertendo tudo em string para evitar 'Invalid number' na linha 'TOTAL'.
    """
    df_str = df_para_exibir.astype(str)  # tudo como texto, evitando erro no AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_str)

    # Configura colunas padrão
    gb.configure_default_column(
        groupable=True,
        editable=False,
        wrapText=True,
        autoHeight=True
    )
    # Usar rolagem vertical nativa do AgGrid (sem paginação do AgGrid também):
    gb.configure_pagination(enabled=False)

    grid_options = gb.build()

    AgGrid(
        df_str,
        gridOptions=grid_options,
        height=altura,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=True,
        theme="streamlit",
    )


# -------------------------------
# Carregamento de Dados
# -------------------------------
escolas_df, estado_df, municipio_df = carregar_dados()

# ======================================
# CONFIGURAÇÃO DA BARRA LATERAL (FILTROS)
# ======================================

st.sidebar.title("Filtros")

# Seleção do nível de agregação
tipo_visualizacao = st.sidebar.radio(
    "Nível de Agregação:",
    ["Escola", "Município", "Estado"]
)

# Seleção do DataFrame conforme o nível escolhido
if tipo_visualizacao == "Escola":
    df = escolas_df
elif tipo_visualizacao == "Município":
    df = municipio_df
else:
    df = estado_df

# Agora crie o mapeamento de colunas usando o DataFrame selecionado
mapeamento_colunas = criar_mapeamento_colunas(df)

# Filtro do Ano
if "ANO" in df.columns:
    anos_disponiveis = sorted(df["ANO"].unique())
    ano_selecionado = st.sidebar.selectbox("Ano do Censo:", anos_disponiveis)
    df_filtrado = df[df["ANO"] == ano_selecionado]
else:
    st.error("A coluna 'ANO' não foi encontrada nos dados carregados.")
    st.stop()

# Filtro da DEPENDENCIA ADMINISTRATIVA
if "DEPENDENCIA ADMINISTRATIVA" in df.columns:
    dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].unique())
    dependencia_selecionada = st.sidebar.multiselect(
        "DEPENDENCIA ADMINISTRATIVA:",
        dependencias_disponiveis,
        default=dependencias_disponiveis
    )
    if dependencia_selecionada:
        df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
else:
    st.warning("A coluna 'DEPENDENCIA ADMINISTRATIVA' não foi encontrada nos dados carregados.")

# Filtro da Etapa de Ensino
etapas_disponiveis = list(mapeamento_colunas.keys())
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)

# Verificação se a etapa está no mapeamento
if etapa_selecionada not in mapeamento_colunas:
    st.error(f"A etapa '{etapa_selecionada}' não foi encontrada no mapeamento de colunas.")
    st.stop()

# Filtro da Subetapa (varia de acordo com a etapa selecionada)
if "subetapas" in mapeamento_colunas[etapa_selecionada] and mapeamento_colunas[etapa_selecionada]["subetapas"]:
    subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

# Filtro para a Série, se aplicável à subetapa selecionada
series_disponiveis = []
if (subetapa_selecionada != "Todas" and
        "series" in mapeamento_colunas[etapa_selecionada] and
        subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]):
    series_disponiveis = list(mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada].keys())
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )
else:
    serie_selecionada = "Todas"

# -------------------------------
# Determinação da Coluna de Dados
# -------------------------------
coluna_dados = obter_coluna_dados(etapa_selecionada, subetapa_selecionada, serie_selecionada, mapeamento_colunas)

# Verifica se a coluna existe no DataFrame
coluna_existe, coluna_real = verificar_coluna_existe(df_filtrado, coluna_dados)
if coluna_existe:
    coluna_dados = coluna_real
else:
    st.warning(f"A coluna '{coluna_dados}' não está disponível nos dados.")
    # Tenta usar a coluna principal como fallback
    coluna_principal = mapeamento_colunas[etapa_selecionada].get("coluna_principal.", "")
    coluna_existe, coluna_principal_real = verificar_coluna_existe(df_filtrado, coluna_principal)

    if coluna_existe:
        coluna_dados = coluna_principal_real
        st.info(f"Usando '{coluna_dados}' como alternativa")
    else:
        st.error("Não foi possível encontrar dados para a etapa selecionada.")
        st.stop()

# -------------------------------
# Cabeçalho e Informações Iniciais
# -------------------------------
st.title("Dashboard de Matrículas - Inepy")
st.markdown(f"**Visualização por {tipo_visualizacao} - Ano: {ano_selecionado}**")

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

# KPI 1
total_matriculas = df_filtrado[coluna_dados].sum()
with col1:
    st.metric("Total de Matrículas", formatar_numero(total_matriculas))

# KPI 2
with col2:
    if tipo_visualizacao == "Escola":
        if len(df_filtrado) > 0:
            media_por_escola = df_filtrado[coluna_dados].mean()
            st.metric("Média de Matrículas por Escola", formatar_numero(media_por_escola))
        else:
            st.metric("Média de Matrículas por Escola", "-")
    else:
        media_por_dependencia = df_filtrado.groupby("DEPENDENCIA ADMINISTRATIVA")[coluna_dados].mean()
        if not media_por_dependencia.empty:
            media_geral = media_por_dependencia.mean()
            st.metric("Média de Matrículas", formatar_numero(media_geral))
        else:
            st.metric("Média de Matrículas", "-")

# KPI 3
with col3:
    if tipo_visualizacao == "Escola":
        total_escolas = len(df_filtrado)
        st.metric("Total de Escolas", formatar_numero(total_escolas))
    elif tipo_visualizacao == "Município":
        total_municipios = len(df_filtrado)
        st.metric("Total de Municípios", formatar_numero(total_municipios))
    else:
        st.metric("Máximo de Matrículas", formatar_numero(df_filtrado[coluna_dados].max()))

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown("## Dados Detalhados")

# Selecionar colunas iniciais
colunas_tabela = ["ANO"]
if tipo_visualizacao == "Escola":
    colunas_tabela.extend(["CODIGO DA ESCOLA", "NOME DA ESCOLA", "CODIGO DO MUNICIPIO",
                           "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"])
elif tipo_visualizacao == "Município":
    colunas_tabela.extend(["CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO",
                           "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"])
else:
    colunas_tabela.extend(["CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"])

colunas_tabela.append(coluna_dados)

# Verifica colunas existentes no df_filtrado
colunas_existentes = [col for col in colunas_tabela if col in df_filtrado.columns]
colunas_tabela = colunas_existentes

df_filtrado_tabela = df_filtrado.copy()
if coluna_dados in df_filtrado_tabela.columns:
    df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')

    total = df_filtrado_tabela[coluna_dados].sum()
    if total > 0:
        df_filtrado_tabela['% do Total'] = df_filtrado_tabela[coluna_dados].apply(
            lambda x: (x / total) * 100 if pd.notnull(x) else None
        )
        colunas_tabela.append('% do Total')

    tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)

    tabela_exibicao = tabela_dados.copy()
    tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
        lambda x: formatar_numero(x) if pd.notnull(x) else "-"
    )

    if '% do Total' in tabela_exibicao.columns:
        tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
            lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
        )
else:
    tabela_dados = df_filtrado_tabela[colunas_existentes]
    tabela_exibicao = tabela_dados.copy()

# Cria abas
tab1, tab2 = st.tabs(["Visão Tabular", "Resumo Estatístico"])

with tab1:
    st.write("### Configurações de exibição")
    col1, col2, col3, col4 = st.columns(4)

    with col4:
        altura_personalizada = st.checkbox("Ajustar altura da tabela", value=False,
                                           help="Use esta opção se estiver vendo barras de rolagem duplicadas")
        if altura_personalizada:
            altura_manual = st.slider("Altura da tabela (pixels)",
                                      min_value=200,
                                      max_value=1000,
                                      value=600,
                                      step=50)
        else:
            altura_manual = 600  # Valor padrão

    with col1:
        total_registros = len(tabela_exibicao)
        # (Comentado) Paginação manual
        # st.warning(f"Há {formatar_numero(total_registros)} registros no total, exibidos todos de uma vez via AgGrid.")
        mostrar_todos = st.checkbox("Mostrar todos os registros", value=True)

    with col2:
        # (Comentado) Registros por página
        st.write(" ")  # espaço
    with col3:
        modo_desempenho = st.checkbox("Ativar modo de desempenho", value=True,
                                      help="Otimiza o carregamento para grandes conjuntos de dados.")

    st.write("### Filtros da tabela")
    col1, col2, col3, col4, col5, col6 = st.columns([0.6, 3.0, 0.6, 3.0, 0.6, 3.0])

    filtro_texto = None
    colunas_localidade = [col for col in ["NOME DA UF", "NOME DO MUNICIPIO", "NOME DA ESCOLA"] if
                          col in tabela_exibicao.columns]
    if colunas_localidade:
        with col1:
            st.write("**Localidade:**")
        with col2:
            coluna_texto_selecionada = st.selectbox("", ["Nenhum"] + colunas_localidade, label_visibility="collapsed")
            if coluna_texto_selecionada != "Nenhum":
                filtro_texto = st.text_input("", placeholder=f"Filtrar {coluna_texto_selecionada}...",
                                             label_visibility="collapsed", key="filtro_texto")

    filtro_codigo = None
    colunas_codigo = [col for col in ["CODIGO DA UF", "CODIGO DO MUNICIPIO", "CODIGO DA ESCOLA"] if
                      col in tabela_exibicao.columns]
    if colunas_codigo:
        with col3:
            st.write("**Código:**")
        with col4:
            coluna_codigo_selecionada = st.selectbox(" ", ["Nenhum"] + colunas_codigo, label_visibility="collapsed")
            if coluna_codigo_selecionada != "Nenhum":
                filtro_codigo = st.text_input(" ", placeholder=f"Filtrar {coluna_codigo_selecionada}...",
                                              label_visibility="collapsed", key="filtro_codigo")

    with col5:
        st.write("**Colunas:**")
    with col6:
        todas_colunas = [col for col in df_filtrado.columns if col not in colunas_tabela]
        if todas_colunas:
            colunas_adicionais = st.multiselect(
                "",
                todas_colunas,
                label_visibility="collapsed",
                placeholder="Selecionar colunas adicionais..."
            )
            if colunas_adicionais:
                colunas_tabela = colunas_tabela + colunas_adicionais
                tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
                tabela_exibicao = tabela_dados.copy()
                tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
                    lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                )
                if '% do Total' in tabela_exibicao.columns:
                    tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
                        lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                    )
        else:
            st.write("Não há colunas adicionais disponíveis")

    # Filtros via campo de busca
    tabela_filtrada = tabela_exibicao.copy()
    filtros_aplicados = False

    # Botão "Aplicar Filtros" em datasets grandes
    if len(tabela_exibicao) > 1000:
        col_filtrar = st.columns([1])[0]
        with col_filtrar:
            aplicar_filtros = st.button("Aplicar Filtros", type="primary")
        mostrar_dica = True
    else:
        aplicar_filtros = True
        mostrar_dica = False

    # Filtro de texto
    if filtro_texto and coluna_texto_selecionada != "Nenhum":
        if len(filtro_texto) >= 3 and aplicar_filtros:
            if len(tabela_filtrada) > 5000:
                tabela_filtrada = tabela_filtrada[
                    tabela_filtrada[coluna_texto_selecionada].astype(str).str.contains(filtro_texto, na=False)
                ]
            else:
                tabela_filtrada = tabela_filtrada[
                    tabela_filtrada[coluna_texto_selecionada].astype(str).str.contains(filtro_texto, case=False,
                                                                                       na=False)
                ]
            filtros_aplicados = True
        elif mostrar_dica and len(filtro_texto) > 0 and len(filtro_texto) < 3:
            st.info("Digite pelo menos 3 caracteres para filtrar por texto.")

    # Filtro de código
    if filtro_codigo and coluna_codigo_selecionada != "Nenhum":
        if len(filtro_codigo) >= 1 and aplicar_filtros:
            tabela_filtrada = tabela_filtrada[
                tabela_filtrada[coluna_codigo_selecionada].astype(str).str.contains(filtro_codigo, na=False)
            ]
            filtros_aplicados = True

    if filtros_aplicados and len(tabela_filtrada) < len(tabela_exibicao):
        st.success(
            f"Filtro aplicado: {len(tabela_filtrada)} de {len(tabela_exibicao)} registros correspondem aos critérios.")

    # Sem paginação manual: exibimos tudo
    # (Anteriormente havia cálculo de 'pagina_atual', 'registros_por_pagina' etc.)
    tabela_com_totais = adicionar_linha_totais(tabela_filtrada, coluna_dados)

    # Exibe a tabela inteira no AgGrid
    altura_tabela = altura_manual
    exibir_tabela_com_aggrid(tabela_com_totais, altura=altura_tabela)

    # Botões de download
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download CSV",
            data=converter_df_para_csv(tabela_dados),
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.csv',
            mime='text/csv',
        )
    with col2:
        st.download_button(
            label="Download Excel",
            data=converter_df_para_excel(tabela_dados),
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

with tab2:
    if coluna_dados in tabela_dados.columns:
        col1, col2 = st.columns(2)

        with col1:
            resumo = pd.DataFrame({
                'Métrica': ['Total', 'Média', 'Mediana', 'Mínimo', 'Máximo', 'Desvio Padrão'],
                'Valor': [
                    formatar_numero(tabela_dados[coluna_dados].sum()),
                    formatar_numero(tabela_dados[coluna_dados].mean()),
                    formatar_numero(tabela_dados[coluna_dados].median()),
                    formatar_numero(tabela_dados[coluna_dados].min()),
                    formatar_numero(tabela_dados[coluna_dados].max()),
                    formatar_numero(tabela_dados[coluna_dados].std())
                ]
            })
            st.write("### Resumo Estatístico")
            resumo_estilizado = resumo.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
            st.dataframe(resumo_estilizado, use_container_width=True, hide_index=True)

        with col2:
            st.write("### Top 5 Valores")
            top5 = tabela_dados.nlargest(5, coluna_dados)
            colunas_exibir = []
            if tipo_visualizacao == "Escola" and "NOME DA ESCOLA" in top5.columns:
                colunas_exibir.append("NOME DA ESCOLA")
            elif tipo_visualizacao == "Município" and "NOME DO MUNICIPIO" in top5.columns:
                colunas_exibir.append("NOME DO MUNICIPIO")
            elif "NOME DA UF" in top5.columns:
                colunas_exibir.append("NOME DA UF")

            if "DEPENDENCIA ADMINISTRATIVA" in top5.columns:
                colunas_exibir.append("DEPENDENCIA ADMINISTRATIVA")

            colunas_exibir.append(coluna_dados)
            if '% do Total' in top5.columns:
                colunas_exibir.append('% do Total')

            top5_exibir = top5[colunas_exibir].copy()
            if coluna_dados in top5_exibir.columns:
                top5_exibir[coluna_dados] = top5_exibir[coluna_dados].apply(
                    lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                )

            if '% do Total' in top5_exibir.columns:
                top5_exibir['% do Total'] = top5_exibir['% do Total'].apply(
                    lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                )

            top5_estilizado = top5_exibir.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
            st.dataframe(top5_estilizado, use_container_width=True, hide_index=True)

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown("**Nota:** Os dados são provenientes do Censo Escolar. Os traços (-) indicam ausência de dados.")