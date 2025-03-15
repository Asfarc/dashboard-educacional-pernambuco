import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from pathlib import Path
import io

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
                "Curso Técnico Integrado": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional"),
                "Normal/Magistério": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério")
            },
            "series": {
                "Propedêutico": {
                    "1ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - 4º ano/4ª Série"),
                    "Não Seriado": obter_coluna_real("Número de Matrículas do Ensino Médio - Propedêutico - Não Seriado")
                },
                "Curso Técnico Integrado": {
                    "1ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - 4º ano/4ª Série"),
                    "Não Seriado": obter_coluna_real("Número de Matrículas do Ensino Médio - Curso Técnico Integrado à Educação Profissional - Não Seriado")
                },
                "Normal/Magistério": {
                    "1ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 1º ano/1ª Série"),
                    "2ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 2º ano/2ª Série"),
                    "3ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 3º ano/3ª Série"),
                    "4ª Série": obter_coluna_real("Número de Matrículas do Ensino Médio - Modalidade Normal/Magistério - 4º ano/4ª Série")
                }
            }
        },
        "EJA": {
            "coluna_principal": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA)"),
            "subetapas": {
                "Ensino Fundamental": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental"),
                "Ensino Médio": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Médio")
            },
            "series": {
                "Ensino Fundamental": {
                    "Anos Iniciais": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Iniciais"),
                    "Anos Finais": obter_coluna_real("Número de Matrículas da Educação de Jovens e Adultos (EJA) - Ensino Fundamental - Anos Finais")
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
                    "Concomitante": obter_coluna_real("Número de Matrículas da Educação Profissional Técnica - Curso Técnico Concomitante"),
                    "Subsequente": obter_coluna_real("Número de Matrículas da Educação Profissional Técnica - Curso Técnico Subsequente")
                }
            }
        }
    }
    
    return mapeamento

# -------------------------------
# Carregamento de Dados
# -------------------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

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
try:
    if subetapa_selecionada == "Todas":
        # Se nenhuma subetapa for selecionada, use a coluna principal da etapa
        coluna_dados = mapeamento_colunas[etapa_selecionada]["coluna_principal"]
    elif serie_selecionada == "Todas" or "series" not in mapeamento_colunas[etapa_selecionada] or subetapa_selecionada not in mapeamento_colunas[etapa_selecionada].get("series", {}):
        # Se nenhuma série for selecionada ou a subetapa não tiver séries, use a coluna da subetapa
        coluna_dados = mapeamento_colunas[etapa_selecionada]["subetapas"][subetapa_selecionada]
    else:
        # Se uma série específica for selecionada, verifique se ela existe
        if serie_selecionada in mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada]:
            coluna_dados = mapeamento_colunas[etapa_selecionada]["series"][subetapa_selecionada][serie_selecionada]
        else:
            # Caso contrário, use a coluna da subetapa
            coluna_dados = mapeamento_colunas[etapa_selecionada]["subetapas"][subetapa_selecionada]
except KeyError as e:
    st.error(f"Erro ao acessar as informações de mapeamento: {e}")
    # Fallback para a coluna principal se houver erro
    coluna_dados = mapeamento_colunas[etapa_selecionada].get("coluna_principal", "")

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

