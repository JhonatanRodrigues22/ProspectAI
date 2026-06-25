# ProspectAI

Fundação do ProspectAI, uma aplicação planejada para localizar empresas por CEP, categoria e raio e gerar leads comerciais.

> Estado atual: as integrações isoladas com ViaCEP e Google Places estão implementadas. Ainda não existe fluxo integrado de busca, banco de dados, autenticação ou recursos de IA.

## Requisitos

- Python 3.11 ou superior
- Git (necessário apenas para versionamento e publicação)

## Instalação

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Também é possível executar:

```powershell
.\scripts\setup.ps1
```

## Execução

```powershell
python -m launcher
```

Depois, acesse:

- Aplicação: http://127.0.0.1:8000
- Saúde da API: http://127.0.0.1:8000/api/health
- Consulta de CEP: http://127.0.0.1:8000/api/cep/01310-100
- Documentação da API: http://127.0.0.1:8000/docs

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

## Google Places

O serviço `GooglePlacesService` encapsula a Places API (New) e converte resultados de Text Search diretamente em objetos `Lead`.

Configure a chave somente no arquivo `.env`:

```dotenv
GOOGLE_PLACES_API_KEY=sua-chave
GOOGLE_PLACES_TIMEOUT_SECONDS=5
```

Exemplo de uso isolado:

```python
from backend.app.services.google_places_service import GooglePlacesService

service = GooglePlacesService()
leads = await service.search_text("padarias em São Paulo")
```

A integração trata chave ausente ou inválida, rate limit, timeout, erros HTTP e respostas inesperadas. Ela não executa consulta ViaCEP nem implementa o fluxo completo de prospecção.

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
│       ├── api/            # Rotas HTTP
│       ├── core/           # Configuração central
│       ├── domain/         # Modelos internos do negócio
│       ├── integrations/   # Contratos e mapeadores de APIs externas
│       ├── models/         # Contratos de dados
│       └── services/       # Serviços de integração
├── frontend/               # Interface web estática
├── launcher/               # Entrada para execução local
├── docs/                   # Documentação técnica
├── scripts/                # Scripts de ambiente e validação
├── tests/                  # Testes automatizados
└── CHANGELOG.md            # Histórico do produto e projeto
```

Consulte [docs/architecture.md](docs/architecture.md) para os limites definidos nesta etapa.

## Primeiro commit e push

Após instalar o Git e criar um repositório vazio no GitHub:

```powershell
git init
git add .
git commit -m "chore: initialize ProspectAI foundation"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/ProspectAI.git
git push -u origin main
```
