from app import db
from datetime import datetime

class Ubicacion(db.Model):
    __tablename__ = 'ubicacion'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)  # Ej: "Oficina Principal", "Sucursal Norte"
    direccion = db.Column(db.String(300))
    ciudad = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    persona_contacto = db.Column(db.String(100))
    notas = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

    # Relaciones
    equipos = db.relationship('Equipo', backref='ubicacion', lazy='dynamic', cascade='all, delete-orphan')
    ordenes_trabajo = db.relationship('OrdenTrabajo', backref='ubicacion', lazy='dynamic')
    tickets = db.relationship('Ticket', backref='ubicacion', lazy='dynamic')
    mantenimientos = db.relationship('Mantenimiento', backref='ubicacion', lazy='dynamic')

    def __repr__(self):
        return f'<Ubicacion {self.nombre}>'
