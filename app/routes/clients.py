from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy.ext.asyncio import AsyncSession
from ..crud import get_clients, create_client
from app import AsyncSessionLocal

bp = Blueprint("clients", __name__, url_prefix="/clients")

@bp.route("/")
async def index():
    async with AsyncSessionLocal() as db:
        clients = await get_clients(db)
    return render_template("clients_list.html", clients=clients)

@bp.route("/new", methods=["GET", "POST"])
async def new():
    if request.method == "POST":
        data = request.form.to_dict()
        async with AsyncSessionLocal() as db:
            await create_client(db, **data)
        return redirect(url_for("clients.index"))
    return render_template("client_form.html")