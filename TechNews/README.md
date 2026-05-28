# Portal Uberlândia Notícias — Back-end Python

## Estrutura

```
portal-uberlandia/
├── app.py              ← Aplicação Flask principal
├── requirements.txt    ← Dependências Python (inclui gunicorn)
├── database/
│   └── portal.db       ← Criado automaticamente na 1ª execução
├── uploads/            ← Banners enviados pelos anunciantes
├── templates/          ← Coloque os .html aqui para servir via Flask
└── static/             ← Coloque o style.css e logo.png aqui
```

---

## Desenvolvimento local

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar o servidor de desenvolvimento
python app.py
```

O servidor sobe em **http://localhost:5000** e cria o banco SQLite automaticamente.

> ⚠️ `python app.py` usa o servidor embutido do Flask com `debug=False`.
> **Nunca use esse modo para receber acessos reais** — ele é de thread única e não é seguro.

---

## Produção com Gunicorn + Nginx

### Por que Gunicorn?

O servidor embutido do Flask (`app.run(debug=True)`) é de **uso exclusivo em desenvolvimento**: processa uma requisição por vez e expõe detalhes internos do sistema nos erros. O **Gunicorn** é um servidor WSGI de produção que:

- Roda **múltiplos workers** em paralelo (`-w 4` = 4 processos)
- Não expõe tracebacks para o usuário final
- Integra com o **Nginx**, que fica na frente como proxy reverso

### Passo a passo (servidor Linux / VPS)

```bash
# 1. Instalar dependências (já inclui gunicorn)
pip install -r requirements.txt

# 2. Testar se o Gunicorn sobe corretamente
gunicorn -w 4 -b 127.0.0.1:5000 app:app

# 3. Em produção, rodar em segundo plano com o systemd ou nohup:
gunicorn -w 4 -b 127.0.0.1:5000 app:app --daemon --pid gunicorn.pid
```

### Configuração do Nginx (proxy reverso)

Crie o arquivo `/etc/nginx/sites-available/portal`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;

    # Encaminha todas as requisições para o Gunicorn
    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Serve os uploads diretamente pelo Nginx (mais eficiente)
    location /uploads/ {
        alias /caminho/para/portal-uberlandia/uploads/;
    }
}
```

Ative o site:

```bash
ln -s /etc/nginx/sites-available/portal /etc/nginx/sites-enabled/
nginx -t          # testa a configuração
systemctl reload nginx
```

---

## Deploy em plataformas de nuvem

### PythonAnywhere (gratuito para projetos de estudo)

1. Faça upload dos arquivos ou clone via `git clone`
2. Em **Web > Add a new web app**, escolha **Manual configuration** e **Python 3.11**
3. Configure o **WSGI file** para apontar para `app`:
   ```python
   from app import app as application
   ```
4. Clique em **Reload** — pronto, sem precisar configurar Gunicorn manualmente

### Railway / Render

Adicione um arquivo `Procfile` na raiz do projeto:

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

Faça o deploy pelo painel da plataforma conectando o repositório GitHub. O `$PORT` é injetado automaticamente pelo ambiente.

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

---

## Banco de Dados (SQLite)

As tabelas são criadas automaticamente na primeira execução:

- **clientes** — leitores cadastrados
- **contatos** — mensagens recebidas
- **vendas** — orçamentos de publicidade
- **anuncios** — configurações técnicas dos anúncios
- **candidatos** — currículos enviados