# Verifica se a coluna de dados existe; se não, tenta encontrar uma coluna similar
if coluna_dados not in df_filtrado.columns:
    # Tenta verificar se há uma versão case-insensitive da coluna
    coluna_normalizada = coluna_dados.lower().strip()
    colunas_normalizadas = {col.lower().strip(): col for col in df_filtrado.columns}
    
    if coluna_normalizada in colunas_normalizadas:
        coluna_dados_original = coluna_dados
        coluna_dados = colunas_normalizadas[coluna_normalizada]
        st.info(f"Usando coluna '{coluna_dados}' em vez de '{coluna_dados_original}'")
    else:
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
if "DEPENDENCIA ADMINISTRATIVA" in df_filtrado.columns:
    fig1 = px.pie(
        df_filtrado, 
        names="DEPENDENCIA ADMINISTRATIVA", 
        values=coluna_dados,
        title="Distribuição de Matrículas por DEPENDENCIA ADMINISTRATIVA",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("Não foi possível criar o gráfico de distribuição por DEPENDENCIA ADMINISTRATIVA")

# -------------------------------
# Seção de Tabela de Dados Detalhados
# -------------------------------
st.markdown("## Dados Detalhados")

# Seleção das colunas a serem exibidas na tabela, conforme o nível de visualização
if tipo_visualizacao == "Escola":
    colunas_tabela = ["CODIGO DA ESCOLA", "NOME DA ESCOLA", "CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]
elif tipo_visualizacao == "Município":
    colunas_tabela = ["CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]
else:  # Estado
    colunas_tabela = ["CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]

# Adiciona a coluna de dados selecionada ao final
colunas_tabela.append(coluna_dados)

# Verifica se todas as colunas estão presentes no DataFrame filtrado
colunas_existentes = [col for col in colunas_tabela if col in df_filtrado.columns]
if set(colunas_existentes) != set(colunas_tabela):
    st.warning(f"Algumas colunas não estão disponíveis para exibição na tabela: {set(colunas_tabela) - set(colunas_existentes)}")
    colunas_tabela = colunas_existentes

# Permitir que o usuário selecione colunas adicionais para exibir
todas_colunas = [col for col in df_filtrado.columns if col not in colunas_tabela]
if todas_colunas:
    with st.expander("Selecionar colunas adicionais"):
        colunas_adicionais = st.multiselect(
            "Selecione colunas adicionais para exibir:",
            todas_colunas
        )
        if colunas_adicionais:
            colunas_tabela = colunas_tabela + colunas_adicionais

# Converter a coluna de dados para numérico para ordenação correta
df_filtrado_tabela = df_filtrado.copy()
if coluna_dados in df_filtrado_tabela.columns:
    # Converter para numérico para cálculos e ordenação
    df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')
    
    # Adicionar coluna de percentual
    total = df_filtrado_tabela[coluna_dados].sum()
    if total > 0:
        df_filtrado_tabela['% do Total'] = df_filtrado_tabela[coluna_dados].apply(
            lambda x: (x/total)*100 if pd.notnull(x) else None
        )
        colunas_tabela.append('% do Total')
    
    # Ordenar a tabela pelos valores do coluna_dados em ordem decrescente
    tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
    
    # Criar versão formatada para exibição
    tabela_exibicao = tabela_dados.copy()
    tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
        lambda x: formatar_numero(x) if pd.notnull(x) else "-"
    )
    
    # Formatar a coluna de percentual se existir
    if '% do Total' in tabela_exibicao.columns:
        tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
            lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
        )
else:
    tabela_dados = df_filtrado_tabela[colunas_existentes]
    tabela_exibicao = tabela_dados.copy()

# Adicionar informação sobre o total de registros
st.info(f"Total de {len(tabela_dados)} registros encontrados.")

# Criar abas para diferentes visualizações
tab1, tab2 = st.tabs(["Visão Tabular", "Resumo Estatístico"])

with tab1:
    # Opções de paginação primeiro (para saber quantos registros mostrar)
    st.write("### Configurações de exibição")
    col1, col2 = st.columns(2)
    
    with col1:
        mostrar_todos = st.checkbox("Mostrar todos os registros", value=False)
    
    with col2:
        if not mostrar_todos:
            registros_por_pagina = st.slider(
                "Registros por página:", 
                min_value=10, 
                max_value=500, 
                value=100, 
                step=10
            )
        else:
            registros_por_pagina = len(tabela_exibicao)
    
    # Adicionar filtros de busca mais próximos da tabela e com largura reduzida
    st.write("### Filtros da tabela")
    
    # Usar colunas com largura reduzida (20% da largura original, ou seja, 10% da tela cada)
    col1, col2, col3, col4 = st.columns([1, 9, 1, 9])
    
    # Filtros para texto (nomes de localidades)
    filtro_texto = None
    colunas_localidade = [col for col in ["NOME DA UF", "NOME DO MUNICIPIO", "NOME DA ESCOLA"] if col in tabela_exibicao.columns]
    if colunas_localidade:
        with col1:
            st.write("**Localidade:**")
        with col2:
            coluna_texto_selecionada = st.selectbox("", ["Nenhum"] + colunas_localidade, label_visibility="collapsed")
            if coluna_texto_selecionada != "Nenhum":
                filtro_texto = st.text_input("", placeholder=f"Filtrar {coluna_texto_selecionada}...", label_visibility="collapsed")
    
    # Filtros para códigos (numéricos)
    filtro_codigo = None
    colunas_codigo = [col for col in ["CODIGO DA UF", "CODIGO DO MUNICIPIO", "CODIGO DA ESCOLA"] if col in tabela_exibicao.columns]
    if colunas_codigo:
        with col3:
            st.write("**Código:**")
        with col4:
            coluna_codigo_selecionada = st.selectbox(" ", ["Nenhum"] + colunas_codigo, label_visibility="collapsed")
            if coluna_codigo_selecionada != "Nenhum":
                filtro_codigo = st.text_input(" ", placeholder=f"Filtrar {coluna_codigo_selecionada}...", label_visibility="collapsed")
    
    # Aplicar filtros
    tabela_filtrada = tabela_exibicao.copy()
    
    # Filtros em tempo real conforme o usuário digita
    if filtro_texto and coluna_texto_selecionada != "Nenhum":
        # Para nomes, filtra a partir de 3 caracteres
        if len(filtro_texto) >= 3:
            tabela_filtrada = tabela_filtrada[
                tabela_filtrada[coluna_texto_selecionada].astype(str).str.contains(filtro_texto, case=False, na=False)
            ]
    
    if filtro_codigo and coluna_codigo_selecionada != "Nenhum":
        # Para códigos, filtra a partir do primeiro caractere
        if len(filtro_codigo) >= 1:
            tabela_filtrada = tabela_filtrada[
                tabela_filtrada[coluna_codigo_selecionada].astype(str).str.contains(filtro_codigo, na=False)
            ]
    
    # Cálculo de paginação
    total_paginas = max(1, (len(tabela_filtrada) - 1) // registros_por_pagina + 1)
    
    if not mostrar_todos and total_paginas > 1:
        pagina_atual = st.number_input(
            "Página:", 
            min_value=1, 
            max_value=total_paginas, 
            value=1
        )
        inicio = (pagina_atual - 1) * registros_por_pagina
        fim = min(inicio + registros_por_pagina, len(tabela_filtrada))
        
        # Informação da paginação
        st.write(f"Exibindo registros {inicio+1} a {fim} de {len(tabela_filtrada)}")
        
        # Exibir apenas os registros da página atual
        tabela_para_exibir = tabela_filtrada.iloc[inicio:fim]
    else:
        # Exibir todos os registros
        tabela_para_exibir = tabela_filtrada

    # Calcular a soma para a última linha de totais
    totais = {}
    if coluna_dados in tabela_para_exibir.columns:
        # Converter para numérico para cálculos corretos
        valores_numericos = pd.to_numeric(tabela_dados[coluna_dados].loc[tabela_para_exibir.index], errors='coerce')
        totais[coluna_dados] = formatar_numero(valores_numericos.sum())
    
    if '% do Total' in tabela_para_exibir.columns:
        totais['% do Total'] = "100.00%"
    
    # Adicionar linha de totais
    linha_totais = pd.DataFrame([totais], index=['TOTAL'])
    
    # Preencher as outras colunas com strings vazias
    for col in tabela_para_exibir.columns:
        if col not in totais:
            linha_totais[col] = ""
    
    # Ordenar as colunas para corresponder à tabela principal
    linha_totais = linha_totais[tabela_para_exibir.columns]
    
    # Combinar a tabela principal com a linha de totais
    tabela_com_totais = pd.concat([tabela_para_exibir, linha_totais])
    
    # Aplicar a centralização e outros estilos
    def estilizar_tabela(df):
        # Estilo para centralizar todas as células
        return df.style \
            .set_properties(**{'text-align': 'center'}) \
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center')]},
                {'selector': 'td', 'props': [('text-align', 'center')]},
                # Destacar a linha de totais
                {'selector': 'tr:last-child', 'props': [
                    ('font-weight', 'bold'),
                    ('background-color', '#f0f0f0')
                ]}
            ])
    
    # Exibir a tabela com altura ajustada para mostrar todos os registros sem rolagem
    altura_tabela = min(len(tabela_com_totais) * 35 + 38, 600)  # 35px por linha + 38px para o cabeçalho, máximo de 600px
    
    # Exibir a tabela sem o índice (removendo a primeira coluna)
    tabela_estilizada = estilizar_tabela(tabela_com_totais)
    st.dataframe(tabela_estilizada, use_container_width=True, height=altura_tabela, hide_index=True)
    
    # Mostrar informação atualizada sobre total de registros e matrículas após filtros
    st.markdown(f"""
    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">
        Total após filtros: {len(tabela_para_exibir)} registros | {totais[coluna_dados]} matrículas
    </div>
    """, unsafe_allow_html=True)
    
    # Funções para exportar dados
    def converter_df_para_csv(df):
        return df.to_csv(index=False).encode('utf-8')
    
    def converter_df_para_excel(df):
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        return output.getvalue()
    
    # Botões para download
    col1, col2 = st.columns(2)
    
    with col1:
        # Download como CSV
        st.download_button(
            label="Download CSV",
            data=converter_df_para_csv(tabela_dados.loc[tabela_para_exibir.index]),  # Apenas registros exibidos
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.csv',
            mime='text/csv',
        )
    
    with col2:
        # Download como Excel
        st.download_button(
            label="Download Excel",
            data=converter_df_para_excel(tabela_dados.loc[tabela_para_exibir.index]),  # Apenas registros exibidos
            file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

with tab2:
    # Apresentar um resumo estatístico dos dados
    if coluna_dados in tabela_dados.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Tabela de estatísticas
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
            
            # Estilizar a tabela de resumo
            resumo_estilizado = resumo.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
            
            st.dataframe(resumo_estilizado, use_container_width=True, hide_index=True)
        
        with col2:
            # Top 5 valores
            st.write("### Top 5 Valores")
            top5 = tabela_dados.nlargest(5, coluna_dados)
            
            # Selecionar colunas para exibição
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
            
            # Formatar valores para exibição
            top5_exibir = top5[colunas_exibir].copy()
            if coluna_dados in top5_exibir.columns:
                top5_exibir[coluna_dados] = top5_exibir[coluna_dados].apply(
                    lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                )
            
            if '% do Total' in top5_exibir.columns:
                top5_exibir['% do Total'] = top5_exibir['% do Total'].apply(
                    lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                )
                
            # Estilizar a tabela top5
            top5_estilizado = top5_exibir.style.set_properties(**{'text-align': 'center'}) \
                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
            
            st.dataframe(top5_estilizado, use_container_width=True, hide_index=True)

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown("**Nota:** Os dados são provenientes do Censo Escolar. Os traços (-) indicam ausência de dados.")
