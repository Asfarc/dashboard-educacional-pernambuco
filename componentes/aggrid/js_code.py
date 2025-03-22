from st_aggrid import JsCode

# Estilo para destacar a linha de totais
js_total_row = JsCode("""
function(params) {
    try {
        // Verifica se há dados na linha
        if (!params.data) {
            return null;
        }

        // Verifica qualquer coluna com TOTAL (case insensitive)
        let isTotal = false;
        for (const key in params.data) {
            if (params.data[key] !== null && 
                params.data[key] !== undefined &&
                params.data[key].toString().toUpperCase().includes('TOTAL')) {
                isTotal = true;
                break;
            }
        }

        // Verifica se é a última linha (para totais calculados dinamicamente)
        if (isTotal || 
            (params.node && params.api && 
            params.node.rowIndex === (params.api.getDisplayedRowCount() - 1))) {
            return {
                'font-weight': 'bold',
                'background-color': '#e6f2ff',
                'border-top': '2px solid #b3d9ff',
                'color': '#0066cc'
            };
        }
        return null;
    } catch (error) {
        console.error('Erro ao estilizar linha:', error);
        return null;
    }
}
""")


# Função para gerar o código JS de estatísticas
def get_agg_functions_js(coluna_dados):
    """
    Gera o código JavaScript para calcular estatísticas na tabela.

    Args:
        coluna_dados (str): Nome da coluna de dados para cálculos estatísticos

    Returns:
        JsCode: Código JavaScript para o AgGrid
    """
    return JsCode("""
    function(params) {
        try {
            // Obter coluna de dados principal
            const dataColumn = "%s";
            if (!dataColumn) return 'Coluna de dados não definida';

            // Coletar todos os valores visíveis
            const values = [];
            let totalSum = 0;
            let count = 0;

            params.api.forEachNodeAfterFilter(node => {
                if (!node.data) return;

                // Verifica se não é linha de TOTAL
                let isTotal = false;
                for (const key in node.data) {
                    if (node.data[key] && 
                        node.data[key].toString().toUpperCase().includes('TOTAL')) {
                        isTotal = true;
                        break;
                    }
                }
                if (isTotal) return;

                // Extrai o valor como número
                const cellValue = node.data[dataColumn];
                if (cellValue !== null && cellValue !== undefined) {
                    const numValue = Number(cellValue.toString().replace(/[^0-9.,]/g, '').replace(',', '.'));
                    if (!isNaN(numValue)) {
                        values.push(numValue);
                        totalSum += numValue;
                        count++;
                    }
                }
            });
            // Formatar para exibição amigável
            const formatNum = function(num) {
                // Primeiro formatar usando Intl.NumberFormat
                let formatted = new Intl.NumberFormat('pt-BR', { 
                    maximumFractionDigits: 2 
                }).format(num);

                // Depois converter para usar ponto como separador
                // Substituir pontos por underscores temporariamente
                formatted = formatted.replace(/\\./g, '_');
                // Substituir vírgulas por pontos
                formatted = formatted.replace(/,/g, '.');
                // Substituir underscores de volta para pontos
                formatted = formatted.replace(/_/g, '.');
                return formatted;
            };
            // Calcular estatísticas
            if (values.length === 0) {
                return 'Não há dados numéricos';
            }
            const avg = totalSum / count;
            values.sort((a, b) => a - b);
            const min = values[0];
            const max = values[values.length - 1];
            // Mensagem formatada
            return `Total: ${formatNum(totalSum)} | Média: ${formatNum(avg)} | Mín: ${formatNum(min)} | Máx: ${formatNum(max)}`;
        } catch (error) {
            console.error('Erro ao calcular estatísticas:', error);
            return 'Erro ao calcular estatísticas';
        }
    }
    """ % (coluna_dados if coluna_dados else ''))


# Formatador para valores percentuais
percent_formatter = JsCode("""
function(params) {
    if (params.value === null || params.value === undefined || isNaN(params.value)) return '-';
    const numValue = Number(params.value);
    return numValue.toFixed(2) + '%';
}
""")

# Controla o que é exportado pelo módulo
__all__ = ['js_total_row', 'get_agg_functions_js', 'percent_formatter']