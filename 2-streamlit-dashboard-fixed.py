import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Dashboard Indicadores Educacionais - Pernambuco",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Função para carregar os dados
@st.cache_data
def load_data():
    file_path = "Apresentação.xlsx"

    # Carregar dados de indicadores - adicionando decimal=',' para lidar com o formato brasileiro
    df_indicadores = pd.read_excel(file_path, sheet_name="Indicadores", decimal=',')

    # Carregar dados de distribuição
    df_distribuicao = pd.read_excel(file_path, sheet_name="Distribuição", decimal=',')

    # Adicionar categorias aos indicadores
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

    # Adicionar a coluna de categorias
    df_indicadores['Categoria'] = df_indicadores['Indicadores'].map(categorias)

    # Converter os valores percentuais para escala 0-100 se estiverem em escala 0-1
    if df_indicadores['Resultado 2023 (média)'].max() <= 1:
        df_indicadores['Meta PEE-PE'] = df_indicadores['Meta PEE-PE'] * 100
        df_indicadores['Resultado 2023 (média)'] = df_indicadores['Resultado 2023 (média)'] * 100

    # Calcular nível de cumprimento
    df_indicadores['Nível de Cumprimento'] = df_indicadores.apply(
        lambda row: classificar_cumprimento(row), axis=1
    )

    # Transformar dados de distribuição para formato melhor para visualização
    df_dist_long = pd.melt(
        df_distribuicao,
        id_vars=['Faixas Percentuais'],
        var_name='Indicador',
        value_name='Quantidade de Municípios'
    )

    return df_indicadores, df_distribuicao, df_dist_long


# Função para classificar o nível de cumprimento
def classificar_cumprimento(row):
    resultado = row['Resultado 2023 (média)']
    meta = row['Meta PEE-PE']
    percentual = (resultado / meta) * 100 if meta > 0 else 0

    if percentual >= 90:
        return 'Alto (≥90%)'
    elif percentual >= 70:
        return 'Médio (70-89%)'
    elif percentual >= 50:
        return 'Baixo (50-69%)'
    else:
        return 'Crítico (<50%)'


# Carregar dados
df_indicadores, df_distribuicao, df_dist_long = load_data()

# Título principal
st.title("🎓 Dashboard de Indicadores Educacionais - Pernambuco")
st.markdown("""
Esta dashboard interativa permite explorar os indicadores educacionais de Pernambuco,
incluindo as metas do PEE-PE, resultados de 2023 e a distribuição dos municípios por faixa percentual.
""")

# Sidebar com filtros
st.sidebar.header("Filtros")

# Filtro por categoria
categorias = sorted(df_indicadores['Categoria'].unique())
categoria_selecionada = st.sidebar.multiselect(
    "Selecione a categoria:",
    options=categorias,
    default=categorias
)

# Filtro por indicador
indicadores_disponiveis = sorted(
    df_indicadores[df_indicadores['Categoria'].isin(categoria_selecionada)]['Indicadores'].unique())
indicador_selecionado = st.sidebar.multiselect(
    "Selecione o indicador:",
    options=indicadores_disponiveis,
    default=indicadores_disponiveis
)

# Aplicar filtros
df_filtrado = df_indicadores[
    df_indicadores['Categoria'].isin(categoria_selecionada) &
    df_indicadores['Indicadores'].isin(indicador_selecionado)
    ]

# Layout principal
st.header("Visão Geral dos Indicadores")

# Métricas resumidas
col1, col2, col3, col4 = st.columns(4)

with col1:
    media_total = df_filtrado['Resultado 2023 (média)'].mean()
    st.metric("Média de Resultados", f"{media_total:.1f}%")

with col2:
    media_metas = df_filtrado['Meta PEE-PE'].mean()
    st.metric("Média das Metas", f"{media_metas:.1f}%")

with col3:
    gap_medio = (df_filtrado['Meta PEE-PE'] - df_filtrado['Resultado 2023 (média)']).mean()
    st.metric("Gap Médio", f"{gap_medio:.1f}%")

with col4:
    perc_cumprimento = (df_filtrado['Resultado 2023 (média)'] / df_filtrado['Meta PEE-PE'] * 100).mean()
    st.metric("% Médio de Cumprimento", f"{perc_cumprimento:.1f}%")

# Gráfico principal - Comparativo entre resultado e meta
st.subheader("Comparativo: Resultado vs. Meta")

fig = go.Figure()

# Adicionar barras para resultados
fig.add_trace(go.Bar(
    x=df_filtrado['Indicadores'],
    y=df_filtrado['Resultado 2023 (média)'],
    name='Resultado 2023',
    marker_color='royalblue',
    text=df_filtrado['Resultado 2023 (média)'].apply(lambda x: f"{x:.1f}%"),
    textposition='auto'
))

# Adicionar linhas para metas
fig.add_trace(go.Scatter(
    x=df_filtrado['Indicadores'],
    y=df_filtrado['Meta PEE-PE'],
    name='Meta PEE-PE',
    mode='lines+markers',
    line=dict(color='firebrick', width=3, dash='dash'),
    marker=dict(size=10)
))

