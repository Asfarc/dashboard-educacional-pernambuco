import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

###############################################################
# SEÇÃO 1: CONFIGURAÇÃO INICIAL E FUNÇÕES DE CARREGAMENTO
###############################################################

# Configuração da página
st.set_page_config(
    page_title="Dashboard Indicadores Educacionais - Pernambuco",
    layout="wide",                  # Layout amplo da página
    initial_sidebar_state="expanded"  # Sidebar inicialmente expandida
)

# Função para carregar e processar os dados
@st.cache_data  # Esta anotação armazena em cache os dados para melhor performance
def load_data():
    # Caminho do arquivo que contém os dados
    file_path = "Apresentação.xlsx"

    # Carregar planilha de indicadores (com configuração para formato decimal brasileiro)
    df_indicadores = pd.read_excel(file_path, sheet_name="Indicadores", decimal=',')

    # Carregar planilha de distribuição
    df_distribuicao = pd.read_excel(file_path, sheet_name="Distribuição", decimal=',')

    # Mapeamento de indicadores para suas respectivas categorias
    categorias = {
        '1A': 'Educação Infantil',
        '1B': 'Educação Infantil',
        '2A': 'Ensino Fundamental',
        '6A': 'Tempo Integral',
        '6B': 'Tempo Integral',
        '15A': 'Formação Docente',
        '15B': 'Formação Docente',
        '15C': 'Formação Docente'
    }

    # Adicionar coluna de categorias baseada no mapeamento acima
    df_indicadores['Categoria'] = df_indicadores['Indicadores'].map(categorias)

    # Converter percentuais para escala 0-100 se estiverem em escala 0-1
    if df_indicadores['Resultado 2023 (média)'].max() <= 1:
        df_indicadores['Meta PEE-PE'] = df_indicadores['Meta PEE-PE'] * 100
        df_indicadores['Resultado 2023 (média)'] = df_indicadores['Resultado 2023 (média)'] * 100

    # Calcular nível de cumprimento para cada indicador
    df_indicadores['Nível de Cumprimento'] = df_indicadores.apply(
        lambda row: classificar_cumprimento(row), axis=1
    )

    # Transformar dados de distribuição para formato longo (melhor para visualização)
    df_dist_long = pd.melt(
        df_distribuicao,
        id_vars=['Faixas Percentuais'],
        var_name='Indicador',
        value_name='Quantidade de Municípios'
    )

    return df_indicadores, df_distribuicao, df_dist_long


# Função para classificar o nível de cumprimento das metas
def classificar_cumprimento(row):
    resultado = row['Resultado 2023 (média)']
    meta = row['Meta PEE-PE']
    # Calcular percentual de cumprimento em relação à meta
    percentual = (resultado / meta) * 100 if meta > 0 else 0

    # Classificar com base no percentual calculado
    if percentual >= 90:
        return 'Alto (≥90%)'
    elif percentual >= 70:
        return 'Médio (70-89%)'
    elif percentual >= 50:
        return 'Baixo (50-69%)'
    else:
        return 'Crítico (<50%)'


###############################################################
# SEÇÃO 2: CARREGAMENTO DE DADOS E TÍTULO PRINCIPAL
###############################################################

# Carregar dados usando a função definida anteriormente
df_indicadores, df_distribuicao, df_dist_long = load_data()

# Título principal do dashboard
st.title("🎓 Dashboard de Indicadores Educacionais - Pernambuco")
st.markdown("""
Esta dashboard interativa permite explorar os indicadores educacionais de Pernambuco,
incluindo as metas do PEE-PE, resultados de 2023 e a distribuição dos municípios por faixa percentual.
""")


###############################################################
# SEÇÃO 3: CONFIGURAÇÃO DE FILTROS NA BARRA LATERAL
###############################################################

# Cabeçalho da barra lateral
st.sidebar.header("Filtros")

# Filtro por categoria
categorias = sorted(df_indicadores['Categoria'].unique())
categoria_selecionada = st.sidebar.multiselect(
    "Selecione a categoria:",
    options=categorias,
    default=categorias  # Todas as categorias selecionadas por padrão
)

# Filtro por indicador (baseado nas categorias selecionadas)
indicadores_disponiveis = sorted(
    df_indicadores[df_indicadores['Categoria'].isin(categoria_selecionada)]['Indicadores'].unique())
indicador_selecionado = st.sidebar.multiselect(
    "Selecione o indicador:",
    options=indicadores_disponiveis,
    default=indicadores_disponiveis  # Todos os indicadores selecionados por padrão
)

# Aplicar filtros aos dados
df_filtrado = df_indicadores[
    df_indicadores['Categoria'].isin(categoria_selecionada) &
    df_indicadores['Indicadores'].isin(indicador_selecionado)
]


###############################################################
# SEÇÃO 4: MÉTRICAS RESUMIDAS
###############################################################

st.header("Visão Geral dos Indicadores")

# Criar 4 colunas para exibir métricas resumidas
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Métrica 1: Média dos resultados de 2023
    media_total = df_filtrado['Resultado 2023 (média)'].mean()
    st.metric("Média de Resultados", f"{media_total:.1f}%")

