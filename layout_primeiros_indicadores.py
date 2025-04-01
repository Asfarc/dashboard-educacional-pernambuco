import altair as alt

# Configuração ESSENCIAL para formato numérico brasileiro
alt.renderers.set_embed_options({
    'formatLocale': {
        'decimal': ',',
        'thousands': '.',
        'grouping': [3],
        'currency': ['R$', '']
    },
    'timeFormatLocale': 'pt_BR'  # Opcional para datas em português
})

# Dicionário que centraliza parâmetros estilísticos e facilita ajustes
PARAMETROS_ESTILO_CONTAINER = {
    "raio_borda": 8,
    "cor_borda": "#dee2e6",
    "cor_titulo": "#364b60",
    "tamanho_fonte_titulo": "1.1rem",
    "cor_fonte_conteudo": "#364b60",
    "tamanho_fonte_conteudo": "1rem",
}

def obter_estilo_css_container() -> str:
    """
    Retorna um bloco de <style> contendo as configurações de borda,
    cor de texto, etc. para estilizar os containers e a tabela.

    Ajuste as chaves do dicionário PARAMETROS_ESTILO_CONTAINER para personalizar
    facilmente cores, bordas, tamanhos de fonte etc.
    """
    params = PARAMETROS_ESTILO_CONTAINER
    # Os placeholders abaixo usam p.ex. {params["cor_borda"]}, etc.
    bloco_estilo = f"""
    <style>
    .container-custom {{
        border: 1px solid {params["cor_borda"]};  /* Corrigido */
        border-radius: {params["raio_borda"]}px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: white;
    }}
    .container-title {{
        font-family: "Open Sans", sans-serif;
        font-weight: 700;
        color: {params["cor_titulo"]};
        font-size: {params["tamanho_fonte_titulo"]};
        margin-bottom: 0.5rem;
    }}
    .container-text {{
        font-family: "Open Sans", sans-serif;
        color: {params["cor_fonte_conteudo"]};
        font-weight: 400;
        font-size: {params["tamanho_fonte_conteudo"]};
    }}
    /* ----- Tabela customizada ----- */
    .custom-table {{
        width: 100%;
        border-collapse: separate; 
        border-spacing: 0;
        table-layout: fixed;
        border: 1px solid {params["cor_borda"]} !important; /* Borda garantida */
        border-radius: 8px;
        overflow: hidden;
    }}
    .custom-table col:nth-child(1) {{ width: 25%; }}
    .custom-table col:nth-child(2) {{ width: 13%; }}
    .custom-table col:nth-child(3) {{ width: 13%; }}
    .custom-table col:nth-child(4) {{ width: 13%; }}
    .custom-table col:nth-child(5) {{ width: 13%; }}
    .custom-table col:nth-child(6) {{ width: 13%; }}
    .custom-table td, .custom-table th {{
        border: none;         /* Remove qualquer borda das células */
        padding: 8px;
        vertical-align: middle;
        text-align: center;
    }}
    .custom-table th {{
        font-weight: 700; /* negrito */
        text-align: center;
        color: #364b60;
    }}
    .custom-table thead tr th {{
        border-bottom: none !important;
        border-top: none !important;
        box-shadow: none !important;  /* Streamlit adiciona sombra como borda */
        background-color: transparent !important;
    }}
    .custom-table td:first-child, .custom-table th:first-child {{
        border-left: none;  /* remove borda do lado esquerdo */
        text-align: left;
    }}
    .custom-table td:last-child, .custom-table th:last-child {{
        border-right: none; /* remove borda do lado direito */
    }}
    .icone {{
        width: 50px;
        height: 50px;
        vertical-align: middle;
        margin-right: 6px;
    }}
    </style>
    """
    return bloco_estilo


# Importando pandas para acesso à função isna
import pandas as pd


