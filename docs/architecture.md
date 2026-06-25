# Arquitetura

## Objetivo atual

O ProspectAI separa domínio, casos de uso, transporte HTTP e contratos externos. O fluxo atual pesquisa leads por CEP, categoria e raio geográfico.

## Componentes

- **API:** aplicação FastAPI e tradução de erros para HTTP.
- **Aplicação:** orquestração entre ViaCEP, Geocoding e Places.
- **Domínio:** `Lead`, `SearchRequest`, `SearchResult`, `GeoPoint` e cálculo Haversine.
- **Serviços:** clientes assíncronos para provedores externos.
- **Exportadores:** transformações puras de `SearchResult` em formatos externos.
- **Integrações:** contratos e mapeadores específicos dos provedores.
- **Frontend:** arquivos estáticos servidos pelo backend.
- **UI:** aplicação Streamlit que consome exclusivamente o caso de uso `SearchService`.
- **Launcher:** ponto único de entrada para execução local.
- **Testes:** validação automatizada com mocks, sem chamadas externas.

## Fluxo atual

```text
GET /api/search
       |
       v
SearchService
   |-- ViaCEP: CEP -> endereço
   |-- Google Geocoding: endereço -> coordenadas
   |-- Google Places: categoria + círculo -> leads
   `-- Haversine: confirmação do raio -> SearchResult

Streamlit
   `-- SearchRequest -> SearchService -> SearchResult -> tabela/CSV
```

## Limites explícitos

Nesta versão não existem:

- persistência em banco de dados;
- autenticação;
- inteligência artificial;
- exportação Excel;
- paginação, retry ou métricas;
- filtros, paginação ou customização visual avançada.
