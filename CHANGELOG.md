# Changelog

Todas as mudanças relevantes do produto e do projeto são registradas neste arquivo.

## [0.1.0-rc1] - 2026-06-25

### Adicionado

- Launcher unificado para iniciar API e Streamlit com um único comando.
- Configuração guiada e oculta da chave Google no primeiro uso.
- Detecção de portas ocupadas com seleção automática de alternativa.
- Abertura automática da interface no navegador.
- Atalho `ProspectAI.bat` para execução por duplo clique no Windows.
- Release Notes em `docs/releases/v0.1.0-rc1.md`.
- Testes automatizados do launcher.

### Alterado

- Versão pública consolidada como `0.1.0-rc1`.
- Documentação reorganizada para instalação e uso por terceiros.
- Launcher passou a encerrar API e interface em conjunto.
- Tratamento do timeout explícito do ViaCEP foi uniformizado.

## [0.9.0] - 2026-06-25

### Adicionado

- Exportador Excel `.xlsx` para `SearchResult`.
- Planilha `Leads` com cabeçalho destacado, filtros e primeira linha congelada.
- Botão `Baixar Excel` no Streamlit.
- Testes de leitura e compatibilidade com `openpyxl`.

### Alterado

- CSV e Excel passaram a compartilhar cabeçalhos e mapeamento de linhas.
- `openpyxl` adicionado às dependências.
- Versão da API atualizada para `0.9.0`.

## [0.8.0] - 2026-06-25

### Adicionado

- Exportador CSV dedicado para `SearchResult`.
- Cabeçalhos amigáveis em português.
- Encoding UTF-8 com BOM e separador compatível com Excel.
- Botão `Baixar CSV` no Streamlit quando houver resultados.
- Testes de acentos, cabeçalhos, campos vazios e leitura CSV.

### Alterado

- Versão da API atualizada para `0.8.0`.

## [0.7.0] - 2026-06-25

### Adicionado

- Primeira interface funcional em Streamlit.
- Formulário com CEP, categoria e raio.
- Estados visuais de carregamento, erro, ausência de resultados e sucesso.
- Tabela simples para apresentação de leads.
- Script PowerShell para iniciar a interface.
- Testes headless com o framework oficial do Streamlit.

### Alterado

- Normalização de CEP movida para utilitário puro do domínio.
- Streamlit adicionado às dependências da aplicação.
- Versão da API atualizada para `0.7.0`.

## [0.6.0] - 2026-06-25

### Adicionado

- Integração isolada com Google Geocoding.
- Modelo `GeoPoint`.
- Cálculo puro de distância pela fórmula de Haversine.
- Bias circular no Google Places usando origem e raio.
- Filtro final de leads pela distância geográfica calculada.
- Campo opcional `distance_km` em `Lead`.
- Tratamento de endereço insuficiente, geocoding sem resultado e falhas externas.
- Testes mockados de geocoding, distância e filtragem integrada.

### Alterado

- `radius_km` passou a aceitar valores de até 50 km e agora é aplicado de fato.
- Leads sem coordenadas são excluídos do resultado geográfico.
- Versão da API atualizada para `0.6.0`.

## [0.5.0] - 2026-06-25

### Adicionado

- Orquestrador inicial de busca entre ViaCEP e Google Places.
- Endpoint `GET /api/search`.
- Composição textual de categoria e endereço para o Google Places.
- Retorno padronizado como `SearchResult`.
- Tratamento HTTP consistente para validação e falhas dos provedores.
- Testes mockados do serviço de aplicação e do endpoint.

### Observação

- `radius_km` é validado e preservado, mas ainda não executa filtro geográfico real.

## [0.4.0] - 2026-06-25

### Adicionado

- Serviço assíncrono para Text Search da Places API (New).
- Autenticação por `GOOGLE_PLACES_API_KEY`.
- Contratos privados do provedor e mapper de respostas Google para `Lead`.
- Tratamento de chave inválida, rate limit, timeout, erros HTTP e respostas inesperadas.
- Testes automatizados da integração com transporte HTTP simulado.

### Alterado

- Timeout do Google Places passou a ser configurável por variável de ambiente.
- Versão da API atualizada para `0.4.0`.

## [0.3.0] - 2026-06-25

### Adicionado

- Camada de domínio desacoplada em `backend/app/domain/`.
- Modelos `Lead`, `SearchRequest` e `SearchResult`.
- Validações de CEP normalizado, categoria, raio, rating, reviews e coordenadas.
- Testes automatizados dos modelos de domínio.

## [0.2.0] - 2026-06-25

### Adicionado

- Endpoint `GET /api/cep/{cep}`.
- Integração assíncrona com a API ViaCEP.
- Validação e normalização de CEP com ou sem hífen.
- Tratamento de CEP inválido, inexistente, timeout e falhas externas.
- Testes automatizados com respostas externas simuladas.

### Alterado

- Configuração do ViaCEP passou a aceitar timeout por variável de ambiente.
- Versão da API atualizada para `0.2.0`.

## [0.1.0] - 2026-06-25

### Adicionado

- Estrutura inicial do repositório.
- Backend FastAPI com endpoint de saúde.
- Frontend web estático.
- Launcher Python para execução local.
- Configuração por variáveis de ambiente.
- Estrutura para testes, scripts e documentação.
