# TaskMaster Pro (Flask)

A task manager with **real persistence**: create tasks with priorities, due
dates and file attachments, browse the list, open detail pages — plus a
contact form, custom 404/500 pages and flash notifications.

## Quick start

```powershell
cd C:\Fullstack\Back_end\Flask\taskmaster_pro
env\Scripts\activate
pip install -r requirements.txt
python app.py                 # http://127.0.0.1:5000/
```

`taskmaster.db` (SQLite) and the three seed tasks are created automatically
on first run — no migration step.

## Routes

| Route | Methods | What it does |
|---|---|---|
| `/` | GET | home page |
| `/about` | GET | about page |
| `/tasks` | GET | task list (from the database) |
| `/tasks/<id>` | GET | task detail (404 for unknown ids) |
| `/task/new` | GET, POST | create task — validated form, optional attachment |
| `/contact` | GET, POST | contact form with flash feedback |
| `/uploads/<filename>` | GET | serves saved task attachments |

## Tests

```powershell
python -m unittest          # 13 tests against a throw-away temp database
```

## Project layout

```
app.py              routes + SQLite persistence (init_db, per-request `g`)
config.py           Config class (SECRET_KEY from .env, upload folder, 16MB cap)
forms.py            Flask-WTF forms: TaskForm, ContactForm
test_app.py         unittest suite
templates/          base + 8 pages (contact.html and 500.html are new)
static/css, static/js
uploads/            task attachments land here (gitignored)
app_simply.py       DEAD early copy of the app - kept commented, see header
task.html           DEAD template - kept commented, see header
```

## What was fixed in this audit

* **`url_for('tasks')` pointed at a view named `task_many`** — every
  successful task creation died with a BuildError 500 (the cancel link in
  the form was broken the same way). The view is now named `tasks`
* **tasks were never saved** ("Here we'll save to database (coming later)" —
  the later never came): they lived in a static in-memory list. Real SQLite
  storage added, the 3 samples became seed rows
* **duplicate `def home()`**, one with a slash-less `@app.route('home')` and
  `render_template('index.html ')` (trailing space in the template name)
* **`/contact` rendered a template that did not exist** — the navbar's
  Contact link was a guaranteed 500. `contact.html` written
* **unknown task ids passed `task=None` into the template** (crash) — now a
  proper 404
* **`base.html` started with pasted Gmail UI text** above the doctype
  (visible garbage on every page) and loaded `scripts/main.js` from the
  wrong folder (404)
* **`404.html` was truncated mid-block** (the 404 handler crashed) and
  **`500.html` was empty** (the 500 handler crashed) — both completed
* **attachment links 404'd**: uploads are saved to `uploads/` (project root)
  but linked as `static/uploads/...` — a dedicated `/uploads/<filename>`
  route now serves them
* stray `</body></html>` inside `task_detail.html`, a full doctype wrapper
  around `tasks.html`'s `{% extends %}`, flash messages centralized in
  `base.html`, `reqiurement.txt` (misspelled *and* empty) superseded by a
  real `requirements.txt`, `.env` documented, `app_simply.py` and
  `task.html` marked as dead code with explanations (kept, not deleted)

## Config

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev fallback | session/CSRF signing — export your own in production |
| `TASKMASTER_DB` | `taskmaster.db` | database path (tests repoint it) |

Uploads are capped at 16 MB and restricted to jpg/png/pdf/doc/docx;
filenames pass through `secure_filename`.
