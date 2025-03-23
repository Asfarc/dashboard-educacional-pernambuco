Explicação da Estrutura do Projeto Dashboard Educacional de Pernambuco

A estrutura modular que você implementou segue boas práticas de arquitetura de software, separando responsabilidades e facilitando a manutenção. Vamos examinar a função de cada componente:

Arquivos na Raiz

app.py

Arquivo principal da aplicação que coordena todo o fluxo de execução. Contém a interface com o usuário, incluindo controles, filtros e visualizações. Integra os diferentes módulos, fazendo chamadas às funções especializadas quando necessário.

constantes.py

Centraliza todos os textos, mensagens e valores constantes utilizados no sistema. Este arquivo facilita a manutenção e internacionalização, pois toda informação textual está em um único lugar, evitando duplicação e permitindo alterações rápidas.

config.py

Gerencia configurações globais da aplicação Streamlit, como título da página, ícone, layout e estado inicial da barra lateral. Separar essas configurações facilita ajustes rápidos na aparência e comportamento geral do dashboard.

Diretório utils/
__init__.py

Marca o diretório como um pacote Python, permitindo importações organizadas dos módulos internos.

formatacao.py

Contém funções para formatação de valores, principalmente a função formatar_numero() que padroniza a exibição de valores numéricos com separadores de milhar e casas decimais apropriadas. Essencial para apresentação consistente dos dados.

carregamento.py

Responsável por localizar e carregar os arquivos de dados (.parquet) nas diversas possíveis localizações. Inclui tratamento de erros e conversão de tipos de dados, garantindo que as informações estejam prontas para análise.

exportacao.py

Implementa as funções para exportar dados em formatos CSV e Excel, incluindo tratamento para casos especiais como DataFrames vazios e formatação adequada. Facilita o compartilhamento dos dados pelos usuários.

Diretório componentes/
__init__.py
Designa o diretório como um pacote Python organizando os componentes de interface.

Subdiretório aggrid/
__init__.py

Marca o subdiretório como um subpacote para componentes relacionados ao AgGrid.

locale_pt_br.py

Contém a tradução completa para português brasileiro de todas as mensagens e rótulos do componente AgGrid, garantindo uma experiência localizada para os usuários.

js_code.py

Armazena as funções JavaScript utilizadas pelo AgGrid para funcionalidades avançadas como destacar a linha de totais e calcular estatísticas dinamicamente.

config.py

Mantém configurações específicas para o componente AgGrid, separando estas configurações das configurações gerais do aplicativo.

tabelas.py

Implementa funções para manipulação e exibição de tabelas, incluindo a adição de linhas de totais e a configuração completa do componente AgGrid, com ordenação, filtros e formatação personalizada.

navegacao.py

Gerencia os controles de navegação na interface, permitindo ao usuário navegar facilmente pelas tabelas de dados extensas, como ir para o início ou final da tabela.

Diretório processamento/
__init__.py
Define o diretório como um pacote Python para processamento de dados.

mapeamento.py

Contém as funções que interpretam o arquivo JSON de mapeamento de colunas, permitindo a seleção dinâmica das colunas corretas com base na etapa de ensino, subetapa e série selecionadas pelo usuário.

analise.py

Implementa funções analíticas como cálculo de estatísticas, extração dos valores máximos e preparação de dados para visualização. Mantém a lógica de análise separada da interface do usuário.
