# 🚀 Fase 1: Base de Datos y Registro Mejorado

## ✅ Lo que hemos actualizado

### **Modelo de Usuario ampliado:**
- ✅ `nivel_playtomic` → Nivel de Playtomic del jugador (Float: 0.0 - 7.0)
- ✅ `foto_perfil` → URL/nombre de archivo de foto (default: 'default.png')
- ✅ `puntos_ranking` → Puntos para el ranking del club (Integer)
- ✅ `categoria` → Bronce/Plata/Oro según participaciones
- ✅ `telefono` → Teléfono opcional
- ✅ `acepta_terminos` → Aceptación de términos RGPD

### **Formulario de registro mejorado:**
- ✅ Campo "Nivel Playtomic" obligatorio (0-7, con decimales)
- ✅ Placeholder en email: "mismo correo de Playtomic"
- ✅ Checkbox de aceptación de términos y condiciones
- ✅ Validación de aceptación de términos

## 📦 Archivos modificados/nuevos

**Actualizados:**
- `app.py` → Modelo Usuario ampliado + ruta de registro actualizada
- `templates/registro.html` → Formulario con nuevos campos

**Nuevos:**
- `migrar_db.py` → Script para migrar la base de datos existente

## 🔄 Cómo aplicar los cambios

### **IMPORTANTE - Orden de ejecución:**

#### 1️⃣ **En LOCAL (para probar):**

```bash
# 1. Reemplaza los archivos actualizados
# - app.py
# - templates/registro.html

# 2. Añade el archivo nuevo
# - migrar_db.py

# 3. Ejecuta la migración (IMPORTANTE)
python migrar_db.py

# 4. Prueba la app
python app.py
```

Ve a `http://localhost:5000/registro` y prueba el nuevo formulario.

---

#### 2️⃣ **En PRODUCCIÓN (Render):**

**Opción A - Recrear base de datos (RECOMENDADO si tienes pocos usuarios):**

Esta es la forma más limpia si todavía no tienes muchos usuarios registrados.

1. Ve a Render → Tu base de datos PostgreSQL
2. Click en "Settings" → Scroll abajo → "Delete Database"
3. Crear nueva base de datos con el mismo nombre
4. Volver a conectarla a tu app (añadir DATABASE_URL)
5. Subir el código actualizado:
   ```bash
   git add .
   git commit -m "Fase 1: Mejorar registro y base de datos"
   git push
   ```
6. La base de datos se creará con la nueva estructura
7. Registrarte de nuevo y hacerte admin

**Opción B - Migrar base de datos existente (si quieres mantener usuarios):**

1. Sube el código a GitHub:
   ```bash
   git add .
   git commit -m "Fase 1: Mejorar registro y base de datos"
   git push
   ```

2. Espera a que Render redespliegue

3. Ve a Render → Tu servicio web → "Shell" (⚠️ necesitas plan Starter)
   
4. Ejecuta en la shell:
   ```bash
   python migrar_db.py
   ```

**Opción C - Migración manual (si no tienes Shell):**

Añade este código temporal al final de `app.py`, justo antes de `if __name__ == '__main__':`:

```python
# TEMPORAL - Migración automática al arrancar
with app.app_context():
    from sqlalchemy import text
    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE usuario ADD COLUMN nivel_playtomic FLOAT DEFAULT 0.0'))
            conn.execute(text("ALTER TABLE usuario ADD COLUMN foto_perfil VARCHAR(200) DEFAULT 'default.png'"))
            conn.execute(text('ALTER TABLE usuario ADD COLUMN puntos_ranking INTEGER DEFAULT 0'))
            conn.execute(text("ALTER TABLE usuario ADD COLUMN categoria VARCHAR(20) DEFAULT 'Bronce'"))
            conn.execute(text('ALTER TABLE usuario ADD COLUMN telefono VARCHAR(20)'))
            conn.execute(text('ALTER TABLE usuario ADD COLUMN acepta_terminos BOOLEAN DEFAULT 1'))
            conn.commit()
            print("✅ Migración completada")
    except Exception as e:
        print(f"Migración ya aplicada o error: {e}")
```

Luego:
1. Sube el código con este bloque temporal
2. Render redesplegará y ejecutará la migración
3. Verifica que funcione
4. **QUITA** ese código temporal
5. Sube de nuevo sin el código temporal

---

## 🧪 Cómo probar que funciona

### **Test 1: Registro nuevo usuario**
1. Ve a `/registro`
2. Rellena todos los campos incluyendo nivel Playtomic (ej: 3.5)
3. Marca el checkbox de términos
4. Regístrate
5. Verifica que puedes iniciar sesión

### **Test 2: Usuarios existentes**
Los usuarios que ya existen deberían tener valores por defecto:
- nivel_playtomic: 0.0
- categoria: Bronce
- puntos_ranking: 0
- acepta_terminos: True

Puedes actualizarlos manualmente más adelante.

---

## 📝 Notas importantes

### **Sobre el nivel Playtomic:**
- Los usuarios lo meten al registrarse
- Solo el admin puede modificarlo después (implementaremos esto en la siguiente fase)
- Rango válido: 0.0 a 7.0 (con decimales: 2.5, 3.0, 4.5, etc.)

### **Sobre las categorías:**
- Por defecto todos empiezan en "Bronce"
- Cuando implementemos el sistema de pozos, se actualizará automáticamente:
  - Bronce: < 5 pozos
  - Plata: 5-15 pozos
  - Oro: > 15 pozos

### **Sobre la foto de perfil:**
- Por defecto: 'default.png'
- En la siguiente fase implementaremos subida de fotos
- Por ahora mostrará un avatar con la inicial del nombre

### **Sobre términos y condiciones:**
- Por ahora son enlaces de placeholder (#)
- En la siguiente fase crearemos las páginas reales de términos y privacidad

---

## 🎯 Siguiente paso

Cuando esto funcione, seguimos con **Fase 2: Sistema de Pozos**:
- Modelo Pozo en base de datos
- Panel admin: crear pozos
- Meter participantes por email
- Registrar resultados (Top 3)
- Cálculo automático de puntos/ranking

---

**¿Algún problema con la migración?** Avísame y te ayudo 👍
