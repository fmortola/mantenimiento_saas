from app import db
from datetime import datetime

class PlantillaTipoEquipo(db.Model):
    """Plantillas de tipos de equipo gestionables por SuperAdmin"""
    __tablename__ = 'plantilla_tipo_equipo'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)  # Ej: "Línea Blanca"
    codigo = db.Column(db.String(50), unique=True, nullable=False)  # Ej: "linea_blanca"
    descripcion = db.Column(db.String(255))
    icono = db.Column(db.String(50), default='bi-grid')
    activo = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con los items de la plantilla
    items = db.relationship('PlantillaTipoEquipoItem', backref='plantilla',
                           lazy='dynamic', cascade='all, delete-orphan',
                           order_by='PlantillaTipoEquipoItem.orden')

    def __repr__(self):
        return f'<PlantillaTipoEquipo {self.nombre}>'

    def aplicar_a_tenant(self, tenant_id, commit=True):
        """Crea los tipos de equipo de esta plantilla para un tenant"""
        from app.models.tipo_equipo import TipoEquipo

        for item in self.items.all():
            tipo = TipoEquipo(
                nombre=item.nombre,
                icono=item.icono,
                descripcion=item.descripcion,
                tenant_id=tenant_id,
                orden=item.orden
            )
            db.session.add(tipo)

        if commit:
            db.session.commit()


