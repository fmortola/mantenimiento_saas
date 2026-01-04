from app import db
from datetime import datetime

class Mantenimiento(db.Model):
    """Mantenimiento programado para un cliente/ubicación - puede incluir múltiples equipos"""
    __tablename__ = 'mantenimiento'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # preventivo, correctivo, inventario
    estado = db.Column(db.String(30), default='programado')  # programado, en_progreso, completado, cancelado
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_programada = db.Column(db.DateTime)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    notas_admin = db.Column(db.Text)
    notas_cierre = db.Column(db.Text)

    # Firma del cliente al completar mantenimiento
    firma_cliente = db.Column(db.Text)  # Base64 de la firma
    firma_nombre = db.Column(db.String(100))  # Nombre de quien firma
    firma_fecha = db.Column(db.DateTime)  # Fecha/hora de la firma

    # Tenant (multi-tenancy)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)

    # Relaciones
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicacion.id'), nullable=False)
    creado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    creado_por = db.relationship('Usuario', foreign_keys=[creado_por_id], backref='mantenimientos_creados')
    equipos_mantenimiento = db.relationship('MantenimientoEquipo', backref='mantenimiento', lazy='dynamic', cascade='all, delete-orphan')
    tenant = db.relationship('Tenant', backref='mantenimientos')

    @staticmethod
    def generar_numero():
        ultimo = Mantenimiento.query.order_by(Mantenimiento.id.desc()).first()
        if ultimo:
            return f"MT-{ultimo.id + 1:06d}"
        return "MT-000001"

    def total_equipos(self):
        """Total de equipos en esta ubicación"""
        from app.models.equipo import Equipo
        return Equipo.query.filter_by(ubicacion_id=self.ubicacion_id, activo=True).count()

    def equipos_inventariados(self):
        """Equipos que ya están en el sistema para esta ubicación"""
        from app.models.equipo import Equipo
        return Equipo.query.filter_by(ubicacion_id=self.ubicacion_id, activo=True).count()

    def equipos_con_mantenimiento(self):
        """Equipos que ya tienen mantenimiento completado en este ciclo"""
        return self.equipos_mantenimiento.filter_by(estado='completado').count()

    def equipos_en_progreso(self):
        """Equipos en los que se está trabajando actualmente"""
        return self.equipos_mantenimiento.filter_by(estado='en_progreso').count()

    def equipos_pendientes(self):
        """Equipos pendientes de mantenimiento"""
        return self.equipos_mantenimiento.filter_by(estado='pendiente').count()

    def progreso_porcentaje(self):
        """Porcentaje de avance del mantenimiento"""
        total = self.equipos_mantenimiento.count()
        if total == 0:
            return 0
        completados = self.equipos_con_mantenimiento()
        return int((completados / total) * 100)

    def __repr__(self):
        return f'<Mantenimiento {self.numero}>'


class MantenimientoEquipo(db.Model):
    """Registro de mantenimiento individual por equipo"""
    __tablename__ = 'mantenimiento_equipo'

    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(30), default='pendiente')  # pendiente, en_progreso, completado
    descripcion_trabajo = db.Column(db.Text)
    condicion_inicial = db.Column(db.String(50))
    condicion_final = db.Column(db.String(50))
    observaciones = db.Column(db.Text)
    tiempo_minutos = db.Column(db.Integer)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)

    # Relaciones
    mantenimiento_id = db.Column(db.Integer, db.ForeignKey('mantenimiento.id'), nullable=False)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    tecnico = db.relationship('Usuario', backref='mantenimientos_equipo_realizados')
    fotos = db.relationship('FotoTrabajo', backref='mantenimiento_equipo', lazy='dynamic')

    def __repr__(self):
        return f'<MantenimientoEquipo {self.id}>'


TIPOS_MANTENIMIENTO = [
    ('preventivo', 'Mantenimiento Preventivo'),
    ('correctivo', 'Mantenimiento Correctivo'),
    ('inventario', 'Levantamiento de Inventario')
]

ESTADOS_MANTENIMIENTO = [
    ('programado', 'Programado'),
    ('en_progreso', 'En Progreso'),
    ('completado', 'Completado'),
    ('cancelado', 'Cancelado')
]
