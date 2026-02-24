from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# DATABASE CONFIGURATION (Render + Local Compatible)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(basedir, "toolroom.db")
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================
# DATABASE MODELS
# ==========================

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    reorder_level = db.Column(db.Integer)

class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    contact = db.Column(db.String(200))

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.String(100))
    technician = db.Column(db.String(200))
    due_date = db.Column(db.DateTime)
    returned = db.Column(db.Boolean, default=False)

class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.String(100))
    action = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================
# LOGIN ROUTE
# ==========================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Temporary Admin Login
        if username == "admin" and password == "admin123":
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

# ==========================
# DASHBOARD
# ==========================

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    total_tools = Tool.query.count()
    issued = Issue.query.filter_by(returned=False).count()
    overdue = Issue.query.filter(Issue.due_date < datetime.now(), Issue.returned == False).count()
    reorder = Tool.query.filter(Tool.quantity <= Tool.reorder_level).count()

    return render_template("dashboard.html",
                           total_tools=total_tools,
                           issued=issued,
                           overdue=overdue,
                           reorder=reorder)

# ==========================
# TOOLS
# ==========================

@app.route('/tools', methods=['GET','POST'])
def tools():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        tool = Tool(tool_id=request.form['tool_id'],
                    name=request.form['name'],
                    quantity=int(request.form['quantity']),
                    reorder_level=int(request.form['reorder_level']))
        db.session.add(tool)
        db.session.commit()

    return render_template("tools.html", tools=Tool.query.all())

# ==========================
# TECHNICIANS
# ==========================

@app.route('/technicians', methods=['GET','POST'])
def technicians():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        tech = Technician(name=request.form['name'],
                          contact=request.form['contact'])
        db.session.add(tech)
        db.session.commit()

    return render_template("technicians.html", technicians=Technician.query.all())

# ==========================
# ISSUE TOOL
# ==========================

@app.route('/issue', methods=['GET','POST'])
def issue():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        due = datetime.strptime(request.form['due_date'], "%Y-%m-%d")
        new_issue = Issue(tool_id=request.form['tool_id'],
                          technician=request.form['technician'],
                          due_date=due)
        db.session.add(new_issue)

        tool = Tool.query.filter_by(tool_id=request.form['tool_id']).first()
        if tool:
            tool.quantity -= 1
            db.session.add(StockMovement(tool_id=tool.tool_id, action="Issued"))

        db.session.commit()

    return render_template("issue.html", issues=Issue.query.all())

# ==========================
# SOP
# ==========================

@app.route('/sop')
def sop():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("sop.html")

# ==========================
# LOGOUT
# ==========================

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ==========================
# CREATE TABLES
# ==========================

with app.app_context():
    db.create_all()

# ==========================
# RUN
# ==========================

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
