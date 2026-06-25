# ProspectAI

Fundação do ProspectAI, uma aplicação planejada para localizar empresas por CEP, categoria e raio e gerar leads comerciais.

> Estado atual: a consulta de endereços por CEP via ViaCEP está implementada. Ainda não existem busca de empresas, Google Places, banco de dados, autenticação ou recursos de IA.

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
│       ├── models/         # Contratos de dados
│       ├── services/       # Regras e chamadas externas
│       └── integrations/   # Espaço para integrações futuras
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
