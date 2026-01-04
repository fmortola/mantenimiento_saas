from flask import g, redirect, url_for, flash, session
from flask_login import current_user
from functools import wraps


def get_current_tenant_id():
    """Obtiene el tenant_id del usuario actual o de la sesion de impersonacion"""
    if not current_user.is_authenticated:
        return None

    # Si es superadmin y esta impersonando un tenant
    if current_user.es_superadmin():
        return session.get('impersonate_tenant_id')

    return current_user.tenant_id


def get_current_tenant():
    """Obtiene el objeto Tenant actual"""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        return None

    from app.models.tenant import Tenant
    return Tenant.query.get(tenant_id)


def tenant_required(f):
    """Decorador que verifica que el usuario tenga un tenant valido y activo"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesion.', 'warning')
            return redirect(url_for('auth.login'))

        # SuperAdmin puede acceder sin tenant (a menos que este impersonando)
        if current_user.es_superadmin():
            return f(*args, **kwargs)

        # Verificar que tiene tenant
        if not current_user.tenant_id:
            flash('Tu cuenta no esta asociada a ninguna organizacion.', 'danger')
            return redirect(url_for('auth.logout'))

        # Verificar que el tenant esta activo
        if not current_user.tenant.esta_activo():
            flash('Tu organizacion no esta activa o ha vencido. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.logout'))

        return f(*args, **kwargs)
    return decorated_function


def superadmin_required(f):
    """Decorador que verifica permisos de superadmin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesion.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.es_superadmin():
            flash('Acceso denegado. Se requieren permisos de SuperAdmin.', 'danger')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function


def check_plan_limit(limit_type):
    """
    Decorador factory que verifica limites del plan antes de crear recursos.
    Uso: @check_plan_limit('tecnico') o @check_plan_limit('cliente')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.es_superadmin():
                return f(*args, **kwargs)

            tenant = current_user.tenant
            if not tenant:
                flash('Error: No hay tenant asociado.', 'danger')
                return redirect(url_for('admin.dashboard'))

            can_add = False
            mensaje = ''

            if limit_type == 'tecnico':
                can_add = tenant.puede_agregar_tecnico()
                mensaje = 'Has alcanzado el limite de tecnicos de tu plan.'
            elif limit_type == 'cliente':
                can_add = tenant.puede_agregar_cliente()
                mensaje = 'Has alcanzado el limite de clientes de tu plan.'
            elif limit_type == 'equipo':
                can_add = tenant.puede_agregar_equipo()
                mensaje = 'Has alcanzado el limite de equipos de tu plan.'

            if not can_add:
                flash(mensaje + ' Considera actualizar tu plan.', 'warning')
                return redirect(url_for('admin.dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