class PlantillaTipoEquipoItem(db.Model):
    """Items individuales de una plantilla de tipos de equipo"""
    __tablename__ = 'plantilla_tipo_equipo_item'

    id = db.Column(db.Integer, primary_key=True)
    plantilla_id = db.Column(db.Integer, db.ForeignKey('plantilla_tipo_equipo.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    icono = db.Column(db.String(50), default='bi-gear')
    descripcion = db.Column(db.String(255))
    orden = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<PlantillaTipoEquipoItem {self.nombre}>'


# Plantillas predefinidas para cargar en init_saas
PLANTILLAS_PREDEFINIDAS = [
    {
        'nombre': 'Cómputo / TI',
        'codigo': 'computo_ti',
        'descripcion': 'Equipos de computación y tecnología de información',
        'icono': 'bi-pc-display',
        'items': [
            {'nombre': 'Computadora', 'icono': 'bi-pc-display'},
            {'nombre': 'Laptop', 'icono': 'bi-laptop'},
            {'nombre': 'Impresora', 'icono': 'bi-printer'},
            {'nombre': 'Monitor', 'icono': 'bi-display'},
            {'nombre': 'Servidor', 'icono': 'bi-hdd-rack'},
            {'nombre': 'Router/Switch', 'icono': 'bi-router'},
            {'nombre': 'UPS', 'icono': 'bi-battery-charging'},
            {'nombre': 'Scanner', 'icono': 'bi-upc-scan'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]
    },
    {
        'nombre': 'Línea Blanca',
        'codigo': 'linea_blanca',
        'descripcion': 'Electrodomésticos y línea blanca',
        'icono': 'bi-box-seam',
        'items': [
            {'nombre': 'Refrigerador', 'icono': 'bi-box-seam'},
            {'nombre': 'Lavadora', 'icono': 'bi-droplet'},
            {'nombre': 'Secadora', 'icono': 'bi-wind'},
            {'nombre': 'Cocina/Estufa', 'icono': 'bi-fire'},
            {'nombre': 'Microondas', 'icono': 'bi-box'},
            {'nombre': 'Lavavajillas', 'icono': 'bi-droplet-half'},
            {'nombre': 'Aire Acondicionado', 'icono': 'bi-snow'},
            {'nombre': 'Calentador de Agua', 'icono': 'bi-thermometer-sun'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]
    },
    {
        'nombre': 'HVAC / Climatización',
        'codigo': 'hvac',
        'descripcion': 'Sistemas de calefacción, ventilación y aire acondicionado',
        'icono': 'bi-snow',
        'items': [
            {'nombre': 'Minisplit', 'icono': 'bi-snow'},
            {'nombre': 'Aire Central', 'icono': 'bi-wind'},
            {'nombre': 'Chiller', 'icono': 'bi-snow2'},
            {'nombre': 'Calefactor', 'icono': 'bi-thermometer-sun'},
            {'nombre': 'Ventilador Industrial', 'icono': 'bi-fan'},
            {'nombre': 'Extractor', 'icono': 'bi-arrow-up-circle'},
            {'nombre': 'Manejadora de Aire', 'icono': 'bi-wind'},
            {'nombre': 'Torre de Enfriamiento', 'icono': 'bi-water'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]
    },
    {
        'nombre': 'Elevadores',
        'codigo': 'elevadores',
        'descripcion': 'Elevadores, escaleras eléctricas y montacargas',
        'icono': 'bi-arrow-up-square',
        'items': [
            {'nombre': 'Elevador de Pasajeros', 'icono': 'bi-arrow-up-square'},
            {'nombre': 'Elevador de Carga', 'icono': 'bi-box-arrow-up'},
            {'nombre': 'Escalera Eléctrica', 'icono': 'bi-ladder'},
            {'nombre': 'Montacargas', 'icono': 'bi-truck'},
            {'nombre': 'Plataforma Elevadora', 'icono': 'bi-arrows-expand'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]
    },
    {
        'nombre': 'Equipo Médico',
        'codigo': 'equipo_medico',
        'descripcion': 'Equipamiento médico y hospitalario',
        'icono': 'bi-heart-pulse',
        'items': [
            {'nombre': 'Rayos X', 'icono': 'bi-radioactive'},
            {'nombre': 'Ultrasonido', 'icono': 'bi-soundwave'},
            {'nombre': 'Tomógrafo', 'icono': 'bi-circle'},
            {'nombre': 'Resonancia Magnética', 'icono': 'bi-magnet'},
            {'nombre': 'Cama Eléctrica', 'icono': 'bi-hospital'},
            {'nombre': 'Monitor de Signos', 'icono': 'bi-heart-pulse'},
            {'nombre': 'Ventilador Médico', 'icono': 'bi-lungs'},
            {'nombre': 'Esterilizador', 'icono': 'bi-shield-check'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]
    },
    {
        'nombre': 'Restaurantes / Cocina Industrial',
        'codigo': 'restaurantes',
        'descripcion': 'Equipos de cocina industrial y restaurantes',
        'icono': 'bi-cup-hot',
        'items': [
            {'nombre': 'Horno Industrial', 'icono': 'bi-fire'},
            {'nombre': 'Freidora', 'icono': 'bi-droplet-fill'},
            {'nombre': 'Plancha', 'icono': 'bi-grid'},
            {'nombre': 'Cámara Fría', 'icono': 'bi-snow3'},
            {'nombre': 'Congelador', 'icono': 'bi-thermometer-snow'},
            {'nombre': 'Máquina de Hielo', 'icono': 'bi-snow'},
            {'nombre': 'Lavavajillas Industrial', 'icono': 'bi-droplet'},
            {'nombre': 'Campana Extractora', 'icono': 'bi-cloud-arrow-up'},
            {'nombre': 'Otro', 'icono': 'bi-gear'},
        ]
    },
]


def crear_plantillas_predefinidas():
    """Crea las plantillas predefinidas si no existen"""
    creadas = 0
    for plantilla_data in PLANTILLAS_PREDEFINIDAS:
        if not PlantillaTipoEquipo.query.filter_by(codigo=plantilla_data['codigo']).first():
            plantilla = PlantillaTipoEquipo(
                nombre=plantilla_data['nombre'],
                codigo=plantilla_data['codigo'],
                descripcion=plantilla_data['descripcion'],
                icono=plantilla_data['icono'],
                orden=creadas
            )
            db.session.add(plantilla)
            db.session.flush()

            for i, item_data in enumerate(plantilla_data['items']):
                item = PlantillaTipoEquipoItem(
                    plantilla_id=plantilla.id,
                    nombre=item_data['nombre'],
                    icono=item_data['icono'],
                    orden=i
                )
                db.session.add(item)

            creadas += 1

    if creadas > 0:
        db.session.commit()

    return creadas
