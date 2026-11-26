from flask import Blueprint, current_app, redirect, render_template, request, url_for
from app.models.country import country_service
from app.models.packages import load_packages

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET"])
def index():
    query_code = request.args.get("codigo", "").strip()
    itinerary_raw = request.args.get("roteiro", "").strip()
    if query_code or itinerary_raw:
        params = {}
        if query_code:
            params["codigo"] = query_code
        if itinerary_raw:
            params["roteiro"] = itinerary_raw
        return redirect(url_for("home.coverage", **params))

    clients_service = current_app.extensions.get("clients")
    return render_template(
        "home.html",
        countries_count=country_service.get_instrumentation()["size"],
        clients_count=len(clients_service.tree) if clients_service else 0,
        packages=load_packages(),
    )


@home_bp.route("/cobertura", methods=["GET"])
def coverage():
    query_code = request.args.get("codigo", "").strip()
    itinerary_raw = request.args.get("roteiro", "").strip()

    coverage_result = None
    search_performed = False
    search_comparisons = 0

    if query_code:
        search_performed = True
        coverage_result = country_service.get_by_code(query_code)
        search_comparisons = country_service.get_instrumentation()["last_search_comparisons"]

    itinerary_result = None
    if itinerary_raw:
        itinerary_result = country_service.recommend_package_for_itinerary(itinerary_raw)

    countries = country_service.list_all()
    metrics = country_service.get_instrumentation()

    return render_template(
        "cobertura.html",
        countries=countries,
        query_code=query_code.upper(),
        search_performed=search_performed,
        coverage_result=coverage_result,
        search_comparisons=search_comparisons,
        itinerary_raw=itinerary_raw.upper(),
        itinerary_result=itinerary_result,
        metrics=metrics,
    )
