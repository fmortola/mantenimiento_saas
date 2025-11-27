#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de ejemplo
"""
from app import create_app, db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.ubicacion import Ubicacion
from app.models.equipo import Equipo

def init_database():
    app = create_app()

    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("Tablas creadas correctamente")

        # Verificar si ya existe el admin
        admin = Usuario.query.filter_by(email='admin@admin.com').first()
        if not admin:
            # Crear administrador
            admin = Usuario(
                nombre='Administrador',
                email='admin@admin.com',
                telefono='0412-1234567',
                rol='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Usuario admin creado: admin@admin.com / admin123")

        # Crear técnico de ejemplo si no existe
        tecnico = Usuario.query.filter_by(email='tecnico@demo.com').first()
        if not tecnico:
            tecnico = Usuario(
                nombre='Juan Técnico',
                email='tecnico@demo.com',
                telefono='0412-7654321',
                rol='tecnico'
            )
            tecnico.set_password('tecnico123')
            db.session.add(tecnico)
            print("Usuario técnico creado: tecnico@demo.com / tecnico123")

        # Crear cliente de ejemplo si no existe
        cliente = Cliente.query.filter_by(nombre='Empresa Demo S.A.').first()
        if not cliente:
            cliente = Cliente(
                nombre='Empresa Demo S.A.',
                rif='J-12345678-9',
                email='contacto@empresademo.com',
                telefono_principal='0212-1234567',
                persona_contacto='María García'
            )
            db.session.add(cliente)
            db.session.flush()

            # Crear ubicación
            ubicacion = Ubicacion(
                nombre='Oficina Principal',
                direccion='Av. Principal, Torre Centro, Piso 5',
                ciudad='Caracas',
                estado='Distrito Capital',
                telefono='0212-1234567',
                cliente_id=cliente.id
            )
            db.session.add(ubicacion)
            db.session.flush()

            # Crear equipos de ejemplo
            equipos = [
                Equipo(tipo='computadora', nombre='PC Gerencia', marca='Dell', modelo='OptiPlex 7090',
                       departamento='Gerencia', condicion='bueno', ubicacion_id=ubicacion.id),
                Equipo(tipo='computadora', nombre='PC Contabilidad', marca='HP', modelo='ProDesk 400',
                       departamento='Contabilidad', condicion='bueno', ubicacion_id=ubicacion.id),
                Equipo(tipo='impresora', nombre='Impresora Principal', marca='HP', modelo='LaserJet Pro M404',
                       departamento='Recepción', condicion='excelente', ubicacion_id=ubicacion.id),
            ]
            for equipo in equipos:
                db.session.add(equipo)

            # Crear usuario para el cliente
            usuario_cliente = Usuario(
                nombre='María García',
                email='cliente@demo.com',
                telefono='0412-9876543',
                rol='cliente',
                cliente_id=cliente.id
            )
            usuario_cliente.set_password('cliente123')
            db.session.add(usuario_cliente)
            print("Usuario cliente creado: cliente@demo.com / cliente123")

        db.session.commit()
        print("\n¡Base de datos inicializada correctamente!")
        print("\nUsuarios de prueba:")
        print("  Admin: admin@admin.com / admin123")
        print("  Técnico: tecnico@demo.com / tecnico123")
        print("  Cliente: cliente@demo.com / cliente123")

if __name__ == '__main__':
    init_database()
