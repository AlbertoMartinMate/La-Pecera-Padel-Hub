# 🎾 App Club de Pádel - MVP

## 📋 Lo que tienes ahora

Una aplicación web funcional con:
- ✅ Registro de usuarios
- ✅ Login/Logout
- ✅ Dashboard personal
- ✅ Base de datos SQLite (luego migraremos a PostgreSQL)
- ✅ Contraseñas seguras (hasheadas)

## 🚀 Cómo probarlo en tu WSL Ubuntu

### Paso 1: Preparar el entorno

Abre tu WSL Ubuntu y ejecuta estos comandos:

```bash
# Crear carpeta para el proyecto
mkdir padel-club
cd padel-club

# Crear entorno virtual de Python
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install Flask Flask-SQLAlchemy Werkzeug
```

### Paso 2: Copiar los archivos

Copia todos los archivos que te he generado en esta estructura:

```
padel-club/
├── app.py
├── requirements.txt
└── templates/
    ├── base.html
    ├── login.html
    ├── registro.html
    └── dashboard.html
```

### Paso 3: Ejecutar la app

```bash
# Asegúrate de estar en la carpeta padel-club con el entorno activado
python app.py
```

Verás algo como:
```
 * Running on http://127.0.0.1:5000
```

### Paso 4: Probar en tu navegador

1. Abre tu navegador (Chrome, Firefox, etc.)
2. Ve a: `http://localhost:5000`
3. Verás la página de login
4. Haz clic en "Regístrate aquí"
5. Crea tu primera cuenta
6. Inicia sesión

¡Ya está funcionando! 🎉

## 🔍 Cómo funciona cada archivo

### `app.py` (el cerebro)
- Define las rutas (login, registro, dashboard)
- Gestiona la base de datos
- Maneja las sesiones de usuario
- Por ahora usa SQLite (archivo `padel_club.db` que se crea solo)

### `templates/` (lo que ves)
- `base.html`: Plantilla base con el diseño común
- `login.html`: Página de inicio de sesión
- `registro.html`: Página de registro
- `dashboard.html`: Panel personal del usuario

### `requirements.txt`
- Lista de librerías Python necesarias

## ✅ ¿Qué funciona ahora?

- ✅ Puedes crear usuarios
- ✅ Puedes iniciar sesión
- ✅ Cada usuario ve su nombre en el dashboard
- ✅ Las contraseñas están hasheadas (seguras)
- ✅ Los usuarios no pueden acceder al dashboard sin login

## 🎯 Próximos pasos (cuando quieras)

1. **Añadir contenido general del club** (noticias, eventos)
2. **Página de datos personales** (editar perfil)
3. **Panel de administrador** (tú podrás gestionar usuarios)
4. **Estadísticas de partidos** (meter resultados y ver gráficas)
5. **Migrar a PostgreSQL** (cuando vayas a producción)
6. **Desplegar en Render/Railway** (para tener un enlace público)

## 🆘 Si algo no funciona

**Error: "No module named 'flask'"**
- Solución: Activa el entorno virtual con `source venv/bin/activate`

**Error: "Address already in use"**
- Solución: Cierra la app anterior (Ctrl+C) antes de volver a ejecutar

**No me aparece nada en el navegador**
- Solución: Asegúrate de usar `http://localhost:5000` (con http://)

## 📝 Notas importantes

- La base de datos es un archivo `padel_club.db` que se crea automáticamente
- Si quieres empezar de cero, borra ese archivo
- Por ahora todos los usuarios son normales, luego añadiremos el rol de admin
- El código está comentado para que entiendas cada parte

---

**Siguiente paso**: Cuando esto funcione, me dices y vamos añadiendo la siguiente funcionalidad 🚀