with col2:
    # Métrica 2: Média das metas estabelecidas
    media_metas = df_filtrado['Meta PEE-PE'].mean()
    st.metric("Média das Metas", f"{media_metas:.1f}%")

with col3:
    # Métrica 3: Diferença média entre meta e resultado (gap)
    gap_medio = (df_filtrado['Meta PEE-PE'] - df_filtrado['Resultado 2023 (média)']).mean()
    st.metric("Gap Médio", f"{gap_medio:.1f}%")

with col4:
    # Métrica 4: Percentual médio de cumprimento das metas
    perc_cumprimento = (df_filtrado['Resultado 2023 (média)'] / df_filtrado['Meta PEE-PE'] * 100).mean()
    st.metric("% Médio de Cumprimento", f"{perc_cumprimento:.1f}%")


###############################################################
# SEÇÃO 5: GRÁFICO PRINCIPAL - COMPARATIVO RESULTADO VS META
###############################################################

st.subheader("Comparativo: Resultado vs. Meta")

# Criar figura para o gráfico
fig = go.Figure()

# Adicionar barras para os resultados de 2023
fig.add_trace(go.Bar(
    x=df_filtrado['Indicadores'],
    y=df_filtrado['Resultado 2023 (média)'],
    name='Resultado 2023',
    marker_color='royalblue',  # Cor das barras
    text=df_filtrado['Resultado 2023 (média)'].apply(lambda x: f"{x:.1f}%"),  # Texto nas barras
    textposition='auto'  # Posicionamento automático do texto
))

# Adicionar linhas para as metas
fig.add_trace(go.Scatter(
    x=df_filtrado['Indicadores'],
    y=df_filtrado['Meta PEE-PE'],
    name='Meta PEE-PE',
    mode='lines+markers',  # Exibir como linha com marcadores
    line=dict(color='firebrick', width=3, dash='dash'),  # Estilo da linha
    marker=dict(size=10)  # Tamanho dos marcadores
))

# Configurar layout do gráfico
fig.update_layout(
    title='Comparativo entre Resultados 2023 e Metas do PEE-PE',
    xaxis_title='Indicador',
    yaxis_title='Percentual (%)',
    yaxis=dict(range=[0, 105]),  # Intervalo do eixo Y
    barmode='group',
    height=500
)

# Exibir o gráfico
st.plotly_chart(fig, use_container_width=True)


###############################################################
# SEÇÃO 6: DISTRIBUIÇÃO POR FAIXA PERCENTUAL
###############################################################

st.header("Distribuição dos Municípios por Faixa Percentual")

# Definir paleta de cores para as categorias
paleta_categorias = {
    'Educação Infantil': '#3498db',
    'Ensino Fundamental': '#2ecc71',
    'Tempo Integral': '#e74c3c',
    'Formação Docente': '#9b59b6'
}

# Filtrar dados de distribuição conforme indicadores selecionados
df_dist_filtered = df_dist_long[df_dist_long['Indicador'].isin(indicador_selecionado)]

# Criar colunas para controlar a largura (proporção 1:10:1)
col1, col2, col3 = st.columns([1, 10, 1])

# Para cada indicador selecionado, criar um gráfico separado
for indicador in indicador_selecionado:
    # Filtrar dados para este indicador específico
    df_indicador = df_dist_filtered[df_dist_filtered['Indicador'] == indicador]
    
    # Determinar a cor com base na categoria do indicador
    categoria_do_indicador = df_indicadores[df_indicadores['Indicadores'] == indicador]['Categoria'].iloc[0]
    cor_do_indicador = paleta_categorias.get(categoria_do_indicador, '#3498db')  # cor padrão se não encontrar
    
    # Criar gráfico de barras horizontais para este indicador
    fig_ind = go.Figure()
    
    # Adicionar barras horizontais
    fig_ind.add_trace(go.Bar(
        y=df_indicador['Faixas Percentuais'],
        x=df_indicador['Quantidade de Municípios'],
        orientation='h',  # Orientação horizontal
        marker_color=cor_do_indicador,
        text=df_indicador['Quantidade de Municípios'],  # Mostrar valor em cada barra
        textposition='outside',  # Texto fora da barra
        name=indicador
    ))
    
    # Configurar layout
    fig_ind.update_layout(
        title=f'Distribuição dos Municípios por Faixa - Indicador {indicador}',
        yaxis_title='Faixa Percentual',
        xaxis_title='Número de Municípios',
        height=400,
        width=900,  # Largura explícita
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis={'categoryorder': 'array', 
               'categoryarray': df_distribuicao['Faixas Percentuais'].tolist()[::-1]}  # Inverter ordem
    )
    
    # Exibir o gráfico na coluna do meio
    with col2:
        st.plotly_chart(fig_ind, use_container_width=True)


###############################################################
# SEÇÃO 7: HEATMAP DE DISTRIBUIÇÃO
###############################################################

st.subheader("Heatmap de Distribuição")

