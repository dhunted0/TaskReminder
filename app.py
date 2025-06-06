from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from notifypy import Notify
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cenoura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskreminder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Base de Dados
class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data = db.Column(db.String(20), nullable=False)
    prioridade = db.Column(db.String(10), nullable=False)

# Rota inicial
@app.route("/")
def index():
    filtro = request.args.get("prioridade")
    status = request.args.get("status")
    todas = Tarefa.query.all()

    hoje = datetime.today().date()
    hoje_formatado = hoje.strftime("%d/%m/%y")

    tarefas = []
    tarefas_vencidas = []
    tarefas_alerta = []

    primeira_visita = not session.get("notificou")
    session["notificou"] = True

    for t in todas:
        try:
            data_tarefa = datetime.strptime(t.data, "%Y-%m-%d").date()
            t.data_formatada = data_tarefa.strftime("%d/%m/%y")

            if filtro and t.prioridade != filtro:
                continue

            if status == "hoje" and data_tarefa != hoje:
                continue
            elif status == "futuras" and data_tarefa <= hoje:
                continue
            elif status == "vencidas" and data_tarefa >= hoje:
                continue

            if data_tarefa < hoje:
                tarefas_vencidas.append(t)
            else:
                tarefas.append(t)

            if data_tarefa == hoje or data_tarefa == hoje + timedelta(days=1):
                tarefas_alerta.append(t.id)

                # notificação pelo sistema
                if primeira_visita:
                    notificacao = Notify()
                    notificacao.title = "🔔 Tarefa próxima!"
                    notificacao.message = f"{t.titulo} - vence em {t.data_formatada}"
                    notificacao.application_name = "Task Reminder"
                    notificacao.icon = "static/icon.png"
                    notificacao.send()

        except ValueError:
            t.data_formatada = t.data

    tarefas = sorted(tarefas, key=lambda t: datetime.strptime(t.data, "%Y-%m-%d"))
    tarefas_vencidas = sorted(tarefas_vencidas, key=lambda t: datetime.strptime(t.data, "%Y-%m-%d"))

    return render_template(
        "index.html",
        tarefas=tarefas + tarefas_vencidas,
        alerta_ids=tarefas_alerta,
        filtro=filtro,
        status=status,
        hoje_formatado=hoje_formatado
    )

# Adicionar tarefa
@app.route("/adicionar", methods=["POST"])
def adicionar():
    titulo = request.form["titulo"]
    descricao = request.form["descricao"]
    data = request.form["data"]
    prioridade = request.form["prioridade"]
    nova = Tarefa(titulo=titulo, descricao=descricao, data=data, prioridade=prioridade)
    db.session.add(nova)
    db.session.commit()
    flash("✅ Tarefa adicionada com sucesso!")
    return redirect(url_for("index"))

# Editar tarefa
@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    tarefa = Tarefa.query.get_or_404(id)
    tarefa.titulo = request.form["titulo"]
    tarefa.descricao = request.form["descricao"]
    tarefa.data = request.form["data"]
    tarefa.prioridade = request.form["prioridade"]
    db.session.commit()
    flash("✏️ Tarefa editada com sucesso!")
    return redirect(url_for("index"))

# Excluir tarefa
@app.route("/excluir/<int:id>")
def excluir(id):
    tarefa = Tarefa.query.get_or_404(id)
    db.session.delete(tarefa)
    db.session.commit()
    flash("❌ Tarefa excluída com sucesso.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    if not os.path.exists("taskreminder.db"):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
