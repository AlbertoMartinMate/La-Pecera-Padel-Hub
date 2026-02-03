# 🚀 Desplegar en Render - Guía Paso a Paso

## 📋 Preparativos

### 1. Actualizar archivos locales

Primero, actualiza estos archivos en tu proyecto local:

- **app.py** (actualizado para soportar PostgreSQL)
- **requirements.txt** (añadidas librerías para PostgreSQL y servidor)
- **render.yaml** (nuevo - configuración de Render)
- **.gitignore** (nuevo - evita subir archivos innecesarios)

### 2. Probar que todo sigue funcionando localmente

```bash
# Detén la app si está corriendo (Ctrl+C)

# Instala las nuevas dependencias
pip install -r requirements.txt

# Vuelve a ejecutar
python app.py
```

Verifica que todo funcione igual que antes. El código está preparado para usar SQLite en local y PostgreSQL en producción automáticamente.

---

## 🐙 Subir a GitHub

### Paso 1: Crear repositorio en GitHub

1. Ve a https://github.com
2. Haz clic en el botón verde "New" (arriba a la izquierda)
3. Nombre del repositorio: `padel-club-app` (o el que quieras)
4. Déjalo como **Private** (recomendado)
5. **NO marques** "Add a README file"
6. Click en "Create repository"

### Paso 2: Subir tu código

En tu terminal de WSL, dentro de la carpeta `la_pecera_padel_hub2`:

```bash
# Inicializar Git (si no lo has hecho ya)
git init

# Añadir todos los archivos
git add .

# Hacer el primer commit
git commit -m "Initial commit - App Club de Pádel"

# Conectar con tu repositorio de GitHub
# Reemplaza TU_USUARIO con tu usuario de GitHub
git remote add origin https://github.com/TU_USUARIO/padel-club-app.git

# Cambiar a la rama main
git branch -M main

# Subir el código
git push -u origin main
```

**Nota**: Te pedirá tu usuario y contraseña de GitHub. Para la contraseña, necesitas usar un **Personal Access Token** en vez de tu contraseña normal.

#### Crear un Personal Access Token:
1. Ve a GitHub → Settings (tu perfil) → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" → "Generate new token (classic)"
3. Nombre: "Render Deploy"
4. Selecciona: `repo` (todos los checkboxes de repo)
5. "Generate token"
6. **Copia el token** (solo se muestra una vez)
7. Usa ese token como contraseña cuando hagas `git push`

---

## 🌐 Desplegar en Render

### Paso 1: Crear cuenta en Render

1. Ve a https://render.com
2. Haz clic en "Get Started"
3. Regístrate con tu cuenta de GitHub (recomendado, es más fácil)

### Paso 2: Crear el servicio

1. Una vez dentro, haz clic en "New +"
2. Selecciona **"Blueprint"**
3. Conecta tu repositorio de GitHub `padel-club-app`
4. Render detectará automáticamente el archivo `render.yaml`
5. Dale un nombre al servicio (o deja el que sugiere)
6. Haz clic en **"Apply"**

### Paso 3: Esperar el despliegue

Render hará automáticamente:
- ✅ Crear la base de datos PostgreSQL
- ✅ Instalar las dependencias de Python
- ✅ Configurar las variables de entorno
- ✅ Arrancar tu aplicación

Esto tarda unos **5-10 minutos** la primera vez.

### Paso 4: Ver tu app funcionando

1. En el dashboard de Render, verás tu servicio
2. Arriba verás una URL tipo: `https://padel-club-xxx.onrender.com`
3. Haz clic en esa URL
4. ¡**Ya está en internet**! 🎉

---

## ⚙️ Crear tu primer usuario admin en producción

Una vez desplegada la app, necesitas crear tu usuario admin.

**Opción 1 - Desde la interfaz web:**
1. Ve a tu URL: `https://tu-app.onrender.com`
2. Regístrate con tu email
3. Luego, desde el dashboard de Render:
   - Ve a tu servicio web
   - Click en "Shell" (arriba a la derecha)
   - Ejecuta:
   ```bash
   python
   from app import app, db, Usuario
   with app.app_context():
       usuario = Usuario.query.filter_by(email='tu@email.com').first()
       usuario.es_admin = True
       db.session.commit()
       print("Admin creado!")
   exit()
   ```

**Opción 2 - Modificar el código (más fácil):**

Añade este código temporal en `app.py` justo antes de `if __name__ == '__main__':`:

```python
# TEMPORAL: Crear primer admin
with app.app_context():
    admin_email = "tu@email.com"  # Cambia esto
    usuario = Usuario.query.filter_by(email=admin_email).first()
    if usuario:
        usuario.es_admin = True
        db.session.commit()
```

Luego:
```bash
git add app.py
git commit -m "Crear admin inicial"
git push
```

Render redesplegará automáticamente. Luego quita ese código temporal.

---

## 🎯 Resultado Final

Tendrás:
- ✅ App funcionando en internet con un enlace público
- ✅ Base de datos PostgreSQL profesional
- ✅ Tus usuarios pueden registrarse desde cualquier lugar
- ✅ Tú puedes gestionar todo desde el panel admin
- ✅ Gratis (plan gratuito de Render)

## ⚠️ Limitaciones del plan gratuito

- La app "se duerme" tras 15 minutos sin uso
- La primera visita tras "despertar" tarda ~30 segundos
- Límite de 750 horas/mes (suficiente para MVP)
- Base de datos limitada a 1GB

**Nota**: Para tu club de pádel, esto es más que suficiente al principio.

---

## 🔄 Actualizar la app en el futuro

Cuando hagas cambios:

```bash
git add .
git commit -m "Descripción del cambio"
git push
```

Render detectará el cambio y redesplegará automáticamente. ¡Sin hacer nada más!

---

## 🆘 Solución de problemas

**"Build failed"**
- Revisa los logs en Render
- Normalmente es un error en `requirements.txt` o en el código

**"Application error"**
- Ve a Logs en Render para ver el error específico
- Puede ser un error de base de datos o de configuración

**"No puedo hacer push a GitHub"**
- Asegúrate de usar un Personal Access Token como contraseña
- Verifica que el remote está bien configurado: `git remote -v`

---

## 🎉 ¡Listo!

Cuando todo funcione, tendrás tu app del club de pádel funcionando en internet. Podrás compartir el enlace con los primeros usuarios y empezar a probarla de verdad.

**Siguiente paso**: Cuando esté desplegada, podemos añadir las funcionalidades que faltan (contenido general, estadísticas, etc.)
