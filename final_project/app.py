from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

db = SQL("sqlite:///todo.db")

app.config["SECRET_KEY"] = "your_secret_key"

@app.route("/",methods=["GET", "POST"])
def index():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        tasks = request.form.get("tasks")

        if tasks:
             # Insere a nova tarefa
            db.execute("INSERT INTO tasks (description, user_id) VALUES (?, ?)", tasks, session["user_id"])

            # Busca o ID da tarefa recém-criada
            task_id = db.execute("SELECT id FROM tasks WHERE description = ? AND user_id = ? ORDER BY id DESC LIMIT 1", tasks, session["user_id"])

            # Insere no histórico a ação de criação da tarefa
            db.execute("INSERT INTO history (user_id, task_id, action) VALUES (?, ?, ?)", session["user_id"], task_id[0]["id"], 'created task')

        return redirect("/")

    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", session["user_id"])

    return render_template("index.html", tasks=tasks)

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) == 0 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return "Invalid username and/or password"
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = generate_password_hash((request.form.get("password")))
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", username, password)

        return redirect("/login")
    return render_template("register.html")


@app.route("/logout")
def logout():
    """CLEAR USER SESION"""
    session.clear()

    return redirect("/")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/task")
def task():
    return redirect("/")

@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")

    # Busca o histórico completo do usuário logado
    history = db.execute("SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC", session["user_id"])

    return render_template("history.html", history=history)

@app.route("/delete/<int:task_id>", methods=["GET", "POST"])
def delete_task(task_id):
    # Verifica se a tarefa existe
    task = db.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", task_id, session["user_id"])
    print("Task ID:", task_id)  # Adiciona uma verificação para garantir que task_id está correto

    if not task:
        return "Task not found", 404

    # Registra a ação no histórico antes de excluir a tarefa
    db.execute("INSERT INTO history (user_id, task_id, action) VALUES (?, ?, ?)",
               session["user_id"], task_id, 'deleted task')

    # Exclui a tarefa
    db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", task_id, session["user_id"])

    return redirect("/")

@app.route("/edit/<int:task_id>", methods=["POST"])
def edit_task(task_id):
    # Recebe a nova descrição do corpo da requisição JSON
    data = request.get_json()
    new_description = data.get('description')

    # Verifica se a nova descrição foi enviada
    if not new_description:
        return jsonify({"error": "Description is required"}), 400

    # Atualiza a tarefa no banco de dados
    # Atualiza a tarefa no banco de dados
    db.execute("UPDATE tasks SET description = ? WHERE id = ? AND user_id = ?", new_description, task_id, session["user_id"])

    # Registra a ação de edição no histórico
    db.execute("INSERT INTO history (user_id, task_id, action) VALUES (?, ?, ?)", session["user_id"], task_id, 'edited task')

    # Retorna uma resposta de sucesso em JSON
    return jsonify({"message": "Task updated successfully"})
