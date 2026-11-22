# Chamados de TI do campus

Backend em FastAPI (POO, 4 camadas) para abrir, atribuir e fechar chamados de TI.
Prova final · Programação Orientada a Objetos · FATEC Mogi das Cruzes.

## Como rodar

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

```bash
pytest
```

## Estrutura

```
app/
  data/         chamados.json, solicitantes.json, tecnicos.json e RepositorioJson
  models/       Chamado (ABC) -> Hardware, Software, Rede; Solicitante; Tecnico; excecoes.py
  controllers/  regras de aplicação (chamam models e repositório)
  routes/       FastAPI: rotas, schemas Pydantic e tradução de erros em HTTP
tests/          pytest
main.py
```

## Regras de negócio

| Código | Regra |
|---|---|
| RN01 | SLA por tipo (horas): Hardware 48, Software 24, Rede 8 (`prazo_sla()` polimórfico) |
| RN02 | Chamado não fecha sem solução escrita (422) |
| RN03 | Técnico com no máximo 5 chamados abertos (409) |
| RN04 | Chamado fechado não pode ser alterado, reatribuído nem fechado de novo (409) |
| RN05 | Título com ao menos 3 caracteres; descrição não vazia; e-mail válido (422) |
| RN06 | Solicitante com e-mail duplicado (409) |

## Rotas

| Método | Caminho | Descrição | Códigos |
|---|---|---|---|
| GET | /chamados?tipo= | lista com filtro | 200, 422 |
| GET | /chamados/{id} | busca por id | 200, 404 |
| POST | /chamados | cria | 201, 404, 409, 422 |
| PUT | /chamados/{id} | altera título, descrição ou técnico | 200, 404, 409, 422 |
| POST | /chamados/{id}/fechar | fecha com solução | 200, 404, 409, 422 |
| DELETE | /chamados/{id} | remove | 204, 404 |
| GET | /chamados/fora-do-prazo | cálculo: chamados que estouraram o SLA | 200 |
| POST | /solicitantes | cria solicitante | 201, 409, 422 |
| POST | /tecnicos | cria técnico | 201, 422 |

## Erros

| Exceção | HTTP |
|---|---|
| NaoEncontradoErro | 404 |
| ConflitoErro | 409 |
| DadoInvalidoErro | 422 |
