import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from db.exceptions import DatabaseUnavailableError
from routes import register_blueprints

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"data": {"status": "healthy", "message": "GitVision API is running"}}), 200

    register_blueprints(app)

    @app.errorhandler(DatabaseUnavailableError)
    def handle_db_unavailable(_e):
        return jsonify({"error": "database unavailable"}), 503

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(404)
    def handle_not_found(_e):
        return jsonify({"error": "not found"}), 404

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, port=5000)
