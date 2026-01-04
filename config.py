import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-cambiar-en-produccion'

    # MariaDB - NUEVA BD para SaaS (NO usar servicio_tecnico que esta en produccion)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://mantenimiento_saas:password@10.5.1.115:3306/mantenimiento_saas'
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

    # VAPID keys para Push Notifications (generar propias en producción)
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY') or 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U'
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY') or 'Wml2jJSLRKGzm8-BrPJzaW4n1zWh6_KxV-a2zLjvPWI'
    VAPID_CLAIMS = {"sub": "mailto:admin@servicio-tecnico.com"}
