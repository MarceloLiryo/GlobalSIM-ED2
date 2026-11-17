from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

clients_bp = Blueprint("clients", __name__, url_prefix="/clientes")


def services():
    return current_app.extensions["clients"], current_app.extensions["countries"]


@clients_bp.get("/")
def dashboard():
    clients, countries = services()
    query = request.args.get("id", "").strip()
    destination = request.args.get("destino", "").strip().upper()
    itinerary = request.args.get("roteiro", "").strip()
    editing = found = integrated = recommendation = None
    error = None
    comparisons = 0
    try:
        if request.args.get("editar"):
            editing = clients.get_by_id(request.args["editar"])
            if editing is None:
                raise KeyError("Cliente não encontrado para edição.")
        if query:
            found = clients.get_by_id(query)
            comparisons = clients.tree.last_search_comparisons
            if found is None:
                raise KeyError("Cliente não encontrado.")
            if destination:
                integrated = clients.consult_destination(query, destination, countries)
        if itinerary:
            recommendation = countries.recommend_package_for_itinerary(itinerary)
    except (ValueError, KeyError) as err:
        error = str(err).strip("'")
    try:
        page = max(1, int(request.args.get("pagina", 1)))
    except ValueError:
        page = 1
    records = clients.list_all()
    pages = max(1, (len(records) + 49) // 50)
    page = min(page, pages)
    return render_template(
        "clients.html", clients=records[(page - 1) * 50:page * 50], page=page, pages=pages,
        editing=editing, found=found, integrated=integrated, query=query, destination=destination,
        itinerary=itinerary, recommendation=recommendation, error=error,
        comparisons=comparisons, metrics=clients.tree.get_metrics(), packages=clients.packages,
    )


@clients_bp.post("/criar")
def create():
    clients, _ = services()
    try:
        client = clients.create(request.form.to_dict())
        flash(f"Cliente {client.name} cadastrado com sucesso.", "success")
        return redirect(url_for("clients.dashboard", id=client.id))
    except (ValueError, KeyError, OSError) as err:
        flash(str(err), "error")
        return redirect(url_for("clients.dashboard"))


@clients_bp.post("/<int:client_id>/atualizar")
def update(client_id):
    clients, _ = services()
    try:
        clients.update(client_id, request.form.to_dict())
        flash("Cliente atualizado com sucesso.", "success")
    except (ValueError, KeyError, OSError) as err:
        flash(str(err), "error")
    return redirect(url_for("clients.dashboard", id=client_id))


@clients_bp.post("/recomendar")
def assign_recommendation():
    clients, countries = services()
    client_id = request.form.get("id", "")
    itinerary = request.form.get("roteiro", "")
    try:
        client = clients.assign_recommended_package(client_id, itinerary, countries)
        flash(f"Pacote recomendado associado ao cliente {client.name} e eSIM {client.esim}.", "success")
    except (ValueError, KeyError, OSError) as err:
        flash(str(err), "error")
    return redirect(url_for("clients.dashboard", id=client_id, roteiro=itinerary))
