from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.secret_key = "agrogestor123"

# ==================================================
# CONFIGURAÇÃO
# ==================================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agrogestor.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==================================================
# TABELA DE USUÁRIOS
# ==================================================

class Usuario(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==================================================
# PROTEÇÃO DAS PÁGINAS
# ==================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# ==================================================
# LOGIN
# ==================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario and check_password_hash(
            usuario.senha,
            senha
        ):

            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            session["usuario_email"] = usuario.email

            return redirect(
                url_for("index")
            )

        flash(
            "E-mail ou senha incorretos.",
            "erro"
        )

    return render_template(
        "login.html"
    )


# ==================================================
# CADASTRO
# ==================================================

@app.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def cadastro():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        # Verificar campos
        if not nome or not email or not senha:

            flash(
                "Preencha todos os campos.",
                "erro"
            )

            return redirect(
                url_for("cadastro")
            )

        # Verificar e-mail
        if "@" not in email:

            flash(
                "Digite um e-mail válido.",
                "erro"
            )

            return redirect(
                url_for("cadastro")
            )

        # Verificar tamanho da senha
        if len(senha) < 6:

            flash(
                "A senha precisa ter pelo menos 6 caracteres.",
                "erro"
            )

            return redirect(
                url_for("cadastro")
            )

        # Confirmar senha
        if senha != confirmar_senha:

            flash(
                "As senhas não são iguais.",
                "erro"
            )

            return redirect(
                url_for("cadastro")
            )

        # Verificar se e-mail já existe
        usuario_existente = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario_existente:

            flash(
                "Este e-mail já está cadastrado.",
                "erro"
            )

            return redirect(
                url_for("cadastro")
            )

        # Proteger senha
        senha_protegida = generate_password_hash(
            senha
        )

        # Criar usuário
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_protegida
        )

        db.session.add(
            novo_usuario
        )

        db.session.commit()

        flash(
            "Conta criada com sucesso!",
            "sucesso"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "cadastro.html"
    )


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==================================================
# TABELA DE LOTES
# ==================================================

class Lote(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    animais = db.relationship(
        "Animal",
        backref="lote",
        lazy=True
    )


# ==================================================
# TABELA DE ANIMAIS
# ==================================================

class Animal(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    brinco = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    nome = db.Column(
        db.String(100)
    )

    raca = db.Column(
        db.String(100),
        nullable=False
    )

    situacao = db.Column(
        db.String(50),
        nullable=False,
        default="Vazia"
    )

    lote_id = db.Column(
        db.Integer,
        db.ForeignKey("lote.id")
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==================================================
# TABELA DE CUSTOS E RECEITAS
# ==================================================

class Custo(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tipo = db.Column(
        db.String(30),
        nullable=False
    )

    alvo = db.Column(
        db.String(100),
        nullable=False
    )

    descricao = db.Column(
        db.String(255),
        nullable=False
    )

    valor = db.Column(
        db.Float,
        nullable=False
    )

    data = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==================================================
# CRIAR BANCO
# ==================================================

with app.app_context():

    db.create_all()


# ==================================================
# PAINEL
# ==================================================

@app.route("/")
@login_required
def index():

    total_animais = Animal.query.count()

    total_custos = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Despesa"
    ).scalar() or 0

    total_receitas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Receita"
    ).scalar() or 0

    return render_template(
        "index.html",
        total_animais=total_animais,
        total_custos=total_custos,
        total_receitas=total_receitas
    )


# ==================================================
# ANIMAIS
# ==================================================

@app.route("/animais")
@login_required
def animais():

    lista_animais = Animal.query.order_by(
        Animal.id.desc()
    ).all()

    return render_template(
        "animais.html",
        animais=lista_animais
    )


# ==================================================
# CADASTRAR ANIMAL
# ==================================================

@app.route(
    "/animais/cadastrar",
    methods=["GET", "POST"]
)
@login_required
def cadastrar_animal():

    if request.method == "POST":

        brinco = request.form.get(
            "brinco",
            ""
        ).strip()

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        raca = request.form.get(
            "raca",
            ""
        ).strip()

        situacao = request.form.get(
            "situacao",
            "Vazia"
        )

        lote_id = request.form.get(
            "lote_id"
        )

        if not brinco or not raca:

            return (
                "Erro: brinco e raça são obrigatórios."
            )

        animal_existente = Animal.query.filter_by(
            brinco=brinco
        ).first()

        if animal_existente:

            return (
                "Erro: já existe um animal com esse brinco."
            )

        if lote_id:

            lote_id = int(lote_id)

        else:

            lote_id = None

        novo_animal = Animal(
            brinco=brinco,
            nome=nome,
            raca=raca,
            situacao=situacao,
            lote_id=lote_id
        )

        db.session.add(
            novo_animal
        )

        db.session.commit()

        return redirect(
            url_for("animais")
        )

    lotes = Lote.query.order_by(
        Lote.nome.asc()
    ).all()

    return render_template(
        "cadastrar_animal.html",
        lotes=lotes
    )


# ==================================================
# EXCLUIR ANIMAL
# ==================================================

@app.route(
    "/animais/excluir/<int:id>"
)
@login_required
def excluir_animal(id):

    animal = db.session.get(
        Animal,
        id
    )

    if animal is None:

        return "Animal não encontrado."

    db.session.delete(
        animal
    )

    db.session.commit()

    return redirect(
        url_for("animais")
    )


# ==================================================
# CUSTOS E RECEITAS
# ==================================================

@app.route(
    "/custos",
    methods=["GET", "POST"]
)
@login_required
def custos():

    if request.method == "POST":

        tipo = request.form.get(
            "tipo"
        )

        alvo = request.form.get(
            "alvo",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        valor = request.form.get(
            "valor",
            ""
        ).strip()

        if tipo not in [
            "Despesa",
            "Receita"
        ]:

            return "Erro: tipo inválido."

        if not alvo or not descricao or not valor:

            return "Erro: preencha todos os campos."

        try:

            valor = float(
                valor.replace(",", ".")
            )

        except ValueError:

            return "Erro: valor inválido."

        novo_custo = Custo(
            tipo=tipo,
            alvo=alvo,
            descricao=descricao,
            valor=valor
        )

        db.session.add(
            novo_custo
        )

        db.session.commit()

        return redirect(
            url_for("custos")
        )

    lista_custos = Custo.query.order_by(
        Custo.data.desc()
    ).all()

    return render_template(
        "custos.html",
        custos=lista_custos
    )


# ==================================================
# RELATÓRIOS
# ==================================================

@app.route("/relatorios")
@login_required
def relatorios():

    total_despesas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Despesa"
    ).scalar() or 0

    total_receitas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Receita"
    ).scalar() or 0

    vacas_paridas = Animal.query.filter_by(
        situacao="Parida"
    ).count()

    vacas_gestantes = Animal.query.filter_by(
        situacao="Gestante"
    ).count()

    vacas_vazias = Animal.query.filter_by(
        situacao="Vazia"
    ).count()

    total_animais = Animal.query.count()

    if total_animais > 0:

        media_por_animal = (
            total_despesas / total_animais
        )

    else:

        media_por_animal = 0

    return render_template(
        "relatorios.html",
        total_despesas=total_despesas,
        total_receitas=total_receitas,
        vacas_paridas=vacas_paridas,
        vacas_gestantes=vacas_gestantes,
        vacas_vazias=vacas_vazias,
        total_animais=total_animais,
        media_por_animal=media_por_animal
    )


# ==================================================
# INICIAR SERVIDOR
# ==================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )