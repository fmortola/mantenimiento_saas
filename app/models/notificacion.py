from app import db
from datetime import datetime

class PushSubscription(db.Model):
    """Suscripciones para notificaciones push"""
    __tablename__ = 'push_subscription'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.String(255), nullable=False)
    auth = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref='push_subscriptions')

    def __repr__(self):
        return f'<PushSubscription {self.id}>'


class Notificacion(db.Model):
    """Historial de notificaciones"""
    __tablename__ = 'notificacion'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50))  # ticket_nuevo, ticket_asignado, orden_completada, etc
    leida = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_lectura = db.Column(db.DateTime)
    url = db.Column(db.String(255))  # URL para redirigir al hacer clic

    # Tenant (multi-tenancy) - nullable para notificaciones de superadmin
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('Usuario', backref='notificaciones')

    def __repr__(self):
        return f'<Notificacion {self.id}>'


TIPOS_NOTIFICACION = [
    ('ticket_nuevo', 'Nuevo Ticket'),
    ('ticket_asignado', 'Ticket Asignado'),
    ('orden_asignada', 'Orden de Trabajo Asignada'),
    ('orden_completada', 'Orden Completada'),
    ('mantenimiento_asignado', 'Mantenimiento Asignado'),
    ('mantenimiento_completado', 'Mantenimiento Completado'),
    ('equipo_nuevo', 'Nuevo Equipo Registrado')
]
