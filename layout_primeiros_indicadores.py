import altair as alt

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
        border: 1px solid {params["cor_borda"]};
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
        width: 90%;
        border-collapse: collapse; 
        table-layout: fixed;  /* Permite controlar a largura de cada coluna */
        border: 1px solid {params["cor_borda"]}; /* Borda externa da tabela */
    }}
    .custom-table col:nth-child(1) {{ width: 30%; }}
    .custom-table col:nth-child(2) {{ width: 15%; }}
    .custom-table col:nth-child(3) {{ width: 15%; }}
    .custom-table col:nth-child(4) {{ width: 15%; }}
    .custom-table col:nth-child(5) {{ width: 15%; }}
    .custom-table td, .custom-table th {{
        border: none;         /* Remove qualquer borda das células */
        padding: 8px;
        vertical-align: middle;
        text-align: center;
    }}
    .custom-table th {{
        font-weight: 700; /* negrito */
        text-align: center;
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


# Função para construir o gráfico de linha de evolução
def construir_grafico_linha_evolucao(df_transformado, largura=450, altura=300, espessura_linha=5, tamanho_ponto=100):
    # Configurações de estilo
    fonte = "Arial"
    tamanho_texto_eixo = 16
    tamanho_texto_legenda = 16
    cor_grafico = "#364b60"

    # Cores específicas para cada categoria
    cores_categorias = {
        'Escolas': '#364b60',  # Azul escuro
        'Matrículas': '#cccccc',  # Cinza claro
        'Professores': '#a3b8cb'  # Azul claro
    }

    # Crie o gráfico de linha com pontos integrados
    grafico = alt.Chart(df_transformado).mark_line(
        strokeWidth=espessura_linha,
        point={  # Configuração dos pontos integrados à linha
            "filled": True,
            "size": tamanho_ponto
        }
    ).encode(
        x=alt.X('Ano:O',  # O :O força o tratamento como ordinal
                axis=alt.Axis(
                    values=[2015, 2020, 2025],  # Mostra apenas esses anos
                    title="Ano",
                    labelFontSize=tamanho_texto_eixo,
                    titleFontSize=tamanho_texto_eixo + 2,
                    titleFont=fonte,
                    labelFont=fonte,
                    labelAngle=0  # Garante que os rótulos estejam na horizontal
                )),
        y=alt.Y('Valor:Q',
                axis=alt.Axis(
                    title="Quantidade",
                    labelFontSize=tamanho_texto_eixo,
                    titleFontSize=tamanho_texto_eixo + 2,
                    titleFont=fonte,
                    labelFont=fonte,
                    format=',d'  # Formata números com separador de milhar
                )),
        color=alt.Color('Categoria:N',
                        legend=alt.Legend(
                            title="Categoria",
                            titleFontSize=tamanho_texto_legenda + 2,
                            labelFontSize=tamanho_texto_legenda,
                            titleFont=fonte,
                            labelFont=fonte,
                            orient='top',  # Posiciona a legenda no topo
                            titleAnchor='middle'
                        ),
                        scale=alt.Scale(domain=list(cores_categorias.keys()),
                                        range=list(cores_categorias.values())))
    ).properties(
        width=largura,
        height=altura
    ).configure_view(
        strokeWidth=0  # Remove a borda do gráfico
    ).configure_axis(
        gridColor='#f0f0f0',
        domainColor=cor_grafico,
        titleColor=cor_grafico,
        labelColor=cor_grafico
    )

    return grafico