"""
Portal Uberlândia Notícias — Back-end Flask
Trabalho de Tecnologias para Internet I — Uniube 2026
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import re
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# ── Configurações ──────────────────────────────────────────────────────────────

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATABASE     = os.path.join(BASE_DIR, "database", "portal.db")
UPLOAD_DIR   = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024   # 5 MB
app.config["SECRET_KEY"] = "uniube-2026-portal-uberlandia"
CORS(app)   # libera CORS para o front chamar direto durante o desenvolvimento


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_db():
    """Retorna uma conexão com o banco SQLite com Row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


def validate_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def success(data=None, message="OK", status=200):
    return jsonify({"ok": True, "message": message, "data": data}), status


def error(message="Erro desconhecido", status=400):
    return jsonify({"ok": False, "message": message}), status


# ── Banco de dados ─────────────────────────────────────────────────────────────

def init_db():
    """Cria todas as tabelas caso ainda não existam."""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    sql = """
    -- Leitores cadastrados (clientes.html)
    CREATE TABLE IF NOT EXISTS clientes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        nome            TEXT    NOT NULL,
        email           TEXT    NOT NULL UNIQUE,
        data_nascimento TEXT,
        genero          TEXT    CHECK(genero IN ('m','f','o')),
        bairro          TEXT,
        criado_em       TEXT    DEFAULT (datetime('now','localtime'))
    );

    -- Mensagens de contato (contato.html)
    CREATE TABLE IF NOT EXISTS contatos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nome        TEXT    NOT NULL,
        assunto     TEXT    NOT NULL,
        mensagem    TEXT    NOT NULL,
        telefone    TEXT,
        resposta    TEXT    CHECK(resposta IN ('email','tel')),
        criado_em   TEXT    DEFAULT (datetime('now','localtime'))
    );

    -- Solicitações de anúncio (vendas.html)
    CREATE TABLE IF NOT EXISTS vendas (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa     TEXT    NOT NULL,
        tipo        TEXT    NOT NULL,
        dias        INTEGER NOT NULL CHECK(dias BETWEEN 1 AND 30),
        data_inicio TEXT,
        investimento REAL   NOT NULL,
        criado_em   TEXT    DEFAULT (datetime('now','localtime'))
    );

    -- Configurações técnicas de anúncio (anuncio.html)
    CREATE TABLE IF NOT EXISTS anuncios (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        url_destino     TEXT    NOT NULL,
        cor_arte        TEXT    DEFAULT '#004a80',
        arquivo_banner  TEXT,           -- nome do arquivo salvo em /uploads
        senha_hash      TEXT    NOT NULL,
        token_painel    TEXT    NOT NULL UNIQUE,
        criado_em       TEXT    DEFAULT (datetime('now','localtime'))
    );

    -- Candidatos (trabalhe.html)
    CREATE TABLE IF NOT EXISTS candidatos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        area        TEXT    NOT NULL,
        experiencia INTEGER NOT NULL DEFAULT 0,
        portfolio   TEXT,
        inicio_imediato INTEGER DEFAULT 0,   -- 0 = não, 1 = sim
        resumo      TEXT,
        criado_em   TEXT    DEFAULT (datetime('now','localtime'))
    );
    """
    with get_db() as conn:
        conn.executescript(sql)

    print(f"[DB] Banco inicializado em: {DATABASE}")


# ── Rotas de arquivos estáticos (opcional — facilita testes locais) ────────────

