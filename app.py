from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configurações gerais
app.secret_key = "segredo_super_secreto"  # Chave para gerenciar sessões
base_dir = os.path.abspath(os.path.dirname(__file__))  # Diretório base
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'meu_banco.db')}"  # Caminho absoluto para o banco
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Evita warnings do SQLAlchemy

db = SQLAlchemy(app)  # Inicializa o banco de dados

# Usuários para autenticação básica
USUARIOS = {
    "admin@rally.com": "123"  # Email e senha para autenticação
}

# Modelo da tabela Metas
class Meta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    pontuacao = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Meta {self.descricao} - {self.pontuacao}>"

# Modelo da tabela Pontuações
class Pontuacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grupo = db.Column(db.String(50), nullable=False)
    pontos = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Pontuacao {self.grupo} - {self.pontos}>"

# Rota para login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        # Validação de credenciais
        if email in USUARIOS and USUARIOS[email] == senha:
            session["usuario"] = email
            return redirect(url_for("home"))
        else:
            flash("Email ou senha inválidos!", "error")
    return render_template("login.html")

# Rota para logout
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

# Rota para página inicial
@app.route("/")
@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

# Rota para gerenciamento de metas
@app.route("/metas", methods=['GET', 'POST'])
def metas():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        try:
            pontuacao = int(request.form.get('pontuacao', 0))
        except ValueError:
            flash("Pontuação deve ser um número.", "error")
            return redirect(url_for('metas'))

        nova_meta = Meta(descricao=descricao, pontuacao=pontuacao)
        db.session.add(nova_meta)
        db.session.commit()
        return redirect(url_for('metas'))

    metas_lista = Meta.query.all()
    return render_template("metas.html", metas=metas_lista)

# Rota para editar meta
@app.route("/metas/editar/<int:id>", methods=['GET', 'POST'])
def editar_meta(id):
    meta = Meta.query.get_or_404(id)
    if request.method == 'POST':
        meta.descricao = request.form.get('descricao')
        try:
            meta.pontuacao = int(request.form.get('pontuacao', 0))
        except ValueError:
            flash("Pontuação deve ser um número.", "error")
            return redirect(url_for('editar_meta', id=id))
        db.session.commit()
        return redirect(url_for('metas'))

    return render_template("editar_meta.html", meta=meta)

# Rota para excluir meta
@app.route("/metas/excluir/<int:id>")
def excluir_meta(id):
    meta = Meta.query.get_or_404(id)
    db.session.delete(meta)
    db.session.commit()
    return redirect(url_for('metas'))

# Rota para gerenciamento de pontuações
@app.route("/pontuacao", methods=['GET', 'POST'])
def pontuacao():
    if request.method == 'POST':
        grupo = request.form.get('grupo')
        try:
            pontos = int(request.form.get('pontos', 0))
        except ValueError:
            flash("Pontos devem ser um número.", "error")
            return redirect(url_for('pontuacao'))

        nova_pontuacao = Pontuacao(grupo=grupo, pontos=pontos)
        db.session.add(nova_pontuacao)
        db.session.commit()
        return redirect(url_for('pontuacao'))

    pontuacoes_lista = Pontuacao.query.all()
    return render_template("pontuacao.html", pontuacoes=pontuacoes_lista)

# Rota para editar pontuação
@app.route("/pontuacao/editar/<int:id>", methods=['GET', 'POST'])
def editar_pontuacao(id):
    pontuacao = Pontuacao.query.get_or_404(id)
    if request.method == 'POST':
        pontuacao.grupo = request.form.get('grupo')
        try:
            pontuacao.pontos = int(request.form.get('pontos', 0))
        except ValueError:
            flash("Pontos devem ser um número.", "error")
            return redirect(url_for('editar_pontuacao', id=id))
        db.session.commit()
        return redirect(url_for('pontuacao'))

    return render_template("editar_pontuacao.html", pontuacao=pontuacao)

# Rota para excluir pontuação
@app.route("/pontuacao/excluir/<int:id>")
def excluir_pontuacao(id):
    pontuacao = Pontuacao.query.get_or_404(id)
    db.session.delete(pontuacao)
    db.session.commit()
    return redirect(url_for('pontuacao'))

# Rota para resultados
@app.route("/resultados")
def resultados():
    grupos = Pontuacao.query.with_entities(
        Pontuacao.grupo,
        db.func.sum(Pontuacao.pontos).label('total_pontos')
    ).group_by(Pontuacao.grupo).order_by(db.func.sum(Pontuacao.pontos).desc()).all()

    return render_template("resultados.html", grupos=grupos)

# Tratamento de erro 404
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists(os.path.join(base_dir, "meu_banco.db")):
            db.create_all()
    app.run(debug=True)
