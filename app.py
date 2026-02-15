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

# Modelo de Pozo Jugado (historial permanente)
class PozoJugado(db.Model):
    __tablename__ = 'pozos_jugados'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    nivel = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con resultados
    resultados = db.relationship('Resultado', backref='pozo_jugado', lazy=True)
    
    def __repr__(self):
        return f'<PozoJugado {self.titulo}>'

# Modelo de Resultado (participaciones)
class Resultado(db.Model):
    __tablename__ = 'resultados'
    
    id = db.Column(db.Integer, primary_key=True)
    pozo_jugado_id = db.Column(db.Integer, db.ForeignKey('pozos_jugados.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    posicion = db.Column(db.Integer, nullable=True)  # 1, 2, 3 para top 3, NULL para resto
    puntos = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Resultado {self.email} - Pos {self.posicion}>'

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
    
    usuario = Usuario.query.get(session['user_id'])
    mi_nivel = usuario.nivel_playtomic
    
    # Próximos 3 pozos de mi nivel
    proximos_pozos = Pozo.query.filter(
        Pozo.activo == True,
        Pozo.nivel_min <= mi_nivel,
        Pozo.nivel_max >= mi_nivel
    ).order_by(Pozo.fecha).limit(3).all()
    
    # Mi posición en el ranking
    usuarios_ranking = Usuario.query.order_by(Usuario.puntos_ranking.desc()).all()
    mi_posicion = None
    for i, u in enumerate(usuarios_ranking):
        if u.id == usuario.id:
            mi_posicion = i + 1
            break
    
    # Top 5 ranking
    top_ranking = usuarios_ranking[:5]
    
    # Estadísticas del usuario
    resultados = Resultado.query.filter_by(email=usuario.email).all()
    total_pozos = len(resultados)
    primeros = sum(1 for r in resultados if r.posicion == 1)
    segundos = sum(1 for r in resultados if r.posicion == 2)
    terceros = sum(1 for r in resultados if r.posicion == 3)
    participaciones = sum(1 for r in resultados if r.posicion is None)
    
    stats = {
        'total_pozos': total_pozos,
        'primeros': primeros,
        'segundos': segundos,
        'terceros': terceros,
        'participaciones': participaciones
    }
    
    return render_template('dashboard_new.html', 
                           proximos_pozos=proximos_pozos, 
                           usuario=usuario,
                           mi_posicion=mi_posicion,
                           top_ranking=top_ranking,
                           stats=stats)


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
    
    usuario = Usuario.query.get(session['user_id'])
    
    # Buscar resultados del usuario
    resultados = Resultado.query.filter_by(email=usuario.email).all()
    
    # Contar posiciones
    total_pozos = len(resultados)
    primeros = sum(1 for r in resultados if r.posicion == 1)
    segundos = sum(1 for r in resultados if r.posicion == 2)
    terceros = sum(1 for r in resultados if r.posicion == 3)
    participaciones = sum(1 for r in resultados if r.posicion is None)
    
    # Calcular porcentajes
    stats = {
        'total_pozos': total_pozos,
        'primeros': primeros,
        'segundos': segundos,
        'terceros': terceros,
        'participaciones': participaciones,
        'puntos_totales': usuario.puntos_ranking,
        'nivel_actual': usuario.nivel_playtomic,
        'pct_primeros': round((primeros / total_pozos * 100), 1) if total_pozos > 0 else 0,
        'pct_segundos': round((segundos / total_pozos * 100), 1) if total_pozos > 0 else 0,
        'pct_terceros': round((terceros / total_pozos * 100), 1) if total_pozos > 0 else 0,
        'pct_participaciones': round((participaciones / total_pozos * 100), 1) if total_pozos > 0 else 0,
    }
    
    return render_template('estadisticas.html', stats=stats, usuario=usuario)

@app.route('/ranking')
def ranking():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Ordenar usuarios por puntos (mayor a menor)
    usuarios = Usuario.query.order_by(Usuario.puntos_ranking.desc()).all()
    
    return render_template('ranking.html', usuarios=usuarios)

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
    
    usuarios = Usuario.query.order_by(Usuario.fecha_registro.desc()).all()
    pozos = Pozo.query.filter_by(activo=True).order_by(Pozo.fecha).all()
    pozos_jugados = PozoJugado.query.order_by(PozoJugado.fecha.desc()).all()
    
    return render_template('admin_new.html', usuarios=usuarios, pozos=pozos, pozos_jugados=pozos_jugados)

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

@app.route('/admin/actualizar_nivel/<int:user_id>', methods=['POST'])
def actualizar_nivel(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(user_id)
    if usuario:
        nuevo_nivel = request.form.get('nivel', 0)
        usuario.nivel_playtomic = float(nuevo_nivel)
        db.session.commit()
        flash(f'Nivel de {usuario.nombre} actualizado a {nuevo_nivel}', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/crear_pozo', methods=['GET', 'POST'])
def crear_pozo():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        nivel_min = float(request.form.get('nivel_min', 0))
        nivel_max = float(request.form.get('nivel_max', 7))
        enlace = request.form.get('enlace')
        fecha_str = request.form.get('fecha')
        
        # Convertir fecha
        fecha = None
        if fecha_str:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
        
        nuevo_pozo = Pozo(
            titulo=titulo,
            nivel_min=nivel_min,
            nivel_max=nivel_max,
            enlace=enlace,
            fecha=fecha,
            activo=True
        )
        
        db.session.add(nuevo_pozo)
        db.session.commit()
        
        flash(f'Pozo "{titulo}" creado correctamente', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('crear_pozo.html')

@app.route('/admin/editar_pozo/<int:pozo_id>', methods=['GET', 'POST'])
def editar_pozo(pozo_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))
    
    pozo = Pozo.query.get_or_404(pozo_id)
    
    if request.method == 'POST':
        pozo.titulo = request.form.get('titulo')
        pozo.nivel_min = float(request.form.get('nivel_min', 0))
        pozo.nivel_max = float(request.form.get('nivel_max', 7))
        pozo.enlace = request.form.get('enlace')
        fecha_str = request.form.get('fecha')
        
        if fecha_str:
            pozo.fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
        
        db.session.commit()
        flash(f'Pozo "{pozo.titulo}" actualizado', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('editar_pozo.html', pozo=pozo)

@app.route('/admin/borrar_pozo/<int:pozo_id>')
def borrar_pozo(pozo_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))
    
    pozo = Pozo.query.get_or_404(pozo_id)
    titulo = pozo.titulo
    db.session.delete(pozo)
    db.session.commit()
    
    flash(f'Pozo "{titulo}" eliminado', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/subir_resultados', methods=['GET', 'POST'])
def subir_resultados():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo_pozo = request.form.get('titulo_pozo')
        fecha_pozo = request.form.get('fecha_pozo')
        csv_contenido = request.form.get('csv_contenido')
        
        if not csv_contenido:
            flash('Debes pegar el contenido del CSV', 'error')
            return redirect(url_for('subir_resultados'))
        
        # Parsear CSV
        lineas = csv_contenido.strip().split('\n')
        parejas = []
        niveles_totales = []
        
        for linea in lineas[1:]:  # Saltar cabecera
            if not linea.strip():
                continue
            partes = linea.split(',')
            if len(partes) >= 4:
                email1 = partes[0].strip().lower()
                nivel1 = float(partes[1].strip()) if partes[1].strip() else 0
                email2 = partes[2].strip().lower()
                nivel2 = float(partes[3].strip()) if partes[3].strip() else 0
                posicion = int(partes[4].strip()) if len(partes) > 4 and partes[4].strip() else None
                
                media_pareja = (nivel1 + nivel2) / 2
                niveles_totales.extend([nivel1, nivel2])
                
                parejas.append({
                    'email1': email1,
                    'nivel1': nivel1,
                    'email2': email2,
                    'nivel2': nivel2,
                    'media_pareja': media_pareja,
                    'posicion': posicion
                })
        
        # Calcular media del pozo
        media_pozo = sum(niveles_totales) / len(niveles_totales) if niveles_totales else 0
        
        # Crear pozo jugado
        fecha = datetime.strptime(fecha_pozo, '%Y-%m-%d') if fecha_pozo else datetime.utcnow()
        pozo_jugado = PozoJugado(
            titulo=titulo_pozo,
            fecha=fecha,
            nivel=media_pozo
        )
        db.session.add(pozo_jugado)
        db.session.commit()
        
        # Procesar cada pareja
        for pareja in parejas:
            diferencia = pareja['media_pareja'] - media_pozo
            posicion = pareja['posicion']
            
            # Calcular variación según la fórmula
            if diferencia < -0.3:  # Por debajo de la media
                variaciones = {1: 0.10, 2: 0.08, 3: 0.06, None: 0}
            elif diferencia > 0.3:  # Por encima de la media
                variaciones = {1: 0.04, 2: 0.02, 3: 0.01, None: -0.02}
            else:  # En la media
                variaciones = {1: 0.06, 2: 0.04, 3: 0.02, None: -0.01}
            
            variacion = variaciones.get(posicion, 0)
            puntos = {1: 10, 2: 6, 3: 4, None: 2}.get(posicion, 2)
            
            # Guardar resultado y actualizar usuarios
            for email, nivel in [(pareja['email1'], pareja['nivel1']), (pareja['email2'], pareja['nivel2'])]:
                resultado = Resultado(
                    pozo_jugado_id=pozo_jugado.id,
                    email=email,
                    posicion=posicion,
                    puntos=puntos
                )
                db.session.add(resultado)
                
                # Actualizar usuario si existe
                usuario = Usuario.query.filter_by(email=email).first()
                if usuario:
                    usuario.puntos_ranking += puntos
                    usuario.nivel_playtomic = round(usuario.nivel_playtomic + variacion, 2)
                    # Limitar nivel entre 0 y 7
                    usuario.nivel_playtomic = max(0, min(7, usuario.nivel_playtomic))
        
        db.session.commit()
        
        flash(f'Resultados del pozo "{titulo_pozo}" guardados. Media del pozo: {media_pozo:.2f}', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('subir_resultados.html')


@app.route('/admin/ver_resultados/<int:pozo_id>')
def ver_resultados(pozo_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))
    
    pozo = PozoJugado.query.get_or_404(pozo_id)
    resultados = Resultado.query.filter_by(pozo_jugado_id=pozo_id).order_by(Resultado.posicion).all()
    
    return render_template('ver_resultados.html', pozo=pozo, resultados=resultados)


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
    
        # Crear tabla pozos_jugados si no existe
    try:
        if 'pozos_jugados' not in inspector.get_table_names():
            PozoJugado.__table__.create(db.engine)
            print("✅ Tabla pozos_jugados creada")
        else:
            print("✅ Tabla pozos_jugados ya existe")
    except Exception as e:
        print(f"Migración PozosJugados: {e}")
    
    # Crear tabla resultados si no existe
    try:
        if 'resultados' not in inspector.get_table_names():
            Resultado.__table__.create(db.engine)
            print("✅ Tabla resultados creada")
        else:
            print("✅ Tabla resultados ya existe")
    except Exception as e:
        print(f"Migración Resultados: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
