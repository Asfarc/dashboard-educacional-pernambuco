# constantes.py

# ==============================================
# MENSAGENS DE ERRO
# ==============================================
ERRO_CARREGAR_DADOS = "Erro ao carregar os dados: {}"
ERRO_ARQUIVOS_NAO_ENCONTRADOS = "Não foi possível encontrar os arquivos Parquet necessários."
ERRO_CARREGAR_MAPEAMENTO = "Erro ao carregar o mapeamento de colunas: {}"
ERRO_COLUNA_NAO_ENCONTRADA = "A coluna '{}' não está disponível nos dados."
ERRO_ETAPA_NAO_ENCONTRADA = "A etapa '{}' não foi encontrada no mapeamento de colunas."
ERRO_SUBETAPA_NAO_ENCONTRADA = "A subetapa '{}' não foi encontrada para a etapa '{}'."
ERRO_SERIE_NAO_ENCONTRADA = "A série '{}' não foi encontrada para a subetapa '{}'."
ERRO_CONVERTER_CSV = "Erro ao converter para CSV: {}"
ERRO_CONVERTER_EXCEL = "Erro ao converter para Excel: {}"
ERRO_CALCULAR_ESTATISTICAS = "Erro ao calcular estatísticas: {}"
ERRO_CALCULAR_TOP5 = "Erro ao calcular top 5: {}"

# ==============================================
# MENSAGENS DE INFORMAÇÃO
# ==============================================
INFO_VERIFICAR_ARQUIVOS = "Verifique se os arquivos Parquet estão disponíveis no repositório."
INFO_USANDO_ALTERNATIVA = "Usando '{}' como alternativa"
INFO_FILTRO_APLICADO = "Filtro aplicado: mostrando {} de {} registros."
INFO_SEM_DADOS_TOP5 = "Não há dados suficientes para exibir o Top 5."
INFO_NAO_CALCULADO_TOP5 = "Não foi possível calcular os maiores valores."
INFO_SEM_COLUNAS_TOP5 = "Não há colunas disponíveis para exibir o Top 5."
INFO_AMOSTRA_REGISTROS = "Mostrando amostra de 5.000 registros (de um total maior)"

# ==============================================
# MENSAGENS DE AVISO
# ==============================================
AVISO_COLUNA_NAO_DISPONIVEL = "A coluna '{}' não está disponível para análise estatística."
AVISO_DATASET_GRANDE = "O conjunto de dados tem {} linhas, o que pode causar lentidão na visualização."
AVISO_SEM_DADOS_TABELA = "Não há dados para exibir na tabela."
AVISO_USANDO_MAPEAMENTO_INTERNO = "Usando mapeamento interno devido a erro: {}"

# ==============================================
# TÍTULOS E SUBTÍTULOS
# ==============================================
TITULO_DASHBOARD = "Dashboard de Matrículas - Inep"
TITULO_DADOS_DETALHADOS = "Dados Detalhados"
TITULO_ESTATISTICAS = "Estatísticas"
TITULO_TOP5 = "Top 5 Valores"
TITULO_NAVEGACAO = "Navegação da tabela"
TITULO_CONFIGURACOES = "Configurações de exibição"
SUBTITULO_RESUMO = "Resumo Estatístico"
SUBTITULO_FILTROS = "Filtros da tabela"

# ==============================================
# RÓTULOS E TEXTOS DE INTERFACE
# ==============================================
ROTULO_NIVEL_AGREGACAO = "Nível de Agregação:"
ROTULO_ANO_CENSO = "Ano do Censo:"
ROTULO_DEPENDENCIA = "DEPENDENCIA ADMINISTRATIVA:"
ROTULO_ETAPA = "Etapa de Ensino:"
ROTULO_SUBETAPA = "Subetapa:"
ROTULO_SERIE = "Série:"
ROTULO_TOTAL_MATRICULAS = "Total de Matrículas"
ROTULO_MEDIA_MATRICULAS = "Média de Matrículas"
ROTULO_MEDIA_POR_ESCOLA = "Média de Matrículas por Escola"
ROTULO_TOTAL_ESCOLAS = "Total de Escolas"
ROTULO_TOTAL_MUNICIPIOS = "Total de Municípios"
ROTULO_MAXIMO_MATRICULAS = "Máximo de Matrículas"
ROTULO_BTN_PRIMEIRA_LINHA = "⏫ Primeira Linha"
ROTULO_BTN_ULTIMA_LINHA = "⏬ Última Linha"
ROTULO_BTN_DOWNLOAD_CSV = "Download CSV"
ROTULO_BTN_DOWNLOAD_EXCEL = "Download Excel"
ROTULO_MOSTRAR_TUDO = "Carregar todos os dados (pode ser lento)"
ROTULO_MOSTRAR_REGISTROS = "Mostrar todos os registros"
ROTULO_AJUSTAR_ALTURA = "Ajustar altura da tabela"
ROTULO_MODO_DESEMPENHO = "Ativar modo de desempenho"
DICA_ALTURA_TABELA = "Use esta opção se estiver vendo barras de rolagem duplicadas"
DICA_MODO_DESEMPENHO = "Otimiza o carregamento para grandes conjuntos de dados."
RODAPE_NOTA = "**Nota:** Os dados são provenientes do Censo Escolar. Os traços (-) indicam ausência de dados."
DICAS_NAVEGACAO = """
    <div style="background-color: #f5f7fa; padding: 10px; border-radius: 5px; margin-top: 5px; margin-bottom: 15px; font-size: 0.9em;">
        <strong>✨ Dicas de navegação:</strong> Use <kbd>Home</kbd> para ir à primeira linha e <kbd>End</kbd> para ir à última.
        <kbd>↑</kbd>/<kbd>↓</kbd> navega entre linhas, <kbd>←</kbd>/<kbd>→</kbd> entre colunas.
        <kbd>Ctrl+F</kbd> ou a barra de filtro acima para buscar em todas as colunas.
    </div>
"""

# ==============================================
# FORMATOS DE ARQUIVOS E NOMES
# ==============================================
NOME_ARQUIVO_CSV = "dados_{}_{}_.csv"
NOME_ARQUIVO_EXCEL = "dados_{}_{}_.xlsx"
NOME_SEM_DADOS = "Sem_Dados"
MENSAGEM_SEM_DADOS = "Não há dados para exportar."
MENSAGEM_ERRO_CONVERSAO = "Erro na conversão"