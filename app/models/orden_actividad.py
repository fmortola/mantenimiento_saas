from app import db
from datetime import datetime

class OrdenActividad(db.Model):
    """Registro de actividades realizadas en una orden de trabajo"""
    __tablename__ = 'orden_actividad'

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('orden_trabajo.id'), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    tiempo_minutos = db.Column(db.Integer, nullable=False, default=0)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    tecnico = db.relationship('Usuario', backref='actividades_orden')

    def __repr__(self):
        return f'<OrdenActividad {self.id} - {self.tiempo_minutos}min>'
