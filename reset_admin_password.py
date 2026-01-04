#!/usr/bin/env python3
"""
Script para restablecer la contraseña del administrador.
Ejecutar en el servidor con el entorno virtual activo:
    source venv/bin/activate
    python3 reset_admin_password.py
"""
from app import create_app, db
from app.models.usuario import Usuario

def reset_password():
    app = create_app()
    with app.app_context():
        # Mostrar usuarios admin
        admins = Usuario.query.filter_by(rol='admin').all()

        if not admins:
            print("No hay usuarios administradores en el sistema.")
            return

        print("\nUsuarios administradores encontrados:")
        print("-" * 50)
        for admin in admins:
            print(f"  ID: {admin.id} | Email: {admin.email} | Nombre: {admin.nombre}")
        print("-" * 50)

        # Pedir email del admin
        email = input("\nIngresa el email del admin a restablecer: ").strip()

        admin = Usuario.query.filter_by(email=email, rol='admin').first()
        if not admin:
            print(f"No se encontró un admin con el email: {email}")
            return

        # Pedir nueva contraseña
        nueva_password = input("Ingresa la nueva contraseña: ").strip()
        if len(nueva_password) < 4:
            print("La contraseña debe tener al menos 4 caracteres.")
            return

        # Actualizar contraseña
        admin.set_password(nueva_password)
        db.session.commit()

        print(f"\n¡Contraseña actualizada exitosamente para {admin.nombre}!")
        print(f"Email: {admin.email}")

if __name__ == '__main__':
    reset_password()
