# DEAD DUPLICATE APP - kept but never used.
# app_simply.py is an earlier, simplified copy of app.py: a static in-memory
# task list, no forms, no database. It is a SEPARATE Flask instance, so it
# cannot shadow the real one - but it references templates/profile.html,
# which does not exist, so its /user/<username> route is a guaranteed 500.
# app.py is the real application. Kept per the project rule: dead code is
# commented with an explanation, not deleted.
from flask import Flask, render_template

app = Flask(__name__)

tasks = [
        {'id': 1, 'title': 'complete Flask tutorial', 'status': 'pending'},
        {'id': 2, 'title': 'build task manager', 'status': 'in-progress'},
        {'id': 3, 'title': 'deploy to production', 'status': 'completed'},
    ]

@app.route('/')
def home():
    # render_templates looks for HTML files in the template folder
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/tasks')
def tasks():
    return render_template('tasks.html', tasks=tasks)

@app.route('/tasks/<int:id>')
def show_task(id):

    selected_task = None 

    for task in tasks:
        if task['id'] == id:
            selected_task = task

    return render_template('task_detail.html', task=selected_task)


@app.route('/user/<username>')
def profile(username):
    return render_template('profile.html', username=username)


if __name__ == '__main__':
    app.run(debug=True)