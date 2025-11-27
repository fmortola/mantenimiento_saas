#!/usr/bin/env python3
"""
Script para probar notificaciones push.
Ejecutar: python3 test_push.py <email_usuario>
"""
import sys
from app import create_app, db
from app.models.usuario import Usuario
from app.services.notificaciones import enviar_notificacion_push

app = create_app()

with app.app_context():
    if len(sys.argv) < 2:
        print("Uso: python3 test_push.py <email_usuario>")
        print("\nUsuarios disponibles:")
        usuarios = Usuario.query.filter_by(activo=True).all()
        for u in usuarios:
            from app.models.notificacion import PushSubscription
            subs = PushSubscription.query.filter_by(usuario_id=u.id).count()
            print(f"  - {u.email} ({u.rol}) - {subs} suscripciones")
        sys.exit(1)

    email = sys.argv[1]
    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario:
        print(f"Usuario {email} no encontrado")
        sys.exit(1)

    print(f"Enviando notificación de prueba a {usuario.nombre} ({usuario.email})...")

    resultado = enviar_notificacion_push(
        usuario,
        "Prueba de Notificación",
        "Esta es una notificación de prueba del sistema",
        "/"
    )

    if resultado:
        print("Notificación enviada correctamente!")
    else:
        print("Error al enviar la notificación")
