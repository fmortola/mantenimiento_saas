from app import db
from datetime import datetime


class Tenant(db.Model):
    """Representa una empresa/organizacion que usa el SaaS"""
    __tablename__ = 'tenant'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    email_contacto = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20))

    # Branding
    logo = db.Column(db.String(255))

    # Estado y fechas
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.DateTime)

    # Configuración de reportes mensuales
    dia_envio_reportes = db.Column(db.Integer, default=28)  # Día del mes para enviar reportes (1-28)

    # Plan
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)

    # Relaciones
    plan = db.relationship('Plan', backref='tenants')

    def __repr__(self):
        return f'<Tenant {self.nombre}>'

    def puede_agregar_tecnico(self):
        """Verifica si puede agregar mas tecnicos segun el plan"""
        from app.models.usuario import Usuario
        tecnicos_actuales = Usuario.query.filter_by(
            tenant_id=self.id,
            rol='tecnico',
            activo=True
        ).count()
        return tecnicos_actuales < self.plan.max_tecnicos

    def puede_agregar_cliente(self):
        """Verifica si puede agregar mas clientes segun el plan"""
        from app.models.cliente import Cliente
        clientes_actuales = Cliente.query.filter_by(
            tenant_id=self.id,
            activo=True
        ).count()
        return clientes_actuales < self.plan.max_clientes

    def puede_agregar_equipo(self):
        """Verifica si puede agregar mas equipos segun el plan"""
        from app.models.equipo import Equipo
        equipos_actuales = Equipo.query.filter_by(
            tenant_id=self.id,
            activo=True
        ).count()
        return equipos_actuales < self.plan.max_equipos

    def esta_activo(self):
        """Verifica si el tenant esta activo y no vencido"""
        if not self.activo:
            return False
        if self.fecha_vencimiento and self.fecha_vencimiento < datetime.utcnow():
            return False
        return True

    def get_estadisticas(self):
        """Obtiene estadisticas del tenant"""
        from app.models.usuario import Usuario
        from app.models.cliente import Cliente
        from app.models.equipo import Equipo
        from app.models.orden_trabajo import OrdenTrabajo
        from app.models.ticket import Ticket

        return {
            'tecnicos': Usuario.query.filter_by(tenant_id=self.id, rol='tecnico', activo=True).count(),
            'admins': Usuario.query.filter_by(tenant_id=self.id, rol='admin', activo=True).count(),
            'clientes': Cliente.query.filter_by(tenant_id=self.id, activo=True).count(),
            'equipos': Equipo.query.filter_by(tenant_id=self.id, activo=True).count(),
            'ordenes_activas': OrdenTrabajo.query.filter(
                OrdenTrabajo.tenant_id == self.id,
                OrdenTrabajo.estado.in_(['pendiente', 'asignado', 'en_progreso'])
            ).count(),
            'tickets_abiertos': Ticket.query.filter(
                Ticket.tenant_id == self.id,
                Ticket.estado.in_(['abierto', 'asignado', 'en_progreso'])
            ).count()
        }
