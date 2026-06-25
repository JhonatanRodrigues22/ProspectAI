# ProspectAI

Aplicação local para localizar empresas por CEP, categoria e raio e gerar
listas de leads comerciais.

> Versão atual: `v0.1.0-rc1`. O fluxo integra ViaCEP, Google Geocoding,
> Google Places, filtro geográfico real, interface Streamlit e exportações
> CSV e Excel.

## Requisitos

- Python 3.11 ou superior
- Uma chave do Google Maps Platform com as APIs Places e Geocoding
  habilitadas

## Instalação

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

No Windows, o script abaixo prepara o ambiente automaticamente:

```powershell
.\scripts\setup.ps1
```

## Configuração da chave Google

Na primeira execução pelo launcher, o ProspectAI solicita a chave Google de
forma oculta e a salva no arquivo local `.env`. Esse arquivo não é enviado ao
Git.

Também é possível configurá-la antecipadamente:

```dotenv
GOOGLE_PLACES_API_KEY=sua-chave
```

Consulte as [Release Notes da v0.1.0-rc1](docs/releases/v0.1.0-rc1.md) para
as APIs necessárias e limitações conhecidas.

## Execução recomendada

No Windows, dê duplo clique em `ProspectAI.bat`. O arquivo prepara o ambiente
na primeira execução e inicia a aplicação.

Pelo terminal:

```powershell
python -m launcher
```

O launcher:

- inicia a API FastAPI;
- inicia a interface Streamlit;
- procura portas livres se `8000` ou `8501` estiverem ocupadas;
- abre a interface no navegador;
- encerra os dois processos com `Ctrl+C`.

Com as portas padrão:

- Interface: http://127.0.0.1:8501
- Saúde da API: http://127.0.0.1:8000/api/health
- Documentação da API: http://127.0.0.1:8000/docs

Para iniciar sem abrir o navegador:

```powershell
python -m launcher --no-browser
```

### Execução isolada da interface

Execute:

```powershell
python -m streamlit run ui/streamlit_app.py
```

Ou, no Windows:

```powershell
.\scripts\run_streamlit.ps1
```

Depois, acesse http://localhost:8501.

A interface contém CEP, categoria, raio e o botão `Pesquisar`. Ela cria um `SearchRequest` e chama exclusivamente o `SearchService`, exibindo carregamento, erros, ausência de resultados e uma tabela simples quando a busca é concluída.

Quando houver leads, a interface também exibe os botões `Baixar CSV` e `Baixar Excel`.

## Exportação CSV

O exportador recebe um `SearchResult` e gera CSV compatível com Excel no Windows:

- codificação UTF-8 com BOM;
- separador `;`;
- cabeçalhos amigáveis em português;
- campos ausentes representados como células vazias.

O arquivo inclui nome, contatos, endereço, avaliação, distância e identificação da fonte. A exportação não depende do Streamlit e pode ser reutilizada por outras interfaces:

```python
from backend.app.exporters import export_search_result_csv

csv_content = export_search_result_csv(search_result)
```

## Exportação Excel

O exportador Excel recebe o mesmo `SearchResult` e gera um arquivo `.xlsx` em memória:

- aba `Leads`;
- mesmos cabeçalhos e ordem de campos do CSV;
- cabeçalho destacado;
- primeira linha congelada;
- filtro automático;
- larguras básicas ajustadas.

```python
from backend.app.exporters import export_search_result_excel

excel_content = export_search_result_excel(search_result)
```

## Consulta de CEP

O endpoint aceita CEP com ou sem hífen:

```http
GET /api/cep/{cep}
```

