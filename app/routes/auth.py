from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app import db
from app.models.usuario import Usuario

auth_bp = Blueprint('auth', __name__)

# Rutas para PWA (manifest y service worker en raíz)
@auth_bp.route('/manifest.json')
def manifest():
    return send_from_directory(current_app.static_folder, 'manifest.json')

@auth_bp.route('/sw.js')
def service_worker():
    return send_from_directory(current_app.static_folder + '/js', 'sw.js', mimetype='application/javascript')

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.es_superadmin():
            return redirect(url_for('superadmin.dashboard'))
        elif current_user.es_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.es_tecnico():
            return redirect(url_for('tecnico.dashboard'))
        elif current_user.es_cliente():
            return redirect(url_for('cliente.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta esta desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))

            # Verificar tenant activo (excepto superadmin y clientes)
            if not usuario.es_superadmin():
                if not usuario.tenant:
                    flash('Tu cuenta no esta asociada a ninguna organizacion.', 'danger')
                    return redirect(url_for('auth.login'))

                # Los clientes pueden acceder aunque el tenant este vencido (solo lectura)
                # Los admins y tecnicos NO pueden acceder si el tenant esta vencido
                if not usuario.tenant.esta_activo() and not usuario.es_cliente():
                    flash('La suscripcion de tu organizacion ha vencido. Comunicate con soporte para renovar.', 'danger')
                    return redirect(url_for('auth.login'))

            login_user(usuario, remember=True)

            # Limpiar variables de impersonación si no es superadmin
            if not usuario.es_superadmin():
                session.pop('impersonate_tenant_id', None)
                session.pop('impersonate_tenant_nombre', None)

            # Verificar si acepto la politica de privacidad (excepto superadmin)
            if not usuario.es_superadmin() and not usuario.acepto_politica:
                return redirect(url_for('auth.aceptar_politica'))

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if usuario.es_superadmin():
                return redirect(url_for('superadmin.dashboard'))
            elif usuario.es_admin():
                return redirect(url_for('admin.dashboard'))
            elif usuario.es_tecnico():
                return redirect(url_for('tecnico.dashboard'))
            elif usuario.es_cliente():
                return redirect(url_for('cliente.dashboard'))
        else:
            flash('Email o contrasena incorrectos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/aceptar-politica', methods=['GET', 'POST'])
@login_required
def aceptar_politica():
    # Si ya acepto, redirigir al dashboard
    if current_user.acepto_politica:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        if request.form.get('acepto'):
            current_user.acepto_politica = True
            current_user.fecha_acepto_politica = datetime.utcnow()
            db.session.commit()
            flash('Gracias por aceptar nuestra politica de privacidad.', 'success')

            # Redirigir al dashboard correspondiente
            if current_user.es_admin():
                return redirect(url_for('admin.dashboard'))
            elif current_user.es_tecnico():
                return redirect(url_for('tecnico.dashboard'))
            elif current_user.es_cliente():
                return redirect(url_for('cliente.dashboard'))

            return redirect(url_for('auth.index'))

    return render_template('auth/aceptar_politica.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        password_actual = request.form.get('password_actual')
        password_nuevo = request.form.get('password_nuevo')
        password_confirmar = request.form.get('password_confirmar')

        # Validar contraseña actual
        if not current_user.check_password(password_actual):
            flash('La contraseña actual es incorrecta.', 'danger')
            return redirect(url_for('auth.cambiar_password'))

        # Validar que las nuevas contraseñas coincidan
        if password_nuevo != password_confirmar:
            flash('Las contraseñas nuevas no coinciden.', 'danger')
            return redirect(url_for('auth.cambiar_password'))

        # Validar longitud mínima
        if len(password_nuevo) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return redirect(url_for('auth.cambiar_password'))

        # Cambiar contraseña
        current_user.set_password(password_nuevo)
        db.session.commit()

        flash('Contrasena cambiada exitosamente.', 'success')

        # Redirigir al dashboard correspondiente
        if current_user.es_superadmin():
            return redirect(url_for('superadmin.dashboard'))
        elif current_user.es_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.es_tecnico():
            return redirect(url_for('tecnico.dashboard'))
        elif current_user.es_cliente():
            return redirect(url_for('cliente.dashboard'))

        return redirect(url_for('auth.index'))

    return render_template('auth/cambiar_password.html')
