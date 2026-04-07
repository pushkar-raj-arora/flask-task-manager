import sqlite3
import os
from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

# Absolute path to avoid blank page issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'tasks.db')

# Helper function to connect to DB
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Create tasks table if it doesn't exist
def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# ----------------- API ROUTES -----------------

# Get all tasks
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = get_db()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])

# Add a new task via API
@app.route('/api/tasks', methods=['POST'])
def add_task_api():
    data = request.get_json()
    task = data.get('task')
    if not task:
        return jsonify({"error": "Task content required"}), 400

    conn = get_db()
    conn.execute('INSERT INTO tasks (task, done) VALUES (?, ?)', (task, 0))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task added"}), 201

# Update a task via API
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task_api(task_id):
    data = request.get_json()
    new_task = data.get('task')
    if not new_task:
        return jsonify({"error": "Task content required"}), 400

    conn = get_db()
    cursor = conn.execute('UPDATE tasks SET task = ? WHERE id = ?', (new_task, task_id))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task updated"})

# Delete a task via API
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task_api(task_id):
    conn = get_db()
    cursor = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task deleted"})

# Toggle task done via API
@app.route('/api/tasks/<int:task_id>/toggle', methods=['PUT'])
def toggle_task_api(task_id):
    conn = get_db()
    task = conn.execute('SELECT done FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task is None:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    new_status = 0 if task['done'] == 1 else 1
    conn.execute('UPDATE tasks SET done = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task status toggled", "done": new_status})

# ----------------- WEB ROUTES -----------------

# Home page
@app.route('/', methods=['GET', 'POST'])
def home():
    conn = get_db()

    if request.method == 'POST':
        task = request.form.get('task')
        if task:
            conn.execute('INSERT INTO tasks (task, done) VALUES (?, ?)', (task, 0))
            conn.commit()
        conn.close()
        return redirect('/')  # avoids form resubmit popup

    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

# Toggle task done via web
@app.route('/complete/<int:task_id>')
def complete(task_id):
    conn = get_db()
    task = conn.execute('SELECT done FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task is None:
        conn.close()
        return "Task not found", 404

    new_status = 0 if task['done'] == 1 else 1
    conn.execute('UPDATE tasks SET done = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()
    return redirect('/')

# Edit task via web (GET: show form)
@app.route('/edit/<int:task_id>', methods=['GET'])
def edit_task(task_id):
    conn = get_db()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()
    if task is None:
        return "Task not found", 404
    return render_template('edit.html', task=task)

# Edit task via web (POST: save changes)
@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task_post(task_id):
    new_task = request.form.get('task')
    if not new_task:
        return "Task cannot be empty", 400

    conn = get_db()
    cursor = conn.execute('UPDATE tasks SET task = ? WHERE id = ?', (new_task, task_id))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return "Task not found", 404

    return redirect('/')  # back to home after edit

# Delete task via web
@app.route('/delete/<int:task_id>')
def delete_task_web(task_id):
    conn = get_db()
    cursor = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return "Task not found", 404

    return redirect('/')  # back to home after deletion

# if __name__ == '__main__':
#     init_db()  # ensure table exists
#     app.run(debug=True, port=5000)
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))  # Render sets this automatically
    app.run(host="0.0.0.0", port=port, debug=True)