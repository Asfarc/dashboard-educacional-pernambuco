# Bibliotecas padrão
import pandas as pd
import streamlit as st
import os
import io
import numpy as np
import plotly.express as px  # Se estiver usando para visualizações

# Módulos refatorados - Configuração
from config import configurar_pagina

# Módulos refatorados - Constantes
from constantes import *  # Importa todas as constantes

# Módulos refatorados - Utilitários
from utils.formatacao import formatar_numero
from utils.carregamento import carregar_dados
from utils.exportacao import converter_df_para_csv, converter_df_para_excel

# Módulos refatorados - Componentes
from componentes.navegacao import navegar_tabela
from componentes.tabelas import adicionar_linha_totais, exibir_tabela_com_aggrid

# Módulos refatorados - Processamento
from processamento.mapeamento import (
    carregar_mapeamento_colunas,
    criar_mapeamento_colunas,
    obter_coluna_dados,
    verificar_coluna_existe
)
from processamento.analise import preparar_tabela_para_exibicao, calcular_estatisticas, obter_top_valores

# Configuração inicial
configurar_pagina()
# -------------------------------
# Carregamento de Dados
# -------------------------------
try:
    escolas_df, estado_df, municipio_df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.stop()

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

# Filtro da Subetapa
if "subetapas" in mapeamento_colunas[etapa_selecionada] and mapeamento_colunas[etapa_selecionada]["subetapas"]:
    subetapas_disponiveis = list(mapeamento_colunas[etapa_selecionada]["subetapas"].keys())
    subetapa_selecionada = st.sidebar.selectbox(
        "Subetapa:",
        ["Todas"] + subetapas_disponiveis
    )
else:
    subetapa_selecionada = "Todas"

# Filtro para a Série, se aplicável
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
    coluna_principal = mapeamento_colunas[etapa_selecionada].get("coluna_principal", "")
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
st.title(TITULO_DASHBOARD)
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

colunas_tabela = []
if "ANO" in df_filtrado.columns:
    colunas_tabela.append("ANO")

if tipo_visualizacao == "Escola":
    colunas_adicionais = ["CODIGO DA ESCOLA", "NOME DA ESCOLA", "CODIGO DO MUNICIPIO",
                          "NOME DO MUNICIPIO", "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]
elif tipo_visualizacao == "Município":
    colunas_adicionais = ["CODIGO DO MUNICIPIO", "NOME DO MUNICIPIO",
                          "CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]
else:
    colunas_adicionais = ["CODIGO DA UF", "NOME DA UF", "DEPENDENCIA ADMINISTRATIVA"]

for col in colunas_adicionais:
    if col in df_filtrado.columns:
        colunas_tabela.append(col)

if coluna_dados in df_filtrado.columns:
    colunas_tabela.append(coluna_dados)

colunas_existentes = [col for col in colunas_tabela if col in df_filtrado.columns]
colunas_tabela = colunas_existentes

if coluna_dados in df_filtrado.columns:
    with pd.option_context('mode.chained_assignment', None):
        df_filtrado_tabela = df_filtrado[colunas_tabela].copy()
        df_filtrado_tabela[coluna_dados] = pd.to_numeric(df_filtrado_tabela[coluna_dados], errors='coerce')

    total = df_filtrado_tabela[coluna_dados].sum()
    if total > 0:
        with pd.option_context('mode.chained_assignment', None):
            df_filtrado_tabela['% do Total'] = df_filtrado_tabela[coluna_dados].apply(
                lambda x: (x / total) * 100 if pd.notnull(x) else None
            )
        colunas_tabela.append('% do Total')

    tabela_dados = df_filtrado_tabela.sort_values(by=coluna_dados, ascending=False)
    tabela_exibicao = tabela_dados.copy()

    with pd.option_context('mode.chained_assignment', None):
        tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
            lambda x: formatar_numero(x) if pd.notnull(x) else "-"
        )
        if '% do Total' in tabela_exibicao.columns:
            tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
                lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
            )
else:
    tabela_dados = df_filtrado[colunas_existentes].copy()
    tabela_exibicao = tabela_dados.copy()

tab1, tab2 = st.tabs(["Visão Tabular", "Resumo Estatístico"])

