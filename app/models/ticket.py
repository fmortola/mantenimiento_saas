from app import db
from datetime import datetime

# Tabla de asociación para técnicos asignados a tickets
tecnicos_ticket = db.Table('tecnicos_ticket',
    db.Column('tecnico_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('ticket_id', db.Integer, db.ForeignKey('ticket.id'), primary_key=True)
)

class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    asunto = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50))  # problema_equipo, problema_general, solicitud
    prioridad = db.Column(db.String(20), default='normal')
    estado = db.Column(db.String(30), default='abierto')  # abierto, asignado, en_progreso, resuelto, cerrado
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_asignacion = db.Column(db.DateTime)
    fecha_resolucion = db.Column(db.DateTime)
    respuesta_admin = db.Column(db.Text)

    # Tenant (multi-tenancy)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)

    # Relaciones
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicacion.id'), nullable=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=True)
    creado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    asignado_a_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    creado_por = db.relationship('Usuario', foreign_keys=[creado_por_id], backref='tickets_creados')
    asignado_a = db.relationship('Usuario', foreign_keys=[asignado_a_id], backref='tickets_asignados_legacy')

    # Relación muchos a muchos con técnicos
    tecnicos = db.relationship('Usuario', secondary=tecnicos_ticket,
                               lazy='dynamic',
                               backref=db.backref('tickets_asignados', lazy='dynamic'))

    @staticmethod
    def generar_numero():
        ultimo = Ticket.query.order_by(Ticket.id.desc()).first()
        if ultimo:
            return f"TK-{ultimo.id + 1:06d}"
        return "TK-000001"

    def __repr__(self):
        return f'<Ticket {self.numero}>'


TIPOS_TICKET = [
    ('problema_equipo', 'Problema con Equipo'),
    ('problema_general', 'Problema General'),
    ('solicitud', 'Solicitud de Servicio'),
    ('consulta', 'Consulta')
]

ESTADOS_TICKET = [
    ('abierto', 'Abierto'),
    ('asignado', 'Asignado'),
    ('en_progreso', 'En Progreso'),
    ('resuelto', 'Resuelto'),
    ('cerrado', 'Cerrado')
]
