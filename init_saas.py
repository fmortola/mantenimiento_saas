#!/usr/bin/env python3
"""
Script de inicializacion del SaaS.
Ejecutar para crear/recrear:
- Tablas de la base de datos
- Planes predefinidos
- Usuario SuperAdmin
- Tenant de demostracion con tipos de equipo
"""

from app import create_app, db
from app.models.plan import Plan, PLANES_PREDEFINIDOS
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.tipo_equipo import TipoEquipo
from app.models.plantilla_tipo_equipo import PlantillaTipoEquipo, crear_plantillas_predefinidas
from datetime import datetime, timedelta
import sys

def init_saas(drop_all=False):
    app = create_app()

    with app.app_context():
        print("=" * 50)
        print("Inicializacion del SaaS")
        print("=" * 50)

        # Opcion para borrar todo y empezar de cero
        if drop_all:
            print("\n[0/6] ELIMINANDO todas las tablas existentes...")
            db.drop_all()
            print("     Tablas eliminadas.")

        # Crear tablas
        print("\n[1/6] Creando tablas de base de datos...")
        db.create_all()
        print("     Tablas creadas correctamente.")

        # Crear planes predefinidos
        print("\n[2/6] Creando planes predefinidos...")
        planes_creados = 0
        for plan_data in PLANES_PREDEFINIDOS:
            if not Plan.query.filter_by(codigo=plan_data['codigo']).first():
                plan = Plan(**plan_data)
                db.session.add(plan)
                planes_creados += 1
                print(f"     + Plan '{plan_data['nombre']}' creado")

        db.session.commit()
        if planes_creados == 0:
            print("     Los planes ya existian.")
        else:
            print(f"     {planes_creados} planes creados.")

        # Crear plantillas de tipos de equipo predefinidas
        print("\n[3/6] Creando plantillas de tipos de equipo...")
        plantillas_creadas = crear_plantillas_predefinidas()
        if plantillas_creadas > 0:
            print(f"     {plantillas_creadas} plantillas creadas:")
            for p in PlantillaTipoEquipo.query.all():
                print(f"     + {p.nombre} ({p.items.count()} tipos)")
        else:
            print("     Las plantillas ya existian.")

        # Crear SuperAdmin
        print("\n[4/6] Creando usuario SuperAdmin...")
        superadmin = Usuario.query.filter_by(rol='superadmin').first()
        if not superadmin:
            superadmin = Usuario(
                nombre='Fernando Mortola',
                email='fmortola@gmail.com',
                telefono='0000000000',
                rol='superadmin',
                tenant_id=None,  # SuperAdmin no tiene tenant
                activo=True
            )
            superadmin.set_password('Bruno2@@1')
            db.session.add(superadmin)
            db.session.commit()
            print("     SuperAdmin creado:")
            print("     Email: fmortola@gmail.com")
            print("     Password: Bruno2@@1")
        else:
            print(f"     SuperAdmin ya existe: {superadmin.email}")

        # Crear tenant de demostracion
        print("\n[5/6] Creando tenant de demostracion...")
        plan_basico = Plan.query.filter_by(codigo='basico').first()
        tenant_demo = Tenant.query.filter_by(slug='demo').first()

        if plan_basico and not tenant_demo:
            tenant_demo = Tenant(
                nombre='Empresa Demo',
                slug='demo',
                email_contacto='demo@empresa.com',
                telefono='0000000000',
                plan_id=plan_basico.id,
                fecha_vencimiento=datetime.utcnow() + timedelta(days=30),
                activo=True
            )
            db.session.add(tenant_demo)
            db.session.flush()

            # Admin del tenant demo
            admin_demo = Usuario(
                nombre='Admin Demo',
                email='admin@demo.com',
                telefono='0000000000',
                rol='admin',
                tenant_id=tenant_demo.id,
                activo=True
            )
            admin_demo.set_password('demoIN5940')
            db.session.add(admin_demo)

            # Tecnico del tenant demo
            tecnico_demo = Usuario(
                nombre='Tecnico Demo',
                email='tecnico@demo.com',
                telefono='0000000000',
                rol='tecnico',
                tenant_id=tenant_demo.id,
                activo=True
            )
            tecnico_demo.set_password('demoIN5940')
            db.session.add(tecnico_demo)

            db.session.commit()
            print("     Tenant Demo creado:")
            print("     Admin: admin@demo.com / demoIN5940")
            print("     Tecnico: tecnico@demo.com / demoIN5940")
        elif tenant_demo:
            print(f"     Tenant demo ya existe: {tenant_demo.nombre}")
        else:
            print("     No se pudo crear tenant demo (plan basico no encontrado)")

        # Crear tipos de equipo para el tenant demo usando plantilla
        print("\n[6/6] Creando tipos de equipo para tenant demo...")
        if tenant_demo:
            tipos_existentes = TipoEquipo.query.filter_by(tenant_id=tenant_demo.id).count()
            if tipos_existentes == 0:
                # Usar la primera plantilla (Computo/TI) para el demo
                plantilla_computo = PlantillaTipoEquipo.query.filter_by(codigo='computo_ti').first()
                if plantilla_computo:
                    plantilla_computo.aplicar_a_tenant(tenant_demo.id)
                    print(f"     Plantilla '{plantilla_computo.nombre}' aplicada al tenant demo.")
                else:
                    # Fallback: usar el metodo antiguo
                    TipoEquipo.crear_tipos_default(tenant_demo.id)
                    print("     Tipos de equipo por defecto creados.")
            else:
                print(f"     Ya existen {tipos_existentes} tipos de equipo.")
        else:
            print("     No se crearon tipos (tenant demo no existe).")

        print("\n" + "=" * 50)
        print("Inicializacion completada!")
        print("=" * 50)
        print("\nCredenciales:")
        print("-" * 50)
        print("SuperAdmin: fmortola@gmail.com / Bruno2@@1")
        print("Admin Demo: admin@demo.com / demoIN5940")
        print("Tecnico Demo: tecnico@demo.com / demoIN5940")
        print("-" * 50)
        print("\nProximos pasos:")
        print("1. Inicia la aplicacion: python run.py")
        print("2. Accede como SuperAdmin para gestionar tenants")
        print("3. O accede como Admin Demo para probar el sistema")


if __name__ == '__main__':
    # Si se pasa --reset, borrar todo y empezar de cero
    drop_all = '--reset' in sys.argv

    if drop_all:
        print("\n*** MODO RESET: Se eliminaran TODAS las tablas ***")
        respuesta = input("Estas seguro? (escribe 'SI' para confirmar): ")
        if respuesta != 'SI':
            print("Operacion cancelada.")
            sys.exit(0)

    init_saas(drop_all=drop_all)
