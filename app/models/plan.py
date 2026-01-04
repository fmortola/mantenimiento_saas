from app import db
from datetime import datetime


class Plan(db.Model):
    """Planes de suscripcion del SaaS"""
    __tablename__ = 'plan'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    # Limites
    max_tecnicos = db.Column(db.Integer, default=3)
    max_clientes = db.Column(db.Integer, default=10)
    max_equipos = db.Column(db.Integer, default=100)
    max_usuarios_cliente = db.Column(db.Integer, default=5)

    # Caracteristicas
    tiene_reportes = db.Column(db.Boolean, default=True)
    tiene_api = db.Column(db.Boolean, default=False)
    tiene_notificaciones_push = db.Column(db.Boolean, default=True)
    tiene_exportacion_excel = db.Column(db.Boolean, default=True)
    tiene_branding = db.Column(db.Boolean, default=False)

    # Portal del cliente - qué puede ver
    cliente_ve_ordenes = db.Column(db.Boolean, default=False)
    cliente_ve_mantenimientos = db.Column(db.Boolean, default=False)

    # Precio (referencia)
    precio_mensual = db.Column(db.Numeric(10, 2), default=0)
    precio_anual = db.Column(db.Numeric(10, 2), default=0)

    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Plan {self.nombre}>'


# Planes predefinidos para inicializacion
PLANES_PREDEFINIDOS = [
    {
        'nombre': 'Basico',
        'codigo': 'basico',
        'descripcion': 'Ideal para emprendedores y pequenos negocios',
        'max_tecnicos': 2,
        'max_clientes': 5,
        'max_equipos': 10,
        'max_usuarios_cliente': 1,
        'tiene_reportes': True,
        'tiene_api': False,
        'tiene_notificaciones_push': True,
        'tiene_exportacion_excel': False,
        'tiene_branding': False,
        'cliente_ve_ordenes': False,
        'cliente_ve_mantenimientos': False,
        'precio_mensual': 5.90,
        'precio_anual': 64.99
    },
    {
        'nombre': 'Pro',
        'codigo': 'pro',
        'descripcion': 'Para empresas en crecimiento',
        'max_tecnicos': 5,
        'max_clientes': 12,
        'max_equipos': 15,
        'max_usuarios_cliente': 3,
        'tiene_reportes': True,
        'tiene_api': False,
        'tiene_notificaciones_push': True,
        'tiene_exportacion_excel': True,
        'tiene_branding': True,
        'cliente_ve_ordenes': True,
        'cliente_ve_mantenimientos': False,
        'precio_mensual': 12.75,
        'precio_anual': 139.99
    },
    {
        'nombre': 'Enterprise',
        'codigo': 'enterprise',
        'descripcion': 'Para operaciones grandes con soporte premium',
        'max_tecnicos': 20,
        'max_clientes': 30,
        'max_equipos': 50,
        'max_usuarios_cliente': 5,
        'tiene_reportes': True,
        'tiene_api': True,
        'tiene_notificaciones_push': True,
        'tiene_exportacion_excel': True,
        'tiene_branding': True,
        'cliente_ve_ordenes': True,
        'cliente_ve_mantenimientos': True,
        'precio_mensual': 29.99,
        'precio_anual': 299.99
    }
]
