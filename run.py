import click
from flask import Flask
from app.routes.clients import clients_bp
from app.models.client_service import ClientModel
from app.models.packages import load_packages
from app.repository.client_repository import ClientRepository
from app.models.country import country_service
from app.routes.home import home_bp
from app.routes.admin import admin_bp


def create_app(config=None) -> Flask:
    app = Flask(
        __name__,
        template_folder="app/templates",
        static_folder="app/static",
    )
    app.secret_key = "globalsim-ed2-uneb-secret-key"

    if config:
        app.config.update(config)
    app.extensions["clients"] = ClientModel(
        ClientRepository(app.config.get("CLIENTS_FILE")),
        load_packages(app.config.get("PACKAGES_FILE")),
    )
    app.extensions["countries"] = app.config.get("COUNTRY_SERVICE", country_service)

    @app.cli.command("gerar-clientes")
    @click.option("--quantidade", default=1000, type=click.IntRange(1, 10000), show_default=True)
    def generate_clients(quantidade):
        """Acrescenta clientes fictícios sem sobrescrever os existentes."""
        count = app.extensions["clients"].generate_clients(quantidade)
        click.echo(f"{count} clientes fictícios adicionados à Árvore B e ao JSON.")

    app.register_blueprint(clients_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
