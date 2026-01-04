import os
from dotenv import load_dotenv

# Cargar .env desde el directorio del proyecto
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-cambiar-en-produccion'

    # MariaDB - Base de datos SaaS
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:ids12345%24@10.5.1.115:3306/servicio_tecnico'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'images', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

    # Configuracion SaaS
    SAAS_NAME = os.environ.get('SAAS_NAME') or 'TecniGest SaaS'
    SAAS_DOMAIN = os.environ.get('SAAS_DOMAIN') or 'tecnigest.com'

    # Configuración de cookies para compatibilidad con Safari
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Cambiar a True si usas HTTPS
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = False  # Cambiar a True si usas HTTPS

    # VAPID keys para Push Notifications (REQUERIDO - generar con: python gen_vapid.py)
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
    VAPID_CLAIMS = {"sub": os.environ.get('VAPID_EMAIL', 'mailto:admin@example.com')}
