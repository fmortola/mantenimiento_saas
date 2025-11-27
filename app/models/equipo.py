from app import db
from datetime import datetime

class Equipo(db.Model):
    __tablename__ = 'equipo'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # computadora, impresora, servidor, router, etc
    nombre = db.Column(db.String(100))  # Nombre identificador: "PC Gerencia", "Impresora Contabilidad"
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(100))
    serial = db.Column(db.String(100))
    departamento = db.Column(db.String(100))  # Donde está ubicado dentro de la oficina
    condicion = db.Column(db.String(50))  # bueno, regular, malo, fuera_de_servicio
    descripcion = db.Column(db.Text)
    foto = db.Column(db.String(255))  # Path a la foto del equipo
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicacion.id'), nullable=False)

    # Relaciones
    creado_por = db.relationship('Usuario', backref='equipos_creados')
    tickets = db.relationship('Ticket', backref='equipo', lazy='dynamic')
    ordenes_trabajo = db.relationship('OrdenTrabajo', backref='equipo', lazy='dynamic')
    mantenimientos_equipo = db.relationship('MantenimientoEquipo', backref='equipo', lazy='dynamic')

    def ultimo_mantenimiento(self):
        from app.models.mantenimiento import MantenimientoEquipo
        ultimo = MantenimientoEquipo.query.filter_by(
            equipo_id=self.id,
            estado='completado'
        ).order_by(MantenimientoEquipo.fecha_fin.desc()).first()
        return ultimo

    def __repr__(self):
        return f'<Equipo {self.tipo} - {self.nombre}>'


# Tipos de equipos predefinidos
TIPOS_EQUIPO = [
    ('computadora', 'Computadora'),
    ('laptop', 'Laptop'),
    ('impresora', 'Impresora'),
    ('servidor', 'Servidor'),
    ('router', 'Router'),
    ('switch', 'Switch'),
    ('ups', 'UPS'),
    ('scanner', 'Scanner'),
    ('monitor', 'Monitor'),
    ('otro', 'Otro')
]

CONDICIONES_EQUIPO = [
    ('excelente', 'Excelente'),
    ('bueno', 'Bueno'),
    ('regular', 'Regular'),
    ('malo', 'Malo'),
    ('fuera_de_servicio', 'Fuera de Servicio')
]
