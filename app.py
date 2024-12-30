from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)

app.secret_key = "segredo_super_secreto"

USUARIOS = {
    "admin@rally.com": "123",  # Email e senha para autenticação
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meu_banco.db'  # Banco SQLite
# Desativa notificações do SQLAlchemy
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)  # Inicializa o banco de dados

# Modelo da tabela Metas
class Meta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    pontuacao = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Meta {self.descricao} - {self.pontuacao}>"

# Modelo da tabela Pontuacoes
class Pontuacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grupo = db.Column(db.String(50), nullable=False)
    pontos = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Pontuacao {self.grupo} - {self.pontos}>"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        # Verifica se as credenciais estão corretas
        if email in USUARIOS and USUARIOS[email] == senha:
            session["usuario"] = email  # Salva o usuário na sessão
            # Redireciona para a página inicial
            return redirect(url_for("home"))
        else:
            flash("Email ou senha inválidos!", "error")  # Mensagem de erro

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("usuario", None)  # Remove o usuário da sessão
    return redirect(url_for("login"))


@app.route("/")
@app.route("/home")
def home():
    if "usuario" not in session:  # Verifica se o usuário está logado
        return redirect(url_for("login"))  # Redireciona para a página de login
    return render_template("home.html")


@app.route("/metas", methods=['GET', 'POST'])
def metas():
    if request.method == 'POST':
        descricao = request.form['descricao']
        pontuacao = int(request.form['pontuacao'])

        # Cria uma nova meta no banco de dados
        nova_meta = Meta(descricao=descricao, pontuacao=pontuacao)
        db.session.add(nova_meta)
        db.session.commit()

        return redirect(url_for('metas'))  # Redireciona para a lista de metas

    # Exibe as metas cadastradas
    metas_lista = Meta.query.all()
    return render_template("metas.html", metas=metas_lista)


@app.route("/metas/editar/<int:id>", methods=['GET', 'POST'])
def editar_meta(id):
    meta = Meta.query.get_or_404(id)
    if request.method == 'POST':
        meta.descricao = request.form['descricao']
        meta.pontuacao = int(request.form['pontuacao'])
        db.session.commit()
        return redirect(url_for('metas'))

    return render_template("editar_meta.html", meta=meta)


@app.route("/metas/excluir/<int:id>")
def excluir_meta(id):
    meta = Meta.query.get_or_404(id)
    db.session.delete(meta)
    db.session.commit()
    return redirect(url_for('metas'))


@app.route("/pontuacao", methods=['GET', 'POST'])
def pontuacao():
    if request.method == 'POST':
        grupo = request.form['grupo']
        pontos = int(request.form['pontos'])

        # Cria uma nova pontuação no banco de dados
        nova_pontuacao = Pontuacao(grupo=grupo, pontos=pontos)
        db.session.add(nova_pontuacao)
        db.session.commit()

        # Redireciona para a página de pontuação
        return redirect(url_for('pontuacao'))

    # Exibe as pontuações dos grupos
    pontuacoes_lista = Pontuacao.query.all()
    return render_template("pontuacao.html", pontuacoes=pontuacoes_lista)


@app.route("/pontuacao/editar/<int:id>", methods=['GET', 'POST'])
def editar_pontuacao(id):
    pontuacao = Pontuacao.query.get_or_404(id)
    if request.method == 'POST':
        pontuacao.grupo = request.form['grupo']
        pontuacao.pontos = int(request.form['pontos'])
        db.session.commit()
        return redirect(url_for('pontuacao'))

    return render_template("editar_pontuacao.html", pontuacao=pontuacao)


@app.route("/pontuacao/excluir/<int:id>")
def excluir_pontuacao(id):
    pontuacao = Pontuacao.query.get_or_404(id)
    db.session.delete(pontuacao)
    db.session.commit()
    return redirect(url_for('pontuacao'))


@app.route("/resultados")
def resultados():
    # Calcula a pontuação total de cada grupo
    grupos = Pontuacao.query.with_entities(Pontuacao.grupo, db.func.sum(Pontuacao.pontos).label('total_pontos')) \
        .group_by(Pontuacao.grupo) \
        .order_by(db.func.sum(Pontuacao.pontos).desc()).all()

    return render_template("resultados.html", grupos=grupos)


if __name__ == "__main__":
    # Criação de tabelas apenas se não existirem
    with app.app_context():
        if not os.path.exists("meu_banco.db"):  # Verifica se o arquivo já existe
            db.create_all()  # Cria as tabelas apenas na primeira execução
    app.run(debug=True)
