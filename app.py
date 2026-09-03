from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# ==================================================
# CONFIGURAÇÃO
# ==================================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agrogestor.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


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
# CRIAR BANCO DE DADOS
# ==================================================

with app.app_context():
    db.create_all()


# ==================================================
# PAINEL PRINCIPAL
# ==================================================

@app.route("/")
def index():

    # Total de animais
    total_animais = Animal.query.count()

    # Total de despesas
    total_despesas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Despesa"
    ).scalar() or 0

    # Total de receitas
    total_receitas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Receita"
    ).scalar() or 0

    # Saldo
    saldo = total_receitas - total_despesas

    return render_template(
        "index.html",

        total_animais=total_animais,

        total_despesas=total_despesas,

        # Mantém compatibilidade com seu HTML antigo
        total_custos=total_despesas,

        total_receitas=total_receitas,

        saldo=saldo
    )


# ==================================================
# ANIMAIS
# ==================================================

@app.route("/animais")
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

        # Verificação dos campos obrigatórios
        if not brinco or not raca:

            return (
                "Erro: brinco e raça são obrigatórios."
            )

        # Verificar se o brinco já existe
        animal_existente = Animal.query.filter_by(
            brinco=brinco
        ).first()

        if animal_existente:

            return (
                "Erro: já existe um animal "
                "com esse brinco."
            )

        # Converter lote
        if lote_id:

            try:
                lote_id = int(lote_id)

            except ValueError:
                lote_id = None

        else:
            lote_id = None

        # Criar animal
        novo_animal = Animal(
            brinco=brinco,
            nome=nome,
            raca=raca,
            situacao=situacao,
            lote_id=lote_id
        )

        db.session.add(novo_animal)
        db.session.commit()

        return redirect(
            url_for("animais")
        )

    # Buscar lotes
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
def excluir_animal(id):

    animal = db.session.get(
        Animal,
        id
    )

    if animal is None:

        return "Animal não encontrado."

    db.session.delete(animal)
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
def custos():

    # ==================================================
    # CADASTRAR MOVIMENTAÇÃO
    # ==================================================

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

        # Verificar tipo
        if tipo not in [
            "Despesa",
            "Receita"
        ]:

            return "Erro: tipo inválido."

        # Verificar campos
        if not alvo or not descricao or not valor:

            return (
                "Erro: preencha todos os campos."
            )

        # Converter valor
        try:

            valor = float(
                valor.replace(",", ".")
            )

        except ValueError:

            return "Erro: valor inválido."

        # Não permitir valor zero ou negativo
        if valor <= 0:

            return (
                "Erro: o valor deve ser maior que zero."
            )

        # Criar lançamento
        novo_custo = Custo(
            tipo=tipo,
            alvo=alvo,
            descricao=descricao,
            valor=valor
        )

        db.session.add(novo_custo)
        db.session.commit()

        return redirect(
            url_for("custos")
        )


    # ==================================================
    # BUSCAR MOVIMENTAÇÕES
    # ==================================================

    lista_custos = Custo.query.order_by(
        Custo.data.desc()
    ).all()


    # ==================================================
    # CALCULAR DESPESAS
    # ==================================================

    total_despesas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Despesa"
    ).scalar() or 0


    # ==================================================
    # CALCULAR RECEITAS
    # ==================================================

    total_receitas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Receita"
    ).scalar() or 0


    # ==================================================
    # CALCULAR SALDO
    # ==================================================

    saldo = total_receitas - total_despesas


    # ==================================================
    # ENVIAR DADOS PARA custos.html
    # ==================================================

    return render_template(
        "custos.html",

        custos=lista_custos,

        total_despesas=total_despesas,

        total_receitas=total_receitas,

        saldo=saldo
    )


# ==================================================
# RELATÓRIOS
# ==================================================

@app.route("/relatorios")
def relatorios():

    # ==================================================
    # TOTAL DE DESPESAS
    # ==================================================

    total_despesas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Despesa"
    ).scalar() or 0


    # ==================================================
    # TOTAL DE RECEITAS
    # ==================================================

    total_receitas = db.session.query(
        db.func.sum(Custo.valor)
    ).filter(
        Custo.tipo == "Receita"
    ).scalar() or 0


    # ==================================================
    # SALDO
    # ==================================================

    saldo = total_receitas - total_despesas


    # ==================================================
    # SITUAÇÃO DO REBANHO
    # ==================================================

    vacas_paridas = Animal.query.filter_by(
        situacao="Parida"
    ).count()

    vacas_gestantes = Animal.query.filter_by(
        situacao="Gestante"
    ).count()

    vacas_vazias = Animal.query.filter_by(
        situacao="Vazia"
    ).count()


    # ==================================================
    # TOTAL DE ANIMAIS
    # ==================================================

    total_animais = Animal.query.count()


    # ==================================================
    # MÉDIA DE CUSTO POR ANIMAL
    # ==================================================

    if total_animais > 0:

        media_por_animal = (
            total_despesas / total_animais
        )

    else:

        media_por_animal = 0


    # ==================================================
    # MOVIMENTAÇÕES
    # ==================================================

    movimentacoes = Custo.query.order_by(
        Custo.data.desc()
    ).all()


    # ==================================================
    # PORCENTAGENS DO REBANHO
    # ==================================================

    if total_animais > 0:

        percentual_paridas = round(
            vacas_paridas * 100 / total_animais
        )

        percentual_gestantes = round(
            vacas_gestantes * 100 / total_animais
        )

        percentual_vazias = round(
            vacas_vazias * 100 / total_animais
        )

    else:

        percentual_paridas = 0

        percentual_gestantes = 0

        percentual_vazias = 0


    # ==================================================
    # ENVIAR TUDO PARA O RELATÓRIO
    # ==================================================

    return render_template(
        "relatorios.html",

        total_despesas=total_despesas,

        total_receitas=total_receitas,

        saldo=saldo,

        total_animais=total_animais,

        media_por_animal=media_por_animal,

        vacas_paridas=vacas_paridas,

        vacas_gestantes=vacas_gestantes,

        vacas_vazias=vacas_vazias,

        percentual_paridas=percentual_paridas,

        percentual_gestantes=percentual_gestantes,

        percentual_vazias=percentual_vazias,

        movimentacoes=movimentacoes
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