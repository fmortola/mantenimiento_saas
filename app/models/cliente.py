from app import db
from datetime import datetime

class Cliente(db.Model):
    __tablename__ = 'cliente'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    rif = db.Column(db.String(20))
    email = db.Column(db.String(120))
    telefono_principal = db.Column(db.String(20))
    telefono_secundario = db.Column(db.String(20))
    persona_contacto = db.Column(db.String(100))
    notas = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Tenant (multi-tenancy)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)

    # Relaciones
    ubicaciones = db.relationship('Ubicacion', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')
    ordenes_trabajo = db.relationship('OrdenTrabajo', backref='cliente', lazy='dynamic')
    tickets = db.relationship('Ticket', backref='cliente', lazy='dynamic')
    mantenimientos = db.relationship('Mantenimiento', backref='cliente', lazy='dynamic')

    def total_equipos(self):
        total = 0
        for ubicacion in self.ubicaciones:
            total += ubicacion.equipos.count()
        return total

    def __repr__(self):
        return f'<Cliente {self.nombre}>'
