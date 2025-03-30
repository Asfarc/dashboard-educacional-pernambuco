import re
import os

# Caminho do arquivo original e do novo arquivo
caminho_arquivo_original = r"C:\Users\User\Desktop\DashBoard\backup\Código py\2-streamlit-dashboard-fixed.py"
diretorio_destino = os.path.dirname(caminho_arquivo_original)
caminho_arquivo_saida = os.path.join(diretorio_destino, "dashboard_renomeado.txt")

# Mapeamento de nomes para funções
mapeamento_funcoes = {
    "formatar_numero": "aplicar_padrao_numerico_brasileiro",
    "carregar_dados": "importar_arquivos_parquet",
    "carregar_mapeamento_colunas": "ler_dicionario_de_etapas",
    "criar_mapeamento_colunas": "padronizar_dicionario_de_etapas",
    "obter_coluna_dados": "procurar_coluna_matriculas_por_etapa",
    "verificar_coluna_existe": "confirmar_existencia_coluna_matriculas_por_etapa",
    "converter_df_para_csv": "gerar_arquivo_csv",
    "converter_df_para_excel": "gerar_planilha_excel"
}

# Mapeamento de nomes para variáveis
mapeamento_variaveis = {
    "tipo_visualizacao": "tipo_nivel_agregacao_selecionado",
    "mapeamento_colunas": "dicionario_das_etapas_de_ensino",
    "etapas_disponiveis": "lista_etapas_ensino",
    "etapa_selecionada": "etapa_ensino_selecionada",
    "series_disponiveis": "lista_de_series_das_etapas_de_ensino",
    "coluna_dados": "coluna_matriculas_por_etapa",
    "ajustar_altura": "modificar_altura_tabela",
    "colunas_tabela": "colunas_selecionadas_para_exibicao",
    "todas_colunas_possiveis": "conjunto_total_de_colunas",
    "colunas_adicionais_selecionadas": "colunas_adicionais_selecionadas_para_exibicao",
    "colunas_existentes": "colunas_matriculas_por_etapa_existentes",
    "kpi_container": "container_indicadores_principais",
    "tempo_final": "registro_conclusao_processamento",
    "tempo_total": "tempo_total_processamento_segundos"
}


def substituir_identificador(texto, palavra, substituicao):
    """
    Substitui apenas identificadores completos, evitando substituições parciais.
    Considera um identificador como: início do texto, após espaço, após parêntese,
    após vírgula, após =, etc. E termina antes de um espaço, parêntese, vírgula, etc.
    """
    # Padrão para reconhecer o identificador completo
    # \b marca limites de palavra
    padrao = r'\b' + re.escape(palavra) + r'\b'

    # Substitui todas as ocorrências do padrão
    novo_texto = re.sub(padrao, substituicao, texto)

    return novo_texto


def processamento_adicional(conteudo, mapeamento):
    """
    Faz o processamento adicional para tratar casos específicos
    """
    for antigo, novo in mapeamento.items():
        conteudo = substituir_identificador(conteudo, antigo, novo)

    return conteudo


def main():
    try:
        # Lê o arquivo original
        with open(caminho_arquivo_original, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read()

        # Faz as substituições
        conteudo_modificado = conteudo

        # Substituições para funções (def função_nome(...))
        for antigo, novo in mapeamento_funcoes.items():
            # Identificar definições de função
            padrao_def = r'def\s+' + re.escape(antigo) + r'\s*\('
            conteudo_modificado = re.sub(padrao_def, f'def {novo}(', conteudo_modificado)

            # Identificar chamadas de função
            conteudo_modificado = substituir_identificador(conteudo_modificado, antigo, novo)

        # Substituições para variáveis
        conteudo_modificado = processamento_adicional(conteudo_modificado, mapeamento_variaveis)

        # Salva o arquivo modificado
        with open(caminho_arquivo_saida, 'w', encoding='utf-8') as arquivo:
            arquivo.write(conteudo_modificado)

        print(f"Arquivo salvo com sucesso em: {caminho_arquivo_saida}")

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")


if __name__ == "__main__":
    main()