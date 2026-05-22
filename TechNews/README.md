# Portal Uberlândia Notícias — Back-end Python

## Estrutura

```
portal-uberlandia/
├── app.py              ← Aplicação Flask principal
├── requirements.txt    ← Dependências Python
├── database/
│   └── portal.db       ← Criado automaticamente na 1ª execução
├── uploads/            ← Banners enviados pelos anunciantes
├── templates/          ← Coloque os .html aqui para servir via Flask
└── static/             ← Coloque o style.css e logo.png aqui
```

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar o servidor
python app.py
```

O servidor sobe em **http://localhost:5000** e cria o banco SQLite automaticamente.

---

## Endpoints da API

| Método | Rota               | Página do Front      | Descrição                          |
|--------|--------------------|----------------------|------------------------------------|
| POST   | `/api/clientes`    | `clientes.html`      | Cadastro de leitor                 |
| GET    | `/api/clientes`    | —                    | Lista todos os leitores            |
| POST   | `/api/contatos`    | `contato.html`       | Envio de mensagem/sugestão         |
| GET    | `/api/contatos`    | —                    | Lista todas as mensagens           |
| POST   | `/api/vendas`      | `vendas.html`        | Solicitação de orçamento de anúncio|
| GET    | `/api/vendas`      | —                    | Lista solicitações                 |
| POST   | `/api/anuncios`    | `anuncio.html`       | Configuração técnica do anúncio    |
| GET    | `/api/anuncios`    | —                    | Lista anúncios (sem senha)         |
| POST   | `/api/candidatos`  | `trabalhe.html`      | Envio de currículo                 |
| GET    | `/api/candidatos`  | —                    | Lista candidatos                   |
| GET    | `/api/status`      | —                    | Health check do servidor           |

### Exemplos de chamada com `fetch` (para usar no front)

```javascript
// clientes.html — ao submeter o formulário
const formData = new FormData(document.querySelector('form'));
const res = await fetch('http://localhost:5000/api/clientes', {
    method: 'POST',
    body: formData
});
const json = await res.json();
alert(json.message);
```

---

## Banco de Dados (SQLite)

As tabelas são criadas automaticamente:

- **clientes** — leitores cadastrados
- **contatos** — mensagens recebidas
- **vendas** — orçamentos de publicidade
- **anuncios** — configurações técnicas dos anúncios
- **candidatos** — currículos enviados