@app.route("/")
def index():
    """Serve o index.html se estiver na pasta templates; útil para testes."""
    try:
        return render_template("index.html")
    except Exception:
        return "<p>Back-end rodando! Coloque os .html em /templates para servi-los.</p>"


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 1 — Cadastro de Clientes  (POST /api/clientes)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/clientes", methods=["POST"])
def cadastrar_cliente():
    """
    Campos esperados (form-data ou JSON):
      nome_cliente, email_cliente, data_nascimento (opt),
      genero (opt), bairro (opt)
    """
    data = request.form if request.form else request.get_json(silent=True) or {}

    nome  = (data.get("nome_cliente") or "").strip()
    email = (data.get("email_cliente") or "").strip().lower()

    if not nome:
        return error("O campo 'Nome Completo' é obrigatório.")
    if not email or not validate_email(email):
        return error("Informe um e-mail válido.")

    data_nasc   = data.get("data_nascimento") or None
    genero      = data.get("genero") or None
    bairro      = data.get("bairro") or None

    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO clientes (nome, email, data_nascimento, genero, bairro)
                   VALUES (?,?,?,?,?)""",
                (nome, email, data_nasc, genero, bairro)
            )
        return success(message="Cadastro realizado com sucesso!", status=201)

    except sqlite3.IntegrityError:
        return error("Este e-mail já está cadastrado.", 409)


@app.route("/api/clientes", methods=["GET"])
def listar_clientes():
    """Lista todos os clientes cadastrados (uso administrativo)."""
    with get_db() as conn:
        rows = conn.execute("SELECT id, nome, email, bairro, criado_em FROM clientes ORDER BY id DESC").fetchall()
    return success([dict(r) for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 2 — Contato  (POST /api/contatos)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/contatos", methods=["POST"])
def enviar_contato():
    """
    Campos esperados:
      nome_contato, assunto, mensagem, telefone (opt), resposta (opt)
    """
    data = request.form if request.form else request.get_json(silent=True) or {}

    nome     = (data.get("nome_contato") or "").strip()
    assunto  = (data.get("assunto") or "").strip()
    mensagem = (data.get("mensagem") or "").strip()

    if not nome:
        return error("Informe seu nome.")
    if not mensagem:
        return error("A mensagem não pode estar vazia.")

    assuntos_validos = {"sugestao", "elogio", "erro"}
    if assunto not in assuntos_validos:
        assunto = "sugestao"

    telefone = (data.get("telefone") or "").strip() or None
    resposta = data.get("resposta") or None
    if resposta not in ("email", "tel", None):
        resposta = None

    with get_db() as conn:
        conn.execute(
            """INSERT INTO contatos (nome, assunto, mensagem, telefone, resposta)
               VALUES (?,?,?,?,?)""",
            (nome, assunto, mensagem, telefone, resposta)
        )
    return success(message="Mensagem enviada! Retornaremos em breve.", status=201)


@app.route("/api/contatos", methods=["GET"])
def listar_contatos():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM contatos ORDER BY id DESC").fetchall()
    return success([dict(r) for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 3 — Solicitação de Venda de Anúncio  (POST /api/vendas)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/vendas", methods=["POST"])
def solicitar_venda():
    """
    Campos esperados:
      empresa, tipo, dias, data_inicio (opt), investimento
    """
    data = request.form if request.form else request.get_json(silent=True) or {}

    empresa     = (data.get("empresa") or "").strip()
    tipo        = (data.get("tipo") or "").strip()
    dias_raw    = data.get("dias", "")
    invest_raw  = data.get("investimento", "100")
    data_inicio = data.get("data_inicio") or None

    if not empresa:
        return error("Informe o nome da empresa.")

    tipos_validos = {"banner_topo", "lateral", "publieditorial"}
    if tipo not in tipos_validos:
        return error("Tipo de anúncio inválido.")

    try:
        dias = int(dias_raw)
        if not (1 <= dias <= 30):
            raise ValueError
    except (ValueError, TypeError):
        return error("A duração deve ser entre 1 e 30 dias.")

    try:
        investimento = float(str(invest_raw).replace(",", "."))
        if investimento < 100:
            raise ValueError
    except (ValueError, TypeError):
        return error("Investimento mínimo é R$ 100,00.")

    with get_db() as conn:
        conn.execute(
            """INSERT INTO vendas (empresa, tipo, dias, data_inicio, investimento)
               VALUES (?,?,?,?,?)""",
            (empresa, tipo, dias, data_inicio, investimento)
        )
    return success(message="Solicitação recebida! Nossa equipe de vendas entrará em contato.", status=201)


@app.route("/api/vendas", methods=["GET"])
def listar_vendas():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM vendas ORDER BY id DESC").fetchall()
    return success([dict(r) for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 4 — Configuração de Anúncio  (POST /api/anuncios)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/anuncios", methods=["POST"])
def configurar_anuncio():
    """
    Campos esperados (multipart/form-data):
      url_destino, cor_arte (opt), arquivo_banner (file, opt),
      senha_painel, termos (checkbox)
    """
    import hashlib

    url_destino = (request.form.get("url_destino") or "").strip()
    cor_arte    = (request.form.get("cor_arte") or "#004a80").strip()
    senha       = request.form.get("senha_painel") or ""
    termos      = request.form.get("termos")

    if not url_destino or not url_destino.startswith("http"):
        return error("Informe uma URL de destino válida (deve começar com http/https).")
    if len(senha) < 6:
        return error("A senha deve ter pelo menos 6 caracteres.")
    if not termos:
        return error("É necessário aceitar as políticas de publicidade.")

    # Hash simples da senha (SHA-256). Em produção usar bcrypt/argon2.
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    token      = str(uuid.uuid4())

    # Upload do banner (opcional)
    arquivo_banner = None
    if "arquivo_banner" in request.files:
        f = request.files["arquivo_banner"]
        if f and f.filename and allowed_file(f.filename):
            nome_seguro    = f"{token[:8]}_{secure_filename(f.filename)}"
            f.save(os.path.join(UPLOAD_DIR, nome_seguro))
            arquivo_banner = nome_seguro

    with get_db() as conn:
        conn.execute(
            """INSERT INTO anuncios (url_destino, cor_arte, arquivo_banner, senha_hash, token_painel)
               VALUES (?,?,?,?,?)""",
            (url_destino, cor_arte, arquivo_banner, senha_hash, token)
        )

    return success(
        data={"token_painel": token},
        message="Anúncio configurado! Guarde seu token para acessar o painel de métricas.",
        status=201
    )


@app.route("/api/anuncios", methods=["GET"])
def listar_anuncios():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, url_destino, cor_arte, arquivo_banner, criado_em FROM anuncios ORDER BY id DESC"
        ).fetchall()
    return success([dict(r) for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 5 — Candidatos (Trabalhe Conosco)  (POST /api/candidatos)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/candidatos", methods=["POST"])
def cadastrar_candidato():
    """
    Campos esperados:
      area, experiencia, portfolio (opt), inicio ('sim'|'nao'), resumo (opt)
    """
    data = request.form if request.form else request.get_json(silent=True) or {}

    area      = (data.get("area") or "").strip()
    exp_raw   = data.get("experiencia", "0")
    portfolio = (data.get("portfolio") or "").strip() or None
    inicio    = data.get("inicio", "nao")
    resumo    = (data.get("resumo") or "").strip() or None

    areas_validas = {"redacao", "fotografia", "ti"}
    if area not in areas_validas:
        return error("Área de interesse inválida.")

    try:
        experiencia = int(exp_raw)
        if experiencia < 0:
            raise ValueError
    except (ValueError, TypeError):
        return error("Anos de experiência inválido.")

    if portfolio and not portfolio.startswith("http"):
        return error("O link do portfólio deve começar com http/https.")

    inicio_imediato = 1 if inicio == "sim" else 0

    with get_db() as conn:
        conn.execute(
            """INSERT INTO candidatos (area, experiencia, portfolio, inicio_imediato, resumo)
               VALUES (?,?,?,?,?)""",
            (area, experiencia, portfolio, inicio_imediato, resumo)
        )
    return success(message="Currículo enviado com sucesso! Entraremos em contato.", status=201)


@app.route("/api/candidatos", methods=["GET"])
def listar_candidatos():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM candidatos ORDER BY id DESC").fetchall()
    return success([dict(r) for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT 6 — Health check  (GET /api/status)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/status")
def status():
    """Verifica se o servidor e o banco estão operacionais."""
    try:
        with get_db() as conn:
            conn.execute("SELECT 1").fetchone()
        db_ok = True
    except Exception as e:
        db_ok = False

    return jsonify({
        "ok": True,
        "servidor": "Portal Uberlândia Notícias — Back-end Flask",
        "banco": "OK" if db_ok else "ERRO",
        "timestamp": datetime.now().isoformat()
    })


# ══════════════════════════════════════════════════════════════════════════════
#  Inicialização
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    print("\n🚀 Servidor rodando em http://localhost:5000")
    print("   Endpoints disponíveis:")
    print("   POST /api/clientes    — Cadastro de leitores")
    print("   POST /api/contatos    — Mensagens de contato")
    print("   POST /api/vendas      — Solicitação de anúncio")
    print("   POST /api/anuncios    — Configuração técnica de anúncio")
    print("   POST /api/candidatos  — Trabalhe conosco")
    print("   GET  /api/status      — Health check\n")
    app.run(debug=True, port=5000)
