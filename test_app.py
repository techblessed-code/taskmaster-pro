"""Test suite for TaskMaster Pro.

Uses a throw-away SQLite database (TASKMASTER_DB points at a temp file
BEFORE the app is imported, because init_db() runs at import time).
CSRF is disabled for tests (Flask-WTF would need real tokens).

Run with:  python -m unittest          (or python -m unittest test_app -v)
"""

import os
import tempfile

# Must happen before `import app` - init_db() runs at import time.
_fd, _temp_db = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.unlink(_temp_db)                     # init_db creates it fresh
os.environ["TASKMASTER_DB"] = _temp_db

import unittest                                                 # noqa: E402

import app as app_module                                        # noqa: E402


class TaskMasterTests(unittest.TestCase):

    def setUp(self):
        app_module.app.config["TESTING"] = True
        app_module.app.config["WTF_CSRF_ENABLED"] = False
        self.client = app_module.app.test_client()
        # isolate: wipe tasks, re-seed (get_db() needs an app context - it
        # caches the connection on Flask's `g`)
        with app_module.app.app_context():
            conn = app_module.get_db()
            conn.execute("DELETE FROM tasks")
            # AUTOINCREMENT keeps counting from the old max (ids 4,5,6 after
            # the first wipe) - reset it so the re-seeded rows are 1,2,3 again
            conn.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")
            conn.executemany(
                "INSERT INTO tasks (title, description, priority, status,"
                " due_date) VALUES (?, ?, ?, ?, ?)", app_module.SEED_TASKS)
            conn.commit()

    # ------------------------------------------------------------- pages --
    def test_home_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to TaskMaster Pro", response.data)

    def test_about_renders(self):
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"About TaskMaster Pro", response.data)

    def test_tasks_list_shows_seeded_tasks(self):
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"complete Flask tutorial", response.data)
        self.assertIn(b"build task manager", response.data)

    def test_task_detail_renders_full_fields(self):
        response = self.client.get("/tasks/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"complete Flask tutorial", response.data)
        self.assertIn(b"Priority", response.data)

    def test_unknown_task_is_404_not_crash(self):
        # regression: task=None used to be passed to the template (500)
        response = self.client.get("/tasks/9999")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"404", response.data)

    def test_unknown_url_404_page_renders(self):
        # regression: 404.html was truncated mid-block, so the handler
        # itself crashed
        response = self.client.get("/no-such-page")
        self.assertEqual(response.status_code, 404)

    def test_js_path_fixed(self):
        # regression: base.html asked for scripts/main.js (404)
        response = self.client.get("/static/js/main.js")
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------- create task --
    def test_create_task_get_renders_form(self):
        response = self.client.get("/task/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Create New Task", response.data)

    def test_create_task_persists_and_redirects(self):
        # regression: url_for('tasks') used to be a BuildError (the view was
        # named task_many) and nothing was stored anyway
        response = self.client.post("/task/new", data={
            "title": "Write release notes",
            "description": "Summarise the fixes.",
            "priority": "high",
            "due_date": "2026-11-05"},
            follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/tasks", response.headers["Location"])

        listing = self.client.get("/tasks")
        self.assertIn(b"Write release notes", listing.data)

    def test_create_task_invalid_shows_errors(self):
        response = self.client.post("/task/new", data={
            "title": "x", "priority": "low", "due_date": "2026-11-05"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"error-message", response.data)

    # ---------------------------------------------------------- contact --
    def test_contact_page_renders(self):
        # regression: contact.html did not exist -> 500
        response = self.client.get("/contact")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Contact Us", response.data)

    def test_contact_post_flashes_and_redirects(self):
        response = self.client.post("/contact", data={
            "name": "Ada", "email": "ada@example.com",
            "message": "Loved the demo, great work!"})
        self.assertEqual(response.status_code, 302)

        home = self.client.get("/")
        self.assertIn(b"Your message has been sent", home.data)

    def test_contact_invalid_shows_errors(self):
        response = self.client.post("/contact", data={
            "name": "A", "email": "nope", "message": "hi"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"error-message", response.data)


def tearDownModule():
    if os.path.exists(_temp_db):
        os.remove(_temp_db)


if __name__ == "__main__":
    unittest.main()
