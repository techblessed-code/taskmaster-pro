"""TaskMaster Pro - a task manager with real SQLite persistence.

What was broken before (every fix is annotated in place):
- TWO `def home()` definitions, one decorated with @app.route('home') (no
  leading slash) and rendering 'index.html ' (trailing space in the name)
- app.py and create_task.html both used url_for('tasks'), but the view was
  actually named `task_many` -> BuildError 500 on every successful creation
- tasks lived in a static in-memory list ("Here we'll save to database
  (coming later)" - the later never came): created tasks evaporated on the
  next restart
- /contact rendered a template that did not exist (the navbar's Contact
  link was a guaranteed 500)
- an unknown task id passed task=None to the template (crash) instead of 404
"""

import os
import sqlite3

from flask import (
    Flask, render_template, request, flash, redirect, url_for, g, abort,
    send_from_directory)
from werkzeug.utils import secure_filename

from config import Config
from forms import TaskForm, ContactForm

app = Flask(__name__)
app.config.from_object(Config)

# Ensure the upload folder (task attachments) exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Tests point this at a temp database (see test_app.py).
DB_PATH = os.environ.get('TASKMASTER_DB',
                         os.path.join(BASE_DIR, 'taskmaster.db'))

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT,
    priority    TEXT NOT NULL DEFAULT 'low',
    status      TEXT NOT NULL DEFAULT 'pending',
    due_date    TEXT,
    attachment  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# The three sample tasks the app started with - now the SEED rows of the
# database. They used to live in a static in-memory list that forgot
# everything on restart.
SEED_TASKS = [
    ('complete Flask tutorial',
     'Follow the official Flask quickstart end to end.',
     'low', 'pending', '2026-11-01'),
    ('build task manager',
     'This app: forms, uploads, flashes, persistence.',
     'high', 'in-progress', '2026-10-30'),
    ('deploy to production',
     'Behind a real WSGI server with DEBUG off.',
     'high', 'completed', '2026-10-20'),
]


def init_db():
    """Create the tasks table and seed it once (idempotent)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        if conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 0:
            conn.executemany(
                'INSERT INTO tasks (title, description, priority, status,'
                ' due_date) VALUES (?, ?, ?, ?, ?)', SEED_TASKS)
        conn.commit()
    finally:
        conn.close()


# Fresh clone works with zero manual steps: table + seed data ready to go.
init_db()


# ---------------------------------------------------------------- database --
def get_db():
    """One sqlite3 connection per request, cached on Flask's `g`."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row   # templates: task.title / task['id']
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ------------------------------------------------------------------ routes --
@app.route('/')
def home():
    # FIX: there used to be TWO `def home()` - one with @app.route('home')
    # (no leading slash) rendering 'index.html ' (trailing space -> template
    # not found). One route, one clean template name now.
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/tasks')
def tasks():
    # FIX: the view used to be called `task_many`, while app.py's redirect
    # and create_task.html's cancel link both called url_for('tasks') ->
    # BuildError (500) after every successful creation. Reads from the
    # database now instead of the static in-memory list.
    task_list = get_db().execute(
        'SELECT * FROM tasks ORDER BY id').fetchall()
    return render_template('tasks.html', tasks=task_list)


@app.route('/tasks/<int:id>')
def show_task(id):
    task = get_db().execute(
        'SELECT * FROM tasks WHERE id = ?', (id,)).fetchone()
    # FIX: an unknown id used to pass task=None into the template, which
    # crashed while rendering. A proper 404 page now.
    if task is None:
        abort(404)
    return render_template('task_detail.html', task=task)


@app.route('/task/new', methods=['GET', 'POST'])
def create_task():
    form = TaskForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        priority = form.priority.data
        due_date = form.due_date.data

        # Handle optional file upload (kept from the original)
        filename = None
        if form.attachment.data and form.attachment.data.filename:
            file = form.attachment.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # FIX: "Here we'll save to database (coming later)" - the later
        # never came. The task is stored now, so the list actually grows.
        get_db().execute(
            'INSERT INTO tasks (title, description, priority, status,'
            ' due_date, attachment) VALUES (?, ?, ?, ?, ?, ?)',
            (title, description, priority, 'pending',
             due_date.isoformat() if due_date else None, filename))
        get_db().commit()

        flash(f"Task '{title}' created successfully!", 'success')
        # FIX: url_for('tasks') finally resolves - the view IS named tasks.
        return redirect(url_for('tasks'))

    return render_template('create_task.html', form=form)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        flash(f'Thank you {name}! Your message has been sent.', 'success')
        return redirect(url_for('home'))
    # FIX: this route rendered 'contact.html', which did not exist - the
    # navbar's Contact link was a guaranteed 500.
    return render_template('contact.html', form=form)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # FIX: task_detail.html used to link attachments as
    # url_for('static', filename='uploads/...'), but UPLOAD_FOLDER lives in
    # the project ROOT (outside static/) - every attachment link 404'd.
    # This route serves them from the real upload folder.
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# 404 Error Handler
@app.errorhandler(404)
def page_not_found(e):
    # FIX: 404.html was truncated right after `{% block content %}` - the
    # unparseable template made the 404 handler itself crash.
    return render_template('404.html'), 404


# 500 Error Handler
@app.errorhandler(500)
def internal_server_error(e):
    # FIX: 500.html was an EMPTY file -> TemplateNotFound while trying to
    # render a 500.
    return render_template('500.html'), 500


# Run Flask App
if __name__ == '__main__':
    app.run(debug=True, port=5000)