Exemplo:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/cep/01310-100
```

Resposta:

```json
{
  "cep": "01310-100",
  "logradouro": "Avenida Paulista",
  "complemento": "até 610 - lado par",
  "bairro": "Bela Vista",
  "localidade": "São Paulo",
  "uf": "SP",
  "ibge": "3550308",
  "gia": "1004",
  "ddd": "11",
  "siafi": "7107"
}
```

Erros de validação, CEP inexistente, indisponibilidade externa e timeout retornam mensagens amigáveis com status HTTP apropriado.

## Modelos de domínio

Os conceitos centrais ficam em `backend/app/domain/` e não dependem de FastAPI, ViaCEP, Google Places ou persistência:

- `Lead`: empresa ou contato comercial encontrado.
- `SearchRequest`: critérios internos de uma solicitação de busca.
- `SearchResult`: conjunto de leads retornado por uma busca.

Os modelos exigem CEP normalizado com oito dígitos e aplicam validações básicas de categoria, raio, avaliações, quantidade de reviews e coordenadas.

## Google Places e Geocoding

O serviço `GooglePlacesService` encapsula a Places API (New) e converte resultados de Text Search diretamente em objetos `Lead`.

Se não usar o fluxo guiado do launcher, configure a chave no `.env`:

```dotenv
GOOGLE_PLACES_API_KEY=sua-chave
GOOGLE_PLACES_TIMEOUT_SECONDS=5
GOOGLE_GEOCODING_TIMEOUT_SECONDS=5
```

A chave precisa ter acesso às APIs Places e Geocoding no Google Maps
Platform. Restrições de chave e cobrança são administradas no Google Cloud.

Exemplo de uso isolado:

```python
from backend.app.services.google_places_service import GooglePlacesService

service = GooglePlacesService()
leads = await service.search_text("padarias em São Paulo")
```

A integração trata chave ausente ou inválida, rate limit, timeout, erros HTTP e respostas inesperadas. Ela não executa consulta ViaCEP nem implementa o fluxo completo de prospecção.

## Busca de leads

O endpoint inicial de busca combina as integrações existentes:

```http
GET /api/search?cep=12900000&category=academia&radius_km=5
```

Fluxo:

1. valida e normaliza o CEP;
2. resolve o endereço no ViaCEP;
3. converte o endereço em coordenadas com Google Geocoding;
4. consulta o Google Places com categoria, origem e raio;
5. calcula a distância de cada lead com Haversine;
6. descarta resultados sem coordenadas ou fora do raio;
7. retorna um `SearchResult` contendo objetos `Lead`.

Exemplo:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/search?cep=12900000&category=academia&radius_km=5"
```

### Aplicação do raio

`radius_km` é obrigatório, deve estar entre 0 e 50 km e possui aplicação geográfica real. A consulta usa um círculo como bias no Google Places e confirma localmente cada distância com Haversine.

Cada lead aceito recebe `distance_km`, arredondado para três casas decimais. Leads sem coordenadas são descartados porque não é possível confirmar sua distância.

Quando nenhum estabelecimento é encontrado, a API retorna sucesso com `total_results` igual a zero e `leads` vazio.

## Testes

```powershell
pytest
```

Ou:

```powershell
.\scripts\test.ps1
```

## Estrutura

```text
ProspectAI/
├── backend/                # Aplicação FastAPI
│   └── app/
│       ├── application/    # Casos de uso e orquestração
│       ├── api/            # Rotas HTTP
│       ├── core/           # Configuração central
│       ├── domain/         # Modelos internos do negócio
│       ├── exporters/      # Exportadores CSV e Excel
│       ├── integrations/   # Contratos e mapeadores de APIs externas
│       ├── models/         # Contratos de dados
│       └── services/       # Serviços de integração
├── frontend/               # Interface web estática
├── launcher/               # Entrada para execução local
├── ui/                     # Interface funcional em Streamlit
├── docs/                   # Documentação técnica
├── scripts/                # Scripts de ambiente e validação
├── tests/                  # Testes automatizados
└── CHANGELOG.md            # Histórico do produto e projeto
```

Consulte [docs/architecture.md](docs/architecture.md) para os limites definidos nesta etapa.