with tab1:
    st.write("### Configurações de exibição")
    col1, col2, col3, col4 = st.columns(4)

    with col4:
        altura_personalizada = st.checkbox(ROTULO_AJUSTAR_ALTURA, value=False, help=DICA_ALTURA_TABELA)
        if altura_personalizada:
            altura_manual = st.slider("Altura da tabela (pixels)",
                                      min_value=200,
                                      max_value=1000,
                                      value=600,
                                      step=50)
        else:
            altura_manual = 600

    with col1:
        total_registros = len(tabela_exibicao)
        mostrar_todos = st.checkbox(ROTULO_MOSTRAR_REGISTROS, value=True)

    with col2:
        st.write(" ")
    with col3:
        modo_desempenho = st.checkbox(ROTULO_MODO_DESEMPENHO, value=True,
                                      help=DICA_MODO_DESEMPENHO)

    st.write("### Filtros da tabela")
    col5, col6 = st.columns([1, 5])

    with col5:
        st.write("**Colunas:**")
    with col6:
        todas_colunas = [col for col in df_filtrado.columns if col not in colunas_tabela]
        if todas_colunas:
            colunas_adicionais = st.multiselect(
                "Colunas adicionais",
                todas_colunas,
                label_visibility="collapsed",
                placeholder="Selecionar colunas adicionais..."
            )
            if colunas_adicionais:
                colunas_tabela.extend(colunas_adicionais)
                try:
                    tabela_dados = df_filtrado_tabela[colunas_tabela].sort_values(by=coluna_dados, ascending=False)
                    tabela_exibicao = tabela_dados.copy()
                    with pd.option_context('mode.chained_assignment', None):
                        if coluna_dados in tabela_exibicao.columns:
                            tabela_exibicao[coluna_dados] = tabela_exibicao[coluna_dados].apply(
                                lambda x: formatar_numero(x) if pd.notnull(x) else "-"
                            )
                        if '% do Total' in tabela_exibicao.columns:
                            tabela_exibicao['% do Total'] = tabela_exibicao['% do Total'].apply(
                                lambda x: f"{x:.2f}%" if pd.notnull(x) else "-"
                            )
                except Exception as e:
                    st.error(f"Erro ao adicionar colunas: {str(e)}")
        else:
            st.write("Não há colunas adicionais disponíveis")

    tabela_filtrada = tabela_exibicao.copy()

    if len(tabela_exibicao) > 1000:
        col_filtrar = st.columns([1])[0]
        with col_filtrar:
            aplicar_filtros = st.button("Aplicar Filtros", type="primary")
        mostrar_dica = True
    else:
        aplicar_filtros = True
        mostrar_dica = False

    try:
        tabela_com_totais = adicionar_linha_totais(tabela_filtrada, coluna_dados)
    except Exception as e:
        st.warning(f"Não foi possível adicionar a linha de totais: {str(e)}")
        tabela_com_totais = tabela_filtrada

    altura_tabela = altura_manual
    try:
        grid_result = exibir_tabela_com_aggrid(tabela_com_totais, altura=altura_tabela, coluna_dados=coluna_dados)
    except Exception as e:
        st.error(f"Erro ao exibir tabela no AgGrid: {str(e)}")
        st.dataframe(tabela_com_totais, height=altura_tabela)

    col1, col2 = st.columns(2)
    with col1:
        try:
            csv_data = converter_df_para_csv(tabela_dados)
            st.download_button(
                label=ROTULO_BTN_DOWNLOAD_CSV,
                data=csv_data,
                file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.csv',
                mime='text/csv',
            )
        except Exception as e:
            st.error(f"Erro ao preparar CSV para download: {str(e)}")

    with col2:
        try:
            excel_data = converter_df_para_excel(tabela_dados)
            st.download_button(
                label=ROTULO_BTN_DOWNLOAD_EXCEL,
                data=excel_data,
                file_name=f'dados_{etapa_selecionada.replace(" ", "_")}_{ano_selecionado}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        except Exception as e:
            st.error(f"Erro ao preparar Excel para download: {str(e)}")

with tab2:
    if coluna_dados in tabela_dados.columns:
        col1, col2 = st.columns(2)

        with col1:
            try:
                # Usar a função refatorada
                resumo = calcular_estatisticas(tabela_dados, coluna_dados)

                st.write("### Resumo Estatístico")
                resumo_estilizado = resumo.style.set_properties(**{'text-align': 'center'}) \
                    .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                st.dataframe(resumo_estilizado, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Erro ao calcular estatísticas: {str(e)}")
                st.write("Não foi possível calcular as estatísticas para os dados atuais.")

        with col2:
            try:
                st.write("### Top 5 Valores")
                if len(tabela_dados) > 0:
                    try:
                        # Usar a função refatorada
                        top5_exibir = obter_top_valores(tabela_dados, coluna_dados, n=5,
                                                        tipo_visualizacao=tipo_visualizacao)

                        if not top5_exibir.empty:
                            top5_estilizado = top5_exibir.style.set_properties(**{'text-align': 'center'}) \
                                .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                            st.dataframe(top5_estilizado, use_container_width=True, hide_index=True)
                        else:
                            st.info(INFO_SEM_COLUNAS_TOP5)
                    except Exception as e:
                        st.error(ERRO_CALCULAR_TOP5.format(str(e)))
                        st.info(INFO_NAO_CALCULADO_TOP5)
                else:
                    st.info(INFO_SEM_DADOS_TOP5)
            except Exception as e:
                st.error(f"Erro ao processar top 5: {str(e)}")
    else:
        st.warning(AVISO_COLUNA_NAO_DISPONIVEL.format(coluna_dados))

# -------------------------------
# Rodapé do Dashboard
# -------------------------------
st.markdown("---")
st.markdown(RODAPE_NOTA)