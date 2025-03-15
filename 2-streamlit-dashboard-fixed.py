import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from pathlib import Path

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

def carregar_dados():
    """
    Carrega os dados das planilhas no formato Parquet.
    - Lê os arquivos: escolas.parquet, estado.parquet e municipio.parquet.
    - Converte colunas que começam com 'Número de' para tipo numérico.
    Em caso de erro, exibe uma mensagem e interrompe a execução.
    """
    try:
        # Carregar os três arquivos Parquet
        escolas_df = pd.read_parquet("escolas.parquet")
        estado_df = pd.read_parquet("estado.parquet")
        municipio_df = pd.read_parquet("municipio.parquet")
        
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
        
# -------------------------------
# Carregamento de Dados
# -------------------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# ======================================
# CONFIGURAÇÃO DOS DADOS EDUCACIONAIS
# ======================================

def criar_mapeamento_colunas(df):
    """
    Cria um dicionário que mapeia as etapas de ensino para os nomes das colunas.
    Esse mapeamento inclui a coluna principal, subetapas e séries, facilitando a seleção
    dos dados conforme os filtros do usuário.
    
    Parâmetros:
    df (DataFrame): DataFrame a ser usado como referência para verificar colunas existentes
    """
    # Cria um dicionário de correspondência insensível a maiúsculas/minúsculas
    colunas_map = {col.lower().strip(): col for col in df.columns}
    
    mapeamento = {
        "Educação Infantil": {
            "coluna_principal": "Número de Matrículas da Educação Infantil",
            "subetapas": {
                "Creche": "Número de Matrículas da Educação Infantil - Creche",
                "Pré-Escola": "Número de Matrículas da Educação Infantil - Pré-Escola"
            },
            "series": {}
        },
        "Ensino Fundamental": {
            "coluna_principal": "Número de Matrículas do Ensino Fundamental",
            "subetapas": {
                "Anos Iniciais": "Número de Matrículas do Ensino Fundamental - Anos Iniciais",
                "Anos Finais": "Número de Matrículas do Ensino Fundamental - Anos Finais"
            },
            "series": {
                "Anos Iniciais": {
                    "1º Ano": "Número de Matrículas do Ensino Fundamental - Anos Iniciais - 1º Ano",
                    "2º Ano": "Número de Matrículas do Ensino Fundamental - Anos Iniciais - 2º Ano",
                    "3º Ano": "Número de Matrículas do Ensino Fundamental - Anos Iniciais - 3º Ano",
                    "4º Ano": "Número de Matrículas do Ensino Fundamental - Anos Iniciais - 4º Ano",
                    "5º Ano": "Número de Matrículas do Ensino Fundamental - Anos Iniciais - 5º Ano"
                },
                "Anos Finais": {
                    "6º Ano": "Número de Matrículas do Ensino Fundamental - Anos Finais - 6º Ano",
                    "7º Ano": "Número de Matrículas do Ensino Fundamental - Anos Finais - 7º Ano",
                    "8º Ano": "Número de Matrículas do Ensino Fundamental - Anos Finais - 8º Ano",
                    "9º Ano": "Número de Matrículas do Ensino Fundamental - Anos Finais - 9º Ano"
                }
            }
        },
        "Ensino Médio": {
            "coluna_principal": "Número de Matrículas do Ensino Médio",
            "subetapas": {
                "Propedêutico": "Número de Matrículas do Ensino Médio - Propedêutico",
                "Curso Técnico Integrado": "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional",
                "Normal/Magistério": "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério"
            },
            "series": {
                "Propedêutico": {
                    "1ª Série": "Número de Matrículas do Ensino Médio - Propedêutico - 1º ano/1ª Série",
                    "2ª Série": "Número de Matrículas do Ensino Médio - Propedêutico - 2º ano/2ª Série",
                    "3ª Série": "Número de Matrículas do Ensino Médio - Propedêutico - 3º ano/3ª Série",
                    "4ª Série": "Número de Matrículas do Ensino Médio - Propedêutico - 4º ano/4ª Série",
                    "Não Seriado": "Número de Matrículas do Ensino Médio - Propedêutico - Não Seriado"
                },
                "Curso Técnico Integrado": {
                    "1ª Série": "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 1º ano/1ª Série",
                    "2ª Série": "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 2º ano/2ª Série",
                    "3ª Série": "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 3º ano/3ª Série",
                    "4ª Série": "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 4º ano/4ª Série",
                    "Não Seriado": "Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - Não Seriado"
                },
                "Normal/Magistério": {
                    "1ª Série": "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 1º ano/1ª Série",
                    "2ª Série": "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 2º ano/2ª Série",
                    "3ª Série": "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 3º ano/3ª Série",
                    "4ª Série": "Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 4º ano/4ª Série"
                }
            }
        },
        "EJA": {
            "coluna_principal": "Número de Matrículas da Educação de Jovens e Adultos (EJA)",
            "subetapas": {
                "Ensino Fundamental": "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental",
                "Ensino Médio": "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Médio"
            },
            "series": {
                "Ensino Fundamental": {
                    "Anos Iniciais": "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Iniciais",
                    "Anos Finais": "Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Finais"
                }
            }
        },
        "Educação Profissional": {
            "coluna_principal": "Número de Matrículas da Educação Profissional",
            "subetapas": {
                "Técnica": "Número de Matrículas da Educação Profissional Técnica",
                "Curso FIC": "Número de Matrículas da Educação Profissional - Curso FIC Concomitante"
            },
            "series": {
                "Técnica": {
                    "Concomitante": "Número de Matrículas da Educação Profissional Técnica - Curso Técnico Concomitante",
                    "Subsequente": "Número de Matrículas da Educação Profissional Técnica - Curso Técnico Subsequente"
                }
            }
        }
    }
    
    return mapeamento

