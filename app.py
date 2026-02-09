from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# Configuración de la clave secreta
# En producción, Render nos dará una variable de entorno SECRET_KEY
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-de-desarrollo-local')

# Configuración de base de datos
# Si existe DATABASE_URL (Render), usamos PostgreSQL
# Si no, usamos SQLite para desarrollo local
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render usa postgres://, pero SQLAlchemy necesita postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Desarrollo local con SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///padel_club.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Nuevos campos
    nivel_playtomic = db.Column(db.Float, default=0.0)  # Nivel de Playtomic (ej: 3.5, 4.0, etc.)
    foto_perfil = db.Column(db.String(200), default='default.png')  # URL o nombre de archivo
    puntos_ranking = db.Column(db.Integer, default=0)  # Puntos para el ranking
    categoria = db.Column(db.String(20), default='Bronce')  # Bronce, Plata, Oro
    telefono = db.Column(db.String(20), nullable=True)  # Teléfono opcional
    acepta_terminos = db.Column(db.Boolean, default=False)  # Aceptación RGPD

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def calcular_categoria(self):
        """Calcula la categoría según participaciones (será implementado con el sistema de pozos)"""
        # Por ahora mantiene la categoría actual
        # Luego: Bronce < 5 pozos, Plata 5-15, Oro > 15
        return self.categoria

# Modelo de Pozo
class Pozo(db.Model):
    __tablename__ = 'pozos'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    nivel_min = db.Column(db.Float, nullable=False)  # Float para que coincida con nivel_playtomic
    nivel_max = db.Column(db.Float, nullable=False)
    enlace = db.Column(db.String(500), nullable=False)
    fecha = db.Column(db.DateTime, nullable=True)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Pozo {self.titulo} (Nivel {self.nivel_min}-{self.nivel_max})>'

# Rutas

# Rutas
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(password):
            session['user_id'] = usuario.id
            session['user_name'] = usuario.nombre
            session['is_admin'] = usuario.es_admin
            flash('¡Bienvenido de nuevo!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        nivel_playtomic = request.form.get('nivel_playtomic', 0.0)
        acepta_terminos = request.form.get('acepta_terminos') == 'on'
        
        # Validar aceptación de términos
        if not acepta_terminos:
            flash('Debes aceptar los términos y condiciones', 'error')
            return redirect(url_for('registro'))
        
        # Verificar si el email ya existe
        if Usuario.query.filter_by(email=email).first():
            flash('Este email ya está registrado', 'error')
            return redirect(url_for('registro'))
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre, 
            email=email,
            nivel_playtomic=float(nivel_playtomic) if nivel_playtomic else 0.0,
            acepta_terminos=True
        )
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('¡Registro exitoso! Ya puedes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    return render_template('registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard_new.html')


@app.route('/pozos')
def pozos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['user_id'])
    mi_nivel = usuario.nivel_playtomic
    
    # Solo pozos donde mi nivel está en el rango
    pozos = Pozo.query.filter(
        Pozo.activo == True,
        Pozo.nivel_min <= mi_nivel,
        Pozo.nivel_max >= mi_nivel
    ).order_by(Pozo.fecha).all()
    
    return render_template('pozos.html', pozos=pozos, mi_nivel=mi_nivel)

@app.route('/estadisticas')
def estadisticas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('estadisticas.html')

@app.route('/ranking')
def ranking():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('ranking.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener todos los usuarios
    usuarios = Usuario.query.order_by(Usuario.fecha_registro.desc()).all()
    
    return render_template('admin_new.html', usuarios=usuarios)

@app.route('/admin/toggle_user/<int:user_id>')
def toggle_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(user_id)
    if usuario:
        # Por ahora solo mostramos info, en el futuro podemos añadir activar/desactivar
        flash(f'Usuario: {usuario.nombre} ({usuario.email})', 'success')
    
    return redirect(url_for('admin_panel'))

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()
    
    # MIGRACIÓN AUTOMÁTICA - Añadir nuevas columnas si no existen
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('usuario')]
        
        with db.engine.connect() as conn:
            # Añadir columnas nuevas solo si no existen
            if 'nivel_playtomic' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN nivel_playtomic FLOAT DEFAULT 0.0'))
                conn.commit()
                print("✅ Añadida columna: nivel_playtomic")
            
            if 'foto_perfil' not in columns:
                conn.execute(text("ALTER TABLE usuario ADD COLUMN foto_perfil VARCHAR(200) DEFAULT 'default.png'"))
                conn.commit()
                print("✅ Añadida columna: foto_perfil")
            
            if 'puntos_ranking' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN puntos_ranking INTEGER DEFAULT 0'))
                conn.commit()
                print("✅ Añadida columna: puntos_ranking")
            
            if 'categoria' not in columns:
                conn.execute(text("ALTER TABLE usuario ADD COLUMN categoria VARCHAR(20) DEFAULT 'Bronce'"))
                conn.commit()
                print("✅ Añadida columna: categoria")
            
            if 'telefono' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN telefono VARCHAR(20)'))
                conn.commit()
                print("✅ Añadida columna: telefono")
            
            if 'acepta_terminos' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN acepta_terminos BOOLEAN DEFAULT TRUE'))
                conn.commit()
                print("✅ Añadida columna: acepta_terminos")
            
        print("✅ Migración de Usuario completada")
    except Exception as e:
        print(f"Migración Usuario: {e}")
    
    # Crear tabla pozos si no existe
    try:
        inspector = inspect(db.engine)
        if 'pozos' not in inspector.get_table_names():
            Pozo.__table__.create(db.engine)
            print("✅ Tabla pozos creada")
        else:
            print("✅ Tabla pozos ya existe")
    except Exception as e:
        print(f"Migración Pozos: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