# Função para formatar números com padrão brasileiro
def aplicar_padrao_numerico_brasileiro(numero):
    """
    Formata números grandes adicionando separadores de milhar em padrão BR:
    Ex.: 1234567 -> '1.234.567'
         1234.56 -> '1.234,56'
    Se o número for NaN ou '-', retorna '-'.
    Aplica formatação apenas a valores numéricos.

    Parâmetros:
        numero: O número a ser formatado

    Retorna:
        String formatada com o padrão brasileiro de números
    """
    if pd.isna(numero) or numero == "-":
        return "-"

    try:
        float_numero = float(numero)
        if float_numero.is_integer():
            return f"{int(float_numero):,}".replace(",", ".")
        else:
            parte_inteira = int(float_numero)
            parte_decimal = abs(float_numero - parte_inteira)
            inteiro_fmt = f"{parte_inteira:,}".replace(",", ".")
            decimal_fmt = f"{parte_decimal:.2f}".replace("0.", "").replace(".", ",")
            return f"{inteiro_fmt},{decimal_fmt}"
    except (ValueError, TypeError):
        return str(numero)

# Mantemos a função anterior por compatibilidade, mas usando a nova implementação
def formatar_numero_com_pontos_milhar(numero: float) -> str:
    """
    Função compatível com o código existente que usa a implementação de
    aplicar_padrao_numerico_brasileiro.
    """
    return aplicar_padrao_numerico_brasileiro(numero)

# Função modificada com controle de tamanho de texto
def construir_grafico_linha_evolucao(
    df_transformado,
    largura=450,
    altura=300,
    espessura_linha=5,
    tamanho_ponto=100,
    tamanho_texto_eixo=16,
    tamanho_texto_legenda=16,
    tamanho_titulo_eixo=18,
    tamanho_titulo_legenda=18
):
    # Antes de criar o gráfico, faça:
    df_transformado['Valor'] = df_transformado['Valor'].astype(float)
    # Configurações de estilo
    fonte = "Arial"
    cor_grafico = "#364b60"

    # Mantém as cores das categorias
    cores_categorias = {
        'Escolas': '#364b60',
        'Matrículas': '#cccccc',
        'Professores': '#a3b8cb'
    }

    # Criação do gráfico com parâmetros ajustáveis
    grafico = alt.Chart(df_transformado).mark_line(
        strokeWidth=espessura_linha,
        point={"filled": True, "size": tamanho_ponto}
    ).encode(
        x=alt.X('Ano:O',
                axis=alt.Axis(
                    #values=[2015, 2020, 2023],
                    title="Ano",
                    labelFontSize=tamanho_texto_eixo,          # Usa novo parâmetro
                    titleFontSize=tamanho_titulo_eixo,         # Usa novo parâmetro
                    titleFont=fonte,
                    labelFont=fonte,
                    labelAngle=0
                )),
        y=alt.Y('Valor:Q',
                axis=alt.Axis(
                    title="Quantidade",
                    labelFontSize=tamanho_texto_eixo,          # Usa novo parâmetro
                    titleFontSize=tamanho_titulo_eixo,          # Usa novo parâmetro
                    titleFont=fonte,
                    labelFont=fonte,
                    format='.0f',
                    labelExpr="replace(format(datum.value, '.0f'), ',', '.')"
                )),
        color=alt.Color('Categoria:N',
                        legend=alt.Legend(
                            title="",
                            titleFontSize=tamanho_titulo_legenda,  # Usa novo parâmetro
                            labelFontSize=tamanho_texto_legenda,   # Usa novo parâmetro
                            titleFont=fonte,
                            labelFont=fonte,
                            orient='top',
                            titleAnchor='middle'
                        ),
                        scale=alt.Scale(
                            domain=list(cores_categorias.keys()),
                            range=list(cores_categorias.values())
                        ))
    ).properties(
        width=largura,
        height=altura
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        gridColor='#f0f0f0',
        domainColor=cor_grafico,
        titleColor=cor_grafico,
        labelColor=cor_grafico
    )

    return grafico