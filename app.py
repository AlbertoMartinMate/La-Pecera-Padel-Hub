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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
        
        # Verificar si el email ya existe
        if Usuario.query.filter_by(email=email).first():
            flash('Este email ya está registrado', 'error')
            return redirect(url_for('registro'))
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(nombre=nombre, email=email)
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
    
    return render_template('dashboard.html', nombre=session.get('user_name'))

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
    
    return render_template('admin.html', usuarios=usuarios)

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

if __name__ == '__main__':
    app.run(debug=True)