# Changelog

Todas as mudanças relevantes do produto e do projeto são registradas neste arquivo.

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
