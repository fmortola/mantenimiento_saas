#!/usr/bin/env python3
"""
Script para resetear la base de datos en producción.
Ejecutar con: python3 reset_produccion.py

ADVERTENCIA: Este script BORRA TODOS LOS DATOS.
"""
import sys

print("=" * 60)
print("  RESET DE BASE DE DATOS - PRODUCCIÓN")
print("=" * 60)
print()
print("  ⚠️  ADVERTENCIA: Este script BORRARÁ TODOS LOS DATOS")
print()

confirmacion = input("Escribe 'BORRAR TODO' para continuar: ")

if confirmacion != "BORRAR TODO":
    print("\n❌ Operación cancelada.")
    sys.exit(0)

print("\n🔄 Iniciando reset...")

from app import create_app, db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.ubicacion import Ubicacion
from app.models.equipo import Equipo
from app.models.orden_trabajo import OrdenTrabajo, FotoTrabajo
from app.models.ticket import Ticket
from app.models.mantenimiento import Mantenimiento, MantenimientoEquipo
from app.models.notificacion import Notificacion, PushSubscription

app = create_app()

with app.app_context():
    print("📦 Eliminando todas las tablas...")
    db.drop_all()

    print("📦 Creando tablas nuevas...")
    db.create_all()

    print("👤 Creando usuario administrador...")

    # Datos del admin
    admin_email = input("\n📧 Email del administrador [admin@admin.com]: ").strip()
    if not admin_email:
        admin_email = "admin@admin.com"

    admin_nombre = input("👤 Nombre del administrador [Administrador]: ").strip()
    if not admin_nombre:
        admin_nombre = "Administrador"

    admin_password = input("🔑 Contraseña del administrador [admin123]: ").strip()
    if not admin_password:
        admin_password = "admin123"

    admin = Usuario(
        nombre=admin_nombre,
        email=admin_email,
        rol='admin',
        activo=True
    )
    admin.set_password(admin_password)

    db.session.add(admin)
    db.session.commit()

    print()
    print("=" * 60)
    print("  ✅ BASE DE DATOS RESETEADA EXITOSAMENTE")
    print("=" * 60)
    print()
    print(f"  Usuario: {admin_email}")
    print(f"  Contraseña: {admin_password}")
    print()
    print("  Ya puedes acceder al sistema.")
    print("=" * 60)
