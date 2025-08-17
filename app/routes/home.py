from flask import Blueprint, render_template_string

bp = Blueprint("home", __name__)

@bp.route("/")
async def index():
    return render_template_string("""
        <h1>G-Management CRM</h1>
        <ul>
          <li><a href="{{ url_for('clients.index') }}">Manage Clients</a></li>
          <li><a href="{{ url_for('cash_runs.index') }}">Manage Cash Runs</a></li>
        </ul>
    """)