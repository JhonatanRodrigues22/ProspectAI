# Arquitetura inicial

## Objetivo desta etapa

A Issue #001 entrega somente a fundação executável do ProspectAI. A estrutura separa responsabilidades sem antecipar regras de negócio.

## Componentes

- **Backend:** aplicação FastAPI, configuração e rotas HTTP.
- **Frontend:** arquivos estáticos servidos pelo backend.
- **Launcher:** ponto único de entrada para execução local.
- **Integrações:** namespaces vazios para ViaCEP e Google Places.
- **Testes:** validação da fundação existente.

## Fluxo atual

```text
python -m launcher
        |
        v
FastAPI ----> /api/health
   |
   +--------> frontend/
```

## Limites explícitos

Nesta versão não existem:

- consulta ao ViaCEP;
- consulta ao Google Places;
- busca de empresas;
- persistência em banco de dados;
- autenticação;
- inteligência artificial;
- exportação CSV ou Excel.

Esses itens dependem de Issues próprias.
