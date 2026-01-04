from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Tabla de asociación para técnicos asignados a mantenimientos
tecnicos_mantenimiento = db.Table('tecnicos_mantenimiento',
    db.Column('tecnico_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('mantenimiento_id', db.Integer, db.ForeignKey('mantenimiento.id'), primary_key=True)
)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    telefono = db.Column(db.String(20))
    rol = db.Column(db.String(20), nullable=False)  # superadmin, admin, tecnico, cliente
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacion con Tenant (NULL solo para superadmin)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', backref='usuarios')

    # Relación con cliente (si el usuario es de tipo cliente)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    cliente = db.relationship('Cliente', backref='usuarios', foreign_keys=[cliente_id])

    # Mantenimientos asignados al técnico
    mantenimientos_asignados = db.relationship('Mantenimiento', secondary=tecnicos_mantenimiento,
                                               lazy='dynamic',
                                               backref=db.backref('tecnicos', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def es_superadmin(self):
        return self.rol == 'superadmin'

    def es_admin(self):
        return self.rol == 'admin'

    def es_tecnico(self):
        return self.rol == 'tecnico'

    def es_cliente(self):
        return self.rol == 'cliente'

    def puede_acceder(self):
        """Verifica si el usuario puede acceder al sistema"""
        if self.es_superadmin():
            return True
        if not self.activo:
            return False
        if self.tenant and not self.tenant.esta_activo():
            return False
        return True

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