# Primeira seleção do DataFrame
tipo_visualizacao = "Estado"  # Valor padrão
df = estado_df  # DataFrame padrão para iniciar

# Agora crie o mapeamento de colunas usando o DataFrame inicial
mapeamento_colunas = criar_mapeamento_colunas(df)

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

# Filtro do Ano
anos_disponiveis = sorted(df["ANO"].unique())
ano_selecionado = st.sidebar.selectbox("Ano do Censo:", anos_disponiveis)

# Filtro da DEPENDENCIA ADMINISTRATIVA
dependencias_disponiveis = sorted(df["DEPENDENCIA ADMINISTRATIVA"].unique())
dependencia_selecionada = st.sidebar.multiselect(
    "DEPENDENCIA ADMINISTRATIVA:",
    dependencias_disponiveis,
    default=dependencias_disponiveis
)

# Filtro da Etapa de Ensino
etapas_disponiveis = list(mapeamento_colunas.keys())
etapa_selecionada = st.sidebar.selectbox(
    "Etapa de Ensino:",
    etapas_disponiveis
)

# Filtro da Subetapa (varia de acordo com a etapa selecionada)
subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
subetapa_selecionada = st.sidebar.selectbox(
    "Subetapa:",
    ["Todas"] + subetapas_disponiveis
)

# Filtro para a Série, se aplicável à subetapa selecionada
series_disponiveis = []
if subetapa_selecionada != "Todas" and subetapa_selecionada in mapeamento_colunas[etapa_selecionada]["series"]:
    series_disponiveis = list(mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada].keys())
    serie_selecionada = st.sidebar.selectbox(
        "Série:",
        ["Todas"] + series_disponiveis
    )
else:
    serie_selecionada = "Todas"

# -------------------------------
# Aplicação dos Filtros nos Dados
# -------------------------------
df_filtrado = df[df["ANO"] == ano_selecionado]

if dependencia_selecionada:
    df_filtrado = df_filtrado[df_filtrado["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]

# Determinar a coluna de dados com base na etapa, subetapa e série selecionadas
if subetapa_selecionada == "Todas":
    coluna_dados = mapeamento_colunas[etapa_selecionada]["coluna_principal"]
elif serie_selecionada == "Todas" or subetapa_selecionada not in mapeamento_colunas[etapa_selecionada]["series"]:
    coluna_dados = mapeamento_colunas[etapa_selecionada]["subetapas"][subetapa_selecionada]
else:
    if serie_selecionada in mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada]:
        coluna_dados = mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada][serie_selecionada]
    else:
        coluna_dados = mapeamento_colunas[etapa_selecionada]["subetapas"][subetapa_selecionada]

# -------------------------------
# Cabeçalho e Informações Iniciais do Dashboard
# -------------------------------
st.title("Dashboard de Matrículas - Inep")
st.markdown(f"**Visualização por {tipo_visualizacao} - Ano: {ano_selecionado}**")

# Exibição dos filtros selecionados
filtro_texto = f"**Etapa:** {etapa_selecionada}"
if subetapa_selecionada != "Todas":
    filtro_texto += f" | **Subetapa:** {subetapa_selecionada}"
    if serie_selecionada != "Todas" and serie_selecionada in series_disponiveis:
        filtro_texto += f" | **Série:** {serie_selecionada}"
st.markdown(filtro_texto)

# Verifica se a coluna de dados existe; se não, usa a coluna principal
if coluna_dados not in df_filtrado.columns:
    st.warning(f"A coluna {coluna_dados} não está disponível nos dados.")
    coluna_dados = mapeamento_colunas[etapa_selecionada]["coluna_principal"]
    if coluna_dados not in df_filtrado.columns:
        st.error("Não foi possível encontrar dados para a etapa selecionada.")
        st.stop()

