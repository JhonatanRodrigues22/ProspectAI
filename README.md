# ProspectAI

Fundação do ProspectAI, uma aplicação planejada para localizar empresas por CEP, categoria e raio e gerar leads comerciais.

> Estado atual: somente a estrutura inicial está implementada. Ainda não existem busca de empresas, integrações externas, banco de dados, autenticação ou recursos de IA.

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
- Documentação da API: http://127.0.0.1:8000/docs

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
│       └── integrations/   # Futuras integrações externas
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
