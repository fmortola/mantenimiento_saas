from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder.'
    login_manager.login_message_category = 'warning'

    # Crear carpeta de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.tecnico import tecnico_bp
    from app.routes.cliente import cliente_bp
    from app.routes.api import api_bp
    from app.routes.superadmin import superadmin_bp
    from app.routes.firma_publica import firma_publica_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(tecnico_bp, url_prefix='/tecnico')
    app.register_blueprint(cliente_bp, url_prefix='/cliente')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')
    app.register_blueprint(firma_publica_bp)  # Rutas públicas sin prefix

    # Verificar aceptación de política antes de cada request
    @app.before_request
    def verificar_politica_aceptada():
        # Rutas que no requieren verificación
        rutas_excluidas = [
            'auth.login', 'auth.logout', 'auth.aceptar_politica',
            'auth.manifest', 'auth.service_worker',
            'static', 'firma_publica.firmar_orden'
        ]

        if current_user.is_authenticated:
            # Superadmin no requiere aceptar política
            if current_user.es_superadmin():
                return None

            # Si no ha aceptado la política y no está en una ruta excluida
            if not current_user.acepto_politica:
                if request.endpoint and request.endpoint not in rutas_excluidas:
                    return redirect(url_for('auth.aceptar_politica'))

        return None

    # Importar todos los modelos para que SQLAlchemy los conozca
    from app.models import (
        Plan, Tenant, Usuario, Cliente, Ubicacion, TipoEquipo,
        PlantillaTipoEquipo, PlantillaTipoEquipoItem, Equipo,
        OrdenTrabajo, FotoTrabajo, OrdenActividad, Ticket,
        Mantenimiento, MantenimientoEquipo, PushSubscription, Notificacion
    )

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    # Registrar comandos CLI (opcional)
    try:
        import commands
        commands.init_app(app)
    except ImportError:
        pass  # Comandos no disponibles si no existe el archivo

    return app