# -------------------------------
# Seção de Indicadores (KPIs)
# -------------------------------
col1, col2, col3 = st.columns(3)

# KPI 1: Total de Matrículas na etapa/subetapa/série selecionada
total_matriculas = df_filtrado[coluna_dados].sum()
with col1:
    st.metric("Total de Matrículas", formatar_numero(total_matriculas))

# KPI 2: Média de Matrículas
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

# KPI 3: Indicador adicional conforme a visualização
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
# Seção de Gráficos
# -------------------------------
st.markdown("## Análise Gráfica")

# Gráfico 1: Distribuição de Matrículas por DEPENDENCIA ADMINISTRATIVA (Gráfico de Pizza)
fig1 = px.pie(
    df_filtrado, 
    names="DEPENDENCIA ADMINISTRATIVA", 
    values=coluna_dados,
    title="Distribuição de Matrículas por DEPENDENCIA ADMINISTRATIVA",
    color_discrete_sequence=px.colors.qualitative.Set3
)
st.plotly_chart(fig1, use_container_width=True)

# Gráfico 2: Varia conforme o nível de visualização
if tipo_visualizacao == "Estado":
    # Para visualização estadual, comparar matrículas entre diferentes anos
    anos_df = df[df["DEPENDENCIA ADMINISTRATIVA"].isin(dependencia_selecionada)]
    dados_anos = []
    for ano in anos_disponiveis:
        ano_data = anos_df[anos_df["ANO"] == ano]
        if not ano_data.empty and coluna_dados in ano_data.columns:
            dados_anos.append({
                "Ano": ano,
                "Matrículas": ano_data[coluna_dados].sum()
            })
    if dados_anos:
        anos_chart_df = pd.DataFrame(dados_anos)
        fig2 = px.line(
            anos_chart_df, 
            x="Ano", 
            y="Matrículas", 
            title="Evolução de Matrículas ao Longo dos Anos",
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)
    
elif tipo_visualizacao == "Município":
    # Para visualização municipal, mostrar os 10 municípios com maior número de matrículas
    top_municipios = df_filtrado.nlargest(10, coluna_dados)
    if not top_municipios.empty:
        fig2 = px.bar(
            top_municipios, 
            x="NOME DO MUNICIPIO", 
            y=coluna_dados,
            title="Top 10 Municípios por Número de Matrículas",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig2, use_container_width=True)
        
else:  # Visualização por Escola
    top_escolas = df_filtrado.nlargest(10, coluna_dados)
    if not top_escolas.empty:
        # Gerar nomes curtos para facilitar a visualização no gráfico
        top_escolas["Nome Curto"] = top_escolas["NOME DA ESCOLA"].apply(
            lambda x: x[:30] + "..." if len(x) > 30 else x
        )
        fig2 = px.bar(
            top_escolas, 
            x="Nome Curto", 
            y=coluna_dados,
            title="Top 10 Escolas por Número de Matrículas",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig2.update_xaxes(tickangle=45)
        st.plotly_chart(fig2, use_container_width=True)

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown("## Dados Detalhados")

# Seleção das colunas a serem exibidas na tabela, conforme o nível de visualização
if tipo_visualizacao == "Escola":
    colunas_tabela = ["NOME DA ESCOLA", "DEPENDENCIA ADMINISTRATIVA", "NOME DO MUNICIPIO"]
elif tipo_visualizacao == "Município":
    colunas_tabela = ["NOME DO MUNICIPIO", "DEPENDENCIA ADMINISTRATIVA"]
else:  # Estado
    colunas_tabela = ["NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]

# Adiciona a coluna de dados selecionada ao final
colunas_tabela.append(coluna_dados)

# Verifica se todas as colunas estão presentes no DataFrame filtrado
colunas_existentes = [col for col in colunas_tabela if col in df_filtrado.columns]
if set(colunas_existentes) != set(colunas_tabela):
    st.warning(f"Algumas colunas não estão disponíveis para exibição na tabela: {set(colunas_tabela) - set(colunas_existentes)}")
    colunas_tabela = colunas_existentes

# Converter a coluna de dados para numérico para ordenação correta
df_filtrado_tabela = df_filtrado.copy()
if coluna_dados in df_filtrado_tabela.columns:
    df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')
    tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
else:
    tabela_dados = df_filtrado_tabela[colunas_existentes]

st.dataframe(tabela_dados, use_container_width=True)

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown("**Nota:** Os dados são provenientes do Censo Escolar. Os traços (-) indicam ausência de dados.")