# Preparar dados para o heatmap (transformar em matriz)
pivot_data = df_dist_filtered.pivot(
    index='Indicador',
    columns='Faixas Percentuais',
    values='Quantidade de Municípios'
).fillna(0)  # Preencher valores ausentes com 0

# Criar heatmap
fig_heatmap = px.imshow(
    pivot_data,
    labels=dict(x="Faixa Percentual", y="Indicador", color="Número de Municípios"),
    x=pivot_data.columns,
    y=pivot_data.index,
    color_continuous_scale="Viridis",  # Escala de cores
    aspect="auto",
    text_auto=True  # Mostrar valores nas células
)

# Ajustar layout
fig_heatmap.update_layout(
    height=400,
    xaxis={'side': 'bottom'}
)

# Exibir o heatmap
st.plotly_chart(fig_heatmap, use_container_width=True)


###############################################################
# SEÇÃO 8: ANÁLISE POR CATEGORIA
###############################################################

st.header("Análise por Categoria")

# Criar DataFrame para estatísticas por categoria
stats_por_categoria = pd.DataFrame()
stats_por_categoria['Categoria'] = df_indicadores['Categoria'].unique()

# Calcular as estatísticas para cada categoria
for categoria in stats_por_categoria['Categoria']:
    # Filtrar dados para esta categoria
    df_cat = df_indicadores[df_indicadores['Categoria'] == categoria]

    # Média dos resultados
    media_resultado = df_cat['Resultado 2023 (média)'].mean()

    # Média das metas
    media_meta = df_cat['Meta PEE-PE'].mean()

    # Gap médio
    gap_medio = media_meta - media_resultado

    # Percentual de cumprimento
    percentual_cumprimento = (media_resultado / media_meta * 100) if media_meta > 0 else 0

    # Adicionar estatísticas ao dataframe
    stats_por_categoria.loc[
        stats_por_categoria['Categoria'] == categoria, 'Média dos Resultados'] = f"{media_resultado:.1f}%"
    stats_por_categoria.loc[
        stats_por_categoria['Categoria'] == categoria, 'Média das Metas'] = f"{media_meta:.1f}%"
    stats_por_categoria.loc[
        stats_por_categoria['Categoria'] == categoria, 'Gap Médio'] = f"{gap_medio:.1f}%"
    stats_por_categoria.loc[
        stats_por_categoria['Categoria'] == categoria, '% de Cumprimento'] = f"{percentual_cumprimento:.1f}%"

# Exibir tabela de estatísticas
st.dataframe(stats_por_categoria, use_container_width=True)


###############################################################
# SEÇÃO 9: GRÁFICO DE RADAR POR CATEGORIA
###############################################################

st.subheader("Radar de Desempenho por Categoria")

# Preparar dados para o radar - Resultados
radar_data = pd.DataFrame()
radar_data['Categoria'] = df_indicadores['Categoria'].unique()
radar_data['Resultado 2023 (média)'] = [
    df_indicadores[df_indicadores['Categoria'] == cat]['Resultado 2023 (média)'].mean()
    for cat in radar_data['Categoria']]

# Preparar dados para o radar - Metas
radar_meta = pd.DataFrame()
radar_meta['Categoria'] = df_indicadores['Categoria'].unique()
radar_meta['Meta PEE-PE'] = [
    df_indicadores[df_indicadores['Categoria'] == cat]['Meta PEE-PE'].mean()
    for cat in radar_meta['Categoria']]

# Criar gráfico de radar
fig_radar = go.Figure()

# Adicionar área para resultados
fig_radar.add_trace(go.Scatterpolar(
    r=radar_data['Resultado 2023 (média)'],
    theta=radar_data['Categoria'],
    fill='toself',
    name='Resultado 2023',
    line_color='royalblue'
))

# Adicionar área para metas
fig_radar.add_trace(go.Scatterpolar(
    r=radar_meta['Meta PEE-PE'],
    theta=radar_meta['Categoria'],
    fill='toself',
    name='Meta PEE-PE',
    line_color='firebrick',
    opacity=0.6
))

# Configurar layout do radar
fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]  # Escala de 0 a 100%
        )
    ),
    showlegend=True,
    height=500
)

# Exibir o gráfico de radar
st.plotly_chart(fig_radar, use_container_width=True)


###############################################################
# SEÇÃO 10: EXPORTAÇÃO E DOWNLOAD
###############################################################

# Informações sobre exportação para o Canva
st.header("Exportar Visualizações para o Canva")

st.info("""
Para usar essas visualizações no Canva:
1. Capture os gráficos usando o botão de download em cada visualização (três pontos no canto superior direito)
2. Salve as imagens com boa resolução
3. Importe-as no Canva para criar sua apresentação final
""")

# Opção para download dos dados processados
st.subheader("Download dos Dados Processados")
csv_processed = df_indicadores.to_csv(index=False).encode('utf-8')
st.download_button(
    "📥 Download dos dados processados (CSV)",
    csv_processed,
    "indicadores_processados.csv",
    "text/csv",
    key='download-csv'
)

# Rodapé
st.markdown("---")
st.markdown("Dashboard desenvolvida para análise dos indicadores educacionais de Pernambuco")
