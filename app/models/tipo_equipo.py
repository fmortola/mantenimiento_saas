from app import db
from datetime import datetime

class TipoEquipo(db.Model):
    """Tipos de equipo configurables por tenant"""
    __tablename__ = 'tipo_equipo'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)  # Ej: "Lavadora", "Aire Acondicionado"
    icono = db.Column(db.String(50), default='bi-gear')  # Icono Bootstrap
    descripcion = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)  # Para ordenar en listas
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Tenant (multi-tenancy)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)

    # Relaciones
    tenant = db.relationship('Tenant', backref='tipos_equipo')
    equipos = db.relationship('Equipo', backref='tipo_equipo_rel', lazy='dynamic')

    def __repr__(self):
        return f'<TipoEquipo {self.nombre}>'

    @staticmethod
    def crear_tipos_default(tenant_id, commit=True):
        """Crea tipos de equipo por defecto para un tenant nuevo"""
        tipos_default = [
            {'nombre': 'Computadora', 'icono': 'bi-pc-display'},
            {'nombre': 'Laptop', 'icono': 'bi-laptop'},
            {'nombre': 'Impresora', 'icono': 'bi-printer'},
            {'nombre': 'Monitor', 'icono': 'bi-display'},
            {'nombre': 'Servidor', 'icono': 'bi-hdd-rack'},
            {'nombre': 'Router/Switch', 'icono': 'bi-router'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]

        for i, tipo in enumerate(tipos_default):
            t = TipoEquipo(
                nombre=tipo['nombre'],
                icono=tipo['icono'],
                tenant_id=tenant_id,
                orden=i
            )
            db.session.add(t)

        if commit:
            db.session.commit()

    @staticmethod
    def crear_tipos_linea_blanca(tenant_id, commit=True):
        """Crea tipos para empresa de línea blanca"""
        tipos = [
            {'nombre': 'Refrigerador', 'icono': 'bi-box-seam'},
            {'nombre': 'Lavadora', 'icono': 'bi-droplet'},
            {'nombre': 'Secadora', 'icono': 'bi-wind'},
            {'nombre': 'Cocina/Estufa', 'icono': 'bi-fire'},
            {'nombre': 'Microondas', 'icono': 'bi-box'},
            {'nombre': 'Lavavajillas', 'icono': 'bi-droplet-half'},
            {'nombre': 'Aire Acondicionado', 'icono': 'bi-snow'},
            {'nombre': 'Calentador', 'icono': 'bi-thermometer-sun'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]

        for i, tipo in enumerate(tipos):
            t = TipoEquipo(
                nombre=tipo['nombre'],
                icono=tipo['icono'],
                tenant_id=tenant_id,
                orden=i
            )
            db.session.add(t)

        if commit:
            db.session.commit()

    @staticmethod
    def crear_tipos_hvac(tenant_id, commit=True):
        """Crea tipos para empresa de HVAC/climatización"""
        tipos = [
            {'nombre': 'Minisplit', 'icono': 'bi-snow'},
            {'nombre': 'Aire Central', 'icono': 'bi-wind'},
            {'nombre': 'Chiller', 'icono': 'bi-snow2'},
            {'nombre': 'Calefactor', 'icono': 'bi-thermometer-sun'},
            {'nombre': 'Ventilador Industrial', 'icono': 'bi-fan'},
            {'nombre': 'Extractor', 'icono': 'bi-arrow-up-circle'},
            {'nombre': 'Humidificador', 'icono': 'bi-moisture'},
            {'nombre': 'Deshumidificador', 'icono': 'bi-droplet-half'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]

        for i, tipo in enumerate(tipos):
            t = TipoEquipo(
                nombre=tipo['nombre'],
                icono=tipo['icono'],
                tenant_id=tenant_id,
                orden=i
            )
            db.session.add(t)

        if commit:
            db.session.commit()
