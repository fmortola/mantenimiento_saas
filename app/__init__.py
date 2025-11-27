from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(tecnico_bp, url_prefix='/tecnico')
    app.register_blueprint(cliente_bp, url_prefix='/cliente')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
        # Crear usuario admin por defecto si no existe
        from app.models.usuario import Usuario
        admin = Usuario.query.filter_by(email='admin@admin.com').first()
        if not admin:
            admin = Usuario(
                nombre='Administrador',
                email='admin@admin.com',
                telefono='0000000000',
                rol='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    return app
