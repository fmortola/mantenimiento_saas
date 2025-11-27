from app import db
from datetime import datetime

# Tabla de asociación para técnicos asignados a órdenes de trabajo
tecnicos_orden = db.Table('tecnicos_orden',
    db.Column('tecnico_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('orden_id', db.Integer, db.ForeignKey('orden_trabajo.id'), primary_key=True)
)

class OrdenTrabajo(db.Model):
    __tablename__ = 'orden_trabajo'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # reparacion, instalacion, revision, otro
    descripcion_solicitud = db.Column(db.Text, nullable=False)
    descripcion_trabajo = db.Column(db.Text)  # Lo que hizo el técnico
    prioridad = db.Column(db.String(20), default='normal')  # baja, normal, alta, urgente
    estado = db.Column(db.String(30), default='pendiente')  # pendiente, en_progreso, completado, cancelado
    tiempo_estimado = db.Column(db.Integer)  # En minutos
    tiempo_real = db.Column(db.Integer)  # En minutos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_programada = db.Column(db.DateTime)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    notas_admin = db.Column(db.Text)

    # Cliente rápido (para clientes nuevos que llaman)
    cliente_rapido_nombre = db.Column(db.String(200))
    cliente_rapido_telefono = db.Column(db.String(20))
    cliente_rapido_direccion = db.Column(db.String(300))

    # Relaciones
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicacion.id'), nullable=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    creado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    ticket_origen_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)

    creado_por = db.relationship('Usuario', foreign_keys=[creado_por_id], backref='ordenes_creadas')
    ticket_origen = db.relationship('Ticket', backref='orden_generada', foreign_keys=[ticket_origen_id])
    fotos = db.relationship('FotoTrabajo', backref='orden_trabajo', lazy='dynamic', cascade='all, delete-orphan')

    # Relación muchos a muchos con técnicos
    tecnicos = db.relationship('Usuario', secondary=tecnicos_orden,
                               lazy='dynamic',
                               backref=db.backref('ordenes_asignadas', lazy='dynamic'))

    @staticmethod
    def generar_numero():
        ultimo = OrdenTrabajo.query.order_by(OrdenTrabajo.id.desc()).first()
        if ultimo:
            return f"OT-{ultimo.id + 1:06d}"
        return "OT-000001"

    def __repr__(self):
        return f'<OrdenTrabajo {self.numero}>'


class FotoTrabajo(db.Model):
    __tablename__ = 'foto_trabajo'

    id = db.Column(db.Integer, primary_key=True)
    ruta = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(200))
    tipo = db.Column(db.String(20))  # antes, durante, despues
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    orden_trabajo_id = db.Column(db.Integer, db.ForeignKey('orden_trabajo.id'), nullable=True)
    mantenimiento_equipo_id = db.Column(db.Integer, db.ForeignKey('mantenimiento_equipo.id'), nullable=True)


TIPOS_ORDEN = [
    ('reparacion', 'Reparación'),
    ('instalacion', 'Instalación'),
    ('revision', 'Revisión'),
    ('configuracion', 'Configuración'),
    ('otro', 'Otro')
]

PRIORIDADES = [
    ('baja', 'Baja'),
    ('normal', 'Normal'),
    ('alta', 'Alta'),
    ('urgente', 'Urgente')
]

ESTADOS_ORDEN = [
    ('pendiente', 'Pendiente'),
    ('asignado', 'Asignado'),
    ('en_progreso', 'En Progreso'),
    ('completado', 'Completado'),
    ('cancelado', 'Cancelado')
]
