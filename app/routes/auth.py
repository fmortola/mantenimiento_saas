from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
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
        if current_user.es_admin():
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
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))

            login_user(usuario, remember=True)

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if usuario.es_admin():
                return redirect(url_for('admin.dashboard'))
            elif usuario.es_tecnico():
                return redirect(url_for('tecnico.dashboard'))
            elif usuario.es_cliente():
                return redirect(url_for('cliente.dashboard'))
        else:
            flash('Email o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))