# Layout
fig.update_layout(
    title='Comparativo entre Resultados 2023 e Metas do PEE-PE',
    xaxis_title='Indicador',
    yaxis_title='Percentual (%)',
    yaxis=dict(range=[0, 105]),
    barmode='group',
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Segunda linha - Distribuição por faixa percentual
st.header("Distribuição dos Municípios por Faixa Percentual")

# Filtrar dados de distribuição
df_dist_filtered = df_dist_long[df_dist_long['Indicador'].isin(indicador_selecionado)]

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
        orientation='h',
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
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis={'categoryorder': 'array', 
               'categoryarray': df_distribuicao['Faixas Percentuais'].tolist()[::-1]}  # Inverter ordem
    )
    
    # Exibir o gráfico
    st.plotly_chart(fig_ind, use_container_width=True)

# Heatmap
st.subheader("Heatmap de Distribuição")

# Preparar dados para o heatmap
pivot_data = df_dist_filtered.pivot(
    index='Indicador',
    columns='Faixas Percentuais',
    values='Quantidade de Municípios'
).fillna(0)

# Criar heatmap
fig_heatmap = px.imshow(
    pivot_data,
    labels=dict(x="Faixa Percentual", y="Indicador", color="Número de Municípios"),
    x=pivot_data.columns,
    y=pivot_data.index,
    color_continuous_scale="Viridis",
    aspect="auto",
    text_auto=True
)

fig_heatmap.update_layout(
    height=400,
    xaxis={'side': 'bottom'}
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# Análise por categoria
st.header("Análise por Categoria")

# Cálculo de estatísticas por categoria - VERSÃO CORRIGIDA
# Calcular médias manualmente para evitar o erro
stats_por_categoria = pd.DataFrame()
stats_por_categoria['Categoria'] = df_indicadores['Categoria'].unique()

# Calcular as estatísticas para cada categoria
for categoria in stats_por_categoria['Categoria']:
    df_cat = df_indicadores[df_indicadores['Categoria'] == categoria]

    # Média dos resultados
    media_resultado = df_cat['Resultado 2023 (média)'].mean()

    # Média das metas
    media_meta = df_cat['Meta PEE-PE'].mean()

    # Gap médio
    gap_medio = media_meta - media_resultado

    # Percentual de cumprimento
    percentual_cumprimento = (media_resultado / media_meta * 100) if media_meta > 0 else 0

    # Adicionar ao dataframe
    stats_por_categoria.loc[
        stats_por_categoria['Categoria'] == categoria, 'Média dos Resultados'] = f"{media_resultado:.1f}%"
    stats_por_categoria.loc[stats_por_categoria['Categoria'] == categoria, 'Média das Metas'] = f"{media_meta:.1f}%"
    stats_por_categoria.loc[stats_por_categoria['Categoria'] == categoria, 'Gap Médio'] = f"{gap_medio:.1f}%"
    stats_por_categoria.loc[
        stats_por_categoria['Categoria'] == categoria, '% de Cumprimento'] = f"{percentual_cumprimento:.1f}%"

# Exibir tabela
st.dataframe(stats_por_categoria, use_container_width=True)

# Gráfico de radar para as categorias
st.subheader("Radar de Desempenho por Categoria")

# Preparar dados para o radar - VERSÃO CORRIGIDA
radar_data = pd.DataFrame()
radar_data['Categoria'] = df_indicadores['Categoria'].unique()
radar_data['Resultado 2023 (média)'] = [
    df_indicadores[df_indicadores['Categoria'] == cat]['Resultado 2023 (média)'].mean()
    for cat in radar_data['Categoria']]

radar_meta = pd.DataFrame()
radar_meta['Categoria'] = df_indicadores['Categoria'].unique()
radar_meta['Meta PEE-PE'] = [df_indicadores[df_indicadores['Categoria'] == cat]['Meta PEE-PE'].mean()
                             for cat in radar_meta['Categoria']]

# Criar gráfico de radar
fig_radar = go.Figure()

fig_radar.add_trace(go.Scatterpolar(
    r=radar_data['Resultado 2023 (média)'],
    theta=radar_data['Categoria'],
    fill='toself',
    name='Resultado 2023',
    line_color='royalblue'
))

fig_radar.add_trace(go.Scatterpolar(
    r=radar_meta['Meta PEE-PE'],
    theta=radar_meta['Categoria'],
    fill='toself',
    name='Meta PEE-PE',
    line_color='firebrick',
    opacity=0.6
))

fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),
    showlegend=True,
    height=500
)

st.plotly_chart(fig_radar, use_container_width=True)

# Seção para exportar visualizações para o Canva
st.header("Exportar Visualizações para o Canva")

st.info("""
Para usar essas visualizações no Canva:
1. Capture os gráficos usando o botão de download em cada visualização (três pontos no canto superior direito)
2. Salve as imagens com boa resolução
3. Importe-as no Canva para criar sua apresentação final
""")

# Download dos dados processados
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
