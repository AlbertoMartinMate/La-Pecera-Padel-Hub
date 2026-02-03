"""
Script para convertir un usuario en administrador
Ejecuta esto una sola vez para hacerte admin
"""
from app import app, db, Usuario

def hacer_admin():
    with app.app_context():
        # Pregunta qué email quieres hacer admin
        email = input("Introduce el email del usuario que quieres hacer admin: ")
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            usuario.es_admin = True
            db.session.commit()
            print(f"✅ ¡{usuario.nombre} ahora es administrador!")
        else:
            print(f"❌ No se encontró ningún usuario con el email: {email}")
            print("\nUsuarios registrados:")
            todos = Usuario.query.all()
            for u in todos:
                print(f"  - {u.nombre} ({u.email})")

if __name__ == '__main__':
    hacer_admin()
