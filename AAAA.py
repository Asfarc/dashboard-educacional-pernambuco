import pandas as pd
import logging
import os
from datetime import datetime

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def remover_coluna_duplicada(arquivo_entrada, arquivo_saida):
    """
    Remove a coluna duplicada 'Nome da Escola.1' do arquivo parquet
    e salva o resultado em um novo arquivo.
    """
    # Verificar se o arquivo de entrada existe
    if not os.path.exists(arquivo_entrada):
        logger.error(f"Arquivo de entrada não encontrado: {arquivo_entrada}")
        return False

    # Carregar o arquivo parquet
    logger.info(f"Lendo arquivo: {os.path.basename(arquivo_entrada)}")
    try:
        df = pd.read_parquet(arquivo_entrada)

        # Exibir informações antes da remoção
        logger.info(f"Dimensões originais do DataFrame: {df.shape}")
        logger.info(f"Colunas originais: {df.columns.tolist()}")

        # Verificar se a coluna existe
        coluna_a_remover = 'Nome da Escola.1'
        if coluna_a_remover in df.columns:
            # Remover a coluna
            df = df.drop(columns=[coluna_a_remover])
            logger.info(f"Coluna '{coluna_a_remover}' removida com sucesso.")

            # Exibir informações após a remoção
            logger.info(f"Novas dimensões do DataFrame: {df.shape}")
            logger.info(f"Colunas após remoção: {df.columns.tolist()}")

            # Salvar o DataFrame sem a coluna duplicada
            df.to_parquet(arquivo_saida)
            logger.info(f"Arquivo salvo com sucesso em: {arquivo_saida}")
            return True
        else:
            logger.warning(f"Coluna '{coluna_a_remover}' não encontrada no DataFrame.")
            return False

    except Exception as e:
        logger.error(f"Erro ao processar o arquivo: {e}")
        return False


def main():
    # Caminhos dos arquivos
    arquivo_entrada = r"C:\Fábio\dashboard\dados.parquet"
    arquivo_saida = r"C:\Fábio\dashboard\dados_limpo.parquet"

    # Remover coluna duplicada
    if remover_coluna_duplicada(arquivo_entrada, arquivo_saida):
        logger.info("Processo concluído com sucesso!")
    else:
        logger.error("Processo concluído com erros.")


if __name__ == "__main__":
    main()