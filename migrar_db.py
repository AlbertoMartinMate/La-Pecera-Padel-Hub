"""
Script de migración para actualizar la base de datos con los nuevos campos
Ejecuta esto UNA SOLA VEZ después de actualizar app.py
"""
from app import app, db
from sqlalchemy import text

def migrar_base_datos():
    with app.app_context():
        print("🔄 Iniciando migración de base de datos...")
        
        try:
            # Intentar añadir las nuevas columnas
            with db.engine.connect() as conn:
                # Nivel Playtomic
                try:
                    conn.execute(text('ALTER TABLE usuario ADD COLUMN nivel_playtomic FLOAT DEFAULT 0.0'))
                    conn.commit()
                    print("✅ Añadida columna: nivel_playtomic")
                except Exception as e:
                    print(f"⚠️  nivel_playtomic ya existe o error: {e}")
                
                # Foto perfil
                try:
                    conn.execute(text("ALTER TABLE usuario ADD COLUMN foto_perfil VARCHAR(200) DEFAULT 'default.png'"))
                    conn.commit()
                    print("✅ Añadida columna: foto_perfil")
                except Exception as e:
                    print(f"⚠️  foto_perfil ya existe o error: {e}")
                
                # Puntos ranking
                try:
                    conn.execute(text('ALTER TABLE usuario ADD COLUMN puntos_ranking INTEGER DEFAULT 0'))
                    conn.commit()
                    print("✅ Añadida columna: puntos_ranking")
                except Exception as e:
                    print(f"⚠️  puntos_ranking ya existe o error: {e}")
                
                # Categoría
                try:
                    conn.execute(text("ALTER TABLE usuario ADD COLUMN categoria VARCHAR(20) DEFAULT 'Bronce'"))
                    conn.commit()
                    print("✅ Añadida columna: categoria")
                except Exception as e:
                    print(f"⚠️  categoria ya existe o error: {e}")
                
                # Teléfono
                try:
                    conn.execute(text('ALTER TABLE usuario ADD COLUMN telefono VARCHAR(20)'))
                    conn.commit()
                    print("✅ Añadida columna: telefono")
                except Exception as e:
                    print(f"⚠️  telefono ya existe o error: {e}")
                
                # Acepta términos
                try:
                    conn.execute(text('ALTER TABLE usuario ADD COLUMN acepta_terminos BOOLEAN DEFAULT 1'))
                    conn.commit()
                    print("✅ Añadida columna: acepta_terminos")
                except Exception as e:
                    print(f"⚠️  acepta_terminos ya existe o error: {e}")
            
            print("\n✅ ¡Migración completada exitosamente!")
            print("\nNOTA: Los usuarios existentes tienen valores por defecto:")
            print("  - nivel_playtomic: 0.0")
            print("  - foto_perfil: 'default.png'")
            print("  - puntos_ranking: 0")
            print("  - categoria: 'Bronce'")
            print("  - acepta_terminos: True")
            print("\nPuedes actualizar estos valores manualmente desde el panel de admin.")
            
        except Exception as e:
            print(f"\n❌ Error durante la migración: {e}")
            print("\nSi el error persiste, puede que necesites recrear la base de datos.")

if __name__ == '__main__':
    migrar_base_datos()
