# Problemática

## O problema

No campus, os pedidos de suporte de TI chegam por e-mail, WhatsApp e no corredor.
Sem um registro único:

- ninguém sabe **há quanto tempo** um problema está esperando nem se o prazo já estourou;
- chamados são **fechados sem registro da solução**, e o mesmo defeito volta sem histórico;
- alguns técnicos **acumulam chamados** enquanto outros ficam livres;
- um problema de rede que para um laboratório inteiro recebe a **mesma prioridade** de um teclado com defeito.

## Quem usa

| Perfil | O que faz no sistema |
|---|---|
| Solicitante (aluno, professor, secretaria) | abre o chamado e acompanha o status |
| Técnico de TI | recebe o chamado, atende e fecha com a solução escrita |
| Coordenação de TI | consulta os chamados fora do prazo (`GET /chamados/fora-do-prazo`) |

## Por que cada tipo tem um prazo (SLA)

| Tipo | SLA | Motivo |
|---|---|---|
| Rede | 8 h | afeta salas e laboratórios inteiros ao mesmo tempo |
| Software | 24 h | quase sempre resolvido remotamente (instalação, licença, acesso) |
| Hardware | 48 h | pode depender de peça de reposição ou de visita presencial |

O limite de **5 chamados abertos por técnico** distribui a carga da equipe e impede
que um chamado fique parado na fila de alguém sobrecarregado.

## Dados de exemplo (`app/data/*.json`)

Os arquivos JSON vêm com uma situação real de uma semana no campus, pronta para a
demonstração no Swagger:

- **5 solicitantes** (alunos, professor e secretaria) e **3 técnicos**;
- **9 chamados** dos três tipos: 2 fechados com solução, 6 em andamento, 1 aberto sem técnico;
- **5 chamados fora do prazo** em 27/11/2026, incluindo um fechado depois do SLA (chamado 2);
- o técnico **Marcos Lima já tem 4 chamados abertos**: atribuir mais um chega ao limite
  e o seguinte devolve **409**.

### Roteiro sugerido para a apresentação

1. `GET /chamados?tipo=rede` lista os chamados de rede.
2. `GET /chamados/999` devolve 404.
3. `POST /chamados/6/fechar` com `{"solucao": ""}` devolve 422 (não fecha sem solução escrita).
4. Atribuir dois chamados novos ao técnico 1: o segundo devolve 409 (limite de 5).
5. `GET /chamados/fora-do-prazo` mostra o cálculo do tema.
