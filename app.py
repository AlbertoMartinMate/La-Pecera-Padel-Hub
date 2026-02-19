from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-de-desarrollo-local')

database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///padel_club.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)


# ── MODELOS ──────────────────────────────────────────────────────────────────

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    nivel_playtomic = db.Column(db.Float, default=0.0)
    foto_perfil = db.Column(db.String(200), default='default.png')
    puntos_ranking = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(20), default='Bronce')
    telefono = db.Column(db.String(20), nullable=True)
    acepta_terminos = db.Column(db.Boolean, default=False)
    posicion_juego = db.Column(db.String(20), nullable=True)
    disponibilidad_semana = db.Column(db.String(20), nullable=True)
    disponibilidad_horaria = db.Column(db.String(50), nullable=True)
    acepta_notificaciones = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def calcular_categoria(self):
        return self.categoria


class Pozo(db.Model):
    __tablename__ = 'pozos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    nivel_min = db.Column(db.Float, nullable=False)
    nivel_max = db.Column(db.Float, nullable=False)
    enlace = db.Column(db.String(500), nullable=False)
    fecha = db.Column(db.DateTime, nullable=True)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Pozo {self.titulo} (Nivel {self.nivel_min}-{self.nivel_max})>'


class PozoJugado(db.Model):
    __tablename__ = 'pozos_jugados'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    nivel = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resultados = db.relationship('Resultado', backref='pozo_jugado', lazy=True)

    def __repr__(self):
        return f'<PozoJugado {self.titulo}>'


class Resultado(db.Model):
    __tablename__ = 'resultados'

    id = db.Column(db.Integer, primary_key=True)
    pozo_jugado_id = db.Column(db.Integer, db.ForeignKey('pozos_jugados.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    posicion = db.Column(db.Integer, nullable=True)
    puntos = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Resultado {self.email} - Pos {self.posicion}>'


class HistorialNivel(db.Model):
    __tablename__ = 'historial_nivel'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nivel_anterior = db.Column(db.Float, nullable=False)
    nivel_nuevo = db.Column(db.Float, nullable=False)
    pozo_jugado_id = db.Column(db.Integer, db.ForeignKey('pozos_jugados.id'), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<HistorialNivel {self.usuario_id}: {self.nivel_anterior} -> {self.nivel_nuevo}>'


class HistorialRanking(db.Model):
    __tablename__ = 'historial_ranking'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    posicion = db.Column(db.Integer, nullable=False)
    puntos = db.Column(db.Integer, nullable=False)
    pozo_jugado_id = db.Column(db.Integer, db.ForeignKey('pozos_jugados.id'), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<HistorialRanking {self.usuario_id}: pos {self.posicion}>'


# ── RUTAS ────────────────────────────────────────────────────────────────────

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

        if not acepta_terminos:
            flash('Debes aceptar los términos y condiciones', 'error')
            return redirect(url_for('registro'))

        if Usuario.query.filter_by(email=email).first():
            flash('Este email ya está registrado', 'error')
            return redirect(url_for('registro'))

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

    proximos_pozos = Pozo.query.filter(
        Pozo.activo == True,
        Pozo.nivel_min <= mi_nivel,
        Pozo.nivel_max >= mi_nivel
    ).order_by(Pozo.fecha).limit(3).all()

    usuarios_ranking = Usuario.query.order_by(Usuario.puntos_ranking.desc()).all()
    mi_posicion = None
    for i, u in enumerate(usuarios_ranking):
        if u.id == usuario.id:
            mi_posicion = i + 1
            break

    top_ranking = usuarios_ranking[:5]

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

    pozos = Pozo.query.filter(
        Pozo.activo == True,
        Pozo.nivel_min <= mi_nivel,
        Pozo.nivel_max >= mi_nivel
    ).order_by(Pozo.fecha).all()

    # Historial de pozos jugados del usuario
    historial_raw = db.session.query(Resultado, PozoJugado)\
        .join(PozoJugado, Resultado.pozo_jugado_id == PozoJugado.id)\
        .filter(Resultado.email == usuario.email)\
        .order_by(PozoJugado.fecha.desc()).all()

    # Construir lista con puntos acumulados y variación de nivel
    pozos_jugados = []
    puntos_acum = usuario.puntos_ranking  # empezamos desde el total actual y restamos hacia atrás
    for resultado, pozo in historial_raw:
        puntos_acum_display = puntos_acum
        # Buscar variación de nivel en historial_nivel para este pozo
        hist_nivel = HistorialNivel.query.filter_by(
            usuario_id=usuario.id,
            pozo_jugado_id=pozo.id
        ).first()

        variacion = round(hist_nivel.nivel_nuevo - hist_nivel.nivel_anterior, 2) if hist_nivel else 0
        nivel_nuevo = hist_nivel.nivel_nuevo if hist_nivel else usuario.nivel_playtomic

        pozos_jugados.append({
            'titulo': pozo.titulo,
            'fecha': pozo.fecha.strftime('%d/%m/%Y') if pozo.fecha else '-',
            'posicion': resultado.posicion,
            'puntos': resultado.puntos,
            'puntos_acumulados': puntos_acum_display,
            'variacion_nivel': variacion,
            'nivel_nuevo': nivel_nuevo
        })
        puntos_acum -= resultado.puntos  # restamos para reconstruir hacia atrás

    return render_template('pozos.html', pozos=pozos, mi_nivel=mi_nivel, pozos_jugados=pozos_jugados)


@app.route('/estadisticas')
def estadisticas():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['user_id'])

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
        'participaciones': participaciones,
        'puntos_totales': usuario.puntos_ranking,
        'nivel_actual': usuario.nivel_playtomic,
        'pct_primeros': round((primeros / total_pozos * 100), 1) if total_pozos > 0 else 0,
        'pct_segundos': round((segundos / total_pozos * 100), 1) if total_pozos > 0 else 0,
        'pct_terceros': round((terceros / total_pozos * 100), 1) if total_pozos > 0 else 0,
        'pct_participaciones': round((participaciones / total_pozos * 100), 1) if total_pozos > 0 else 0,
    }

    # Media total de puntos por pozo
    puntos_todos = [r.puntos for r in resultados]
    media_total_puntos = round(sum(puntos_todos) / len(puntos_todos), 1) if puntos_todos else 0

    # Historial de nivel (orden cronológico)
    historial = HistorialNivel.query.filter_by(usuario_id=usuario.id)\
        .order_by(HistorialNivel.fecha.asc()).limit(20).all()

    # Últimos 10 pozos con resultado
    ultimos_pozos = db.session.query(Resultado, PozoJugado)\
        .join(PozoJugado, Resultado.pozo_jugado_id == PozoJugado.id)\
        .filter(Resultado.email == usuario.email)\
        .order_by(PozoJugado.fecha.asc())\
        .limit(10).all()

    # Historial de posición en ranking
    historial_ranking = HistorialRanking.query.filter_by(usuario_id=usuario.id)\
        .order_by(HistorialRanking.fecha.asc()).limit(20).all()

    return render_template('estadisticas.html',
                           stats=stats,
                           usuario=usuario,
                           historial=historial,
                           ultimos_pozos=ultimos_pozos,
                           historial_ranking=historial_ranking,
                           media_total_puntos=media_total_puntos)


@app.route('/ranking')
def ranking():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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

        lineas = csv_contenido.strip().split('\n')
        parejas = []
        niveles_totales = []

        for linea in lineas[1:]:
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

        media_pozo = sum(niveles_totales) / len(niveles_totales) if niveles_totales else 0

        fecha = datetime.strptime(fecha_pozo, '%Y-%m-%d') if fecha_pozo else datetime.utcnow()
        pozo_jugado = PozoJugado(
            titulo=titulo_pozo,
            fecha=fecha,
            nivel=media_pozo
        )
        db.session.add(pozo_jugado)
        db.session.commit()

        for pareja in parejas:
            diferencia = pareja['media_pareja'] - media_pozo
            posicion = pareja['posicion']

            if diferencia < -0.3:
                variaciones = {1: 0.10, 2: 0.08, 3: 0.06, None: 0}
            elif diferencia > 0.3:
                variaciones = {1: 0.04, 2: 0.02, 3: 0.01, None: -0.02}
            else:
                variaciones = {1: 0.06, 2: 0.04, 3: 0.02, None: -0.01}

            variacion = variaciones.get(posicion, 0)
            puntos = {1: 10, 2: 6, 3: 4, None: 2}.get(posicion, 2)

            for email, nivel in [(pareja['email1'], pareja['nivel1']), (pareja['email2'], pareja['nivel2'])]:
                resultado = Resultado(
                    pozo_jugado_id=pozo_jugado.id,
                    email=email,
                    posicion=posicion,
                    puntos=puntos
                )
                db.session.add(resultado)

                usuario = Usuario.query.filter_by(email=email).first()
                if usuario:
                    nivel_anterior = usuario.nivel_playtomic
                    usuario.puntos_ranking += puntos
                    usuario.nivel_playtomic = round(usuario.nivel_playtomic + variacion, 2)
                    usuario.nivel_playtomic = max(0, min(7, usuario.nivel_playtomic))

                    # Guardar historial de nivel si hubo cambio
                    if variacion != 0:
                        historial_nivel = HistorialNivel(
                            usuario_id=usuario.id,
                            nivel_anterior=nivel_anterior,
                            nivel_nuevo=usuario.nivel_playtomic,
                            pozo_jugado_id=pozo_jugado.id
                        )
                        db.session.add(historial_nivel)

        # Guardar historial de ranking para todos los participantes
        # (lo hacemos después de actualizar todos los puntos)
        db.session.commit()

        todos_usuarios = Usuario.query.order_by(Usuario.puntos_ranking.desc()).all()
        emails_participantes = set()
        for pareja in parejas:
            emails_participantes.add(pareja['email1'])
            emails_participantes.add(pareja['email2'])

        for email in emails_participantes:
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario:
                posicion_ranking = next(
                    (i + 1 for i, u in enumerate(todos_usuarios) if u.id == usuario.id),
                    None
                )
                if posicion_ranking:
                    historial_rank = HistorialRanking(
                        usuario_id=usuario.id,
                        posicion=posicion_ranking,
                        puntos=usuario.puntos_ranking,
                        pozo_jugado_id=pozo_jugado.id
                    )
                    db.session.add(historial_rank)

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

@app.route('/admin/editar_pozo_jugado/<int:pozo_id>', methods=['GET', 'POST'])
def editar_pozo_jugado(pozo_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))

    pozo = PozoJugado.query.get_or_404(pozo_id)
    resultados = Resultado.query.filter_by(pozo_jugado_id=pozo_id).all()

    if request.method == 'POST':
        pozo.titulo = request.form.get('titulo')
        fecha_str = request.form.get('fecha')
        if fecha_str:
            pozo.fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        nivel_str = request.form.get('nivel')
        pozo.nivel = float(nivel_str) if nivel_str else pozo.nivel
        db.session.commit()
        flash(f'Pozo "{pozo.titulo}" actualizado correctamente', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('editar_pozo_jugado.html', pozo=pozo, resultados=resultados)


@app.route('/admin/borrar_pozo_jugado/<int:pozo_id>')
def borrar_pozo_jugado(pozo_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('No tienes permisos de administrador', 'error')
        return redirect(url_for('login'))

    pozo = PozoJugado.query.get_or_404(pozo_id)
    resultados = Resultado.query.filter_by(pozo_jugado_id=pozo_id).all()

    for resultado in resultados:
        usuario = Usuario.query.filter_by(email=resultado.email).first()
        if usuario:
            usuario.puntos_ranking = max(0, usuario.puntos_ranking - resultado.puntos)
            hist_nivel = HistorialNivel.query.filter_by(
                usuario_id=usuario.id,
                pozo_jugado_id=pozo_id
            ).first()
            if hist_nivel:
                usuario.nivel_playtomic = round(hist_nivel.nivel_anterior, 2)
                db.session.delete(hist_nivel)
            hist_rank = HistorialRanking.query.filter_by(
                usuario_id=usuario.id,
                pozo_jugado_id=pozo_id
            ).first()
            if hist_rank:
                db.session.delete(hist_rank)
        db.session.delete(resultado)

    titulo = pozo.titulo
    db.session.delete(pozo)
    db.session.commit()

    flash(f'Pozo "{titulo}" eliminado y puntos/nivel revertidos correctamente', 'success')
    return redirect(url_for('admin_panel'))

@app.context_processor
def inject_usuario_actual():
    if 'user_id' in session:
        usuario = Usuario.query.get(session['user_id'])
        return {'usuario_actual': usuario}
    return {'usuario_actual': None}


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['user_id'])

    if request.method == 'POST':
        usuario.nombre = request.form.get('nombre', usuario.nombre)
        usuario.telefono = request.form.get('telefono', usuario.telefono)
        usuario.posicion_juego = request.form.get('posicion_juego')
        usuario.disponibilidad_semana = request.form.get('disponibilidad_semana')
        horaria = request.form.getlist('disponibilidad_horaria')
        usuario.disponibilidad_horaria = ','.join(horaria) if horaria else None
        usuario.acepta_notificaciones = 'acepta_notificaciones' in request.form

        foto = request.files.get('foto')
        if foto and foto.filename:
            try:
                resultado = cloudinary.uploader.upload(
                    foto,
                    folder='lapecera/perfiles',
                    transformation=[{'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'}]
                )
                usuario.foto_perfil = resultado['secure_url']
            except Exception as e:
                flash(f'Error al subir la foto: {str(e)}', 'error')

        session['user_name'] = usuario.nombre
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('perfil'))

    return render_template('perfil.html', usuario=usuario)

@app.route('/cambiar_password', methods=['POST'])
def cambiar_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['user_id'])
    password_actual = request.form.get('password_actual')
    password_nueva = request.form.get('password_nueva')
    password_confirmar = request.form.get('password_confirmar')

    if not usuario.check_password(password_actual):
        flash('La contraseña actual no es correcta', 'error')
        return redirect(url_for('perfil'))

    if password_nueva != password_confirmar:
        flash('Las contraseñas nuevas no coinciden', 'error')
        return redirect(url_for('perfil'))

    if len(password_nueva) < 6:
        flash('La contraseña debe tener al menos 6 caracteres', 'error')
        return redirect(url_for('perfil'))

    usuario.set_password(password_nueva)
    db.session.commit()
    flash('Contraseña cambiada correctamente', 'success')
    return redirect(url_for('perfil'))

# ── INICIALIZACIÓN Y MIGRACIONES ─────────────────────────────────────────────

with app.app_context():
    db.create_all()

    from sqlalchemy import text, inspect
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('usuario')]

        with db.engine.connect() as conn:
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

            if 'posicion_juego' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN posicion_juego VARCHAR(20)'))
                conn.commit()
            if 'disponibilidad_semana' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN disponibilidad_semana VARCHAR(20)'))
                conn.commit()
            if 'disponibilidad_horaria' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN disponibilidad_horaria VARCHAR(50)'))
                conn.commit()
            if 'acepta_notificaciones' not in columns:
                conn.execute(text('ALTER TABLE usuario ADD COLUMN acepta_notificaciones BOOLEAN DEFAULT FALSE'))
                conn.commit()

        print("✅ Migración de Usuario completada")
    except Exception as e:
        print(f"Migración Usuario: {e}")

    try:
        inspector = inspect(db.engine)
        tablas = inspector.get_table_names()

        if 'pozos' not in tablas:
            Pozo.__table__.create(db.engine)
            print("✅ Tabla pozos creada")
        else:
            print("✅ Tabla pozos ya existe")

        if 'pozos_jugados' not in tablas:
            PozoJugado.__table__.create(db.engine)
            print("✅ Tabla pozos_jugados creada")
        else:
            print("✅ Tabla pozos_jugados ya existe")

        if 'resultados' not in tablas:
            Resultado.__table__.create(db.engine)
            print("✅ Tabla resultados creada")
        else:
            print("✅ Tabla resultados ya existe")

        if 'historial_nivel' not in tablas:
            HistorialNivel.__table__.create(db.engine)
            print("✅ Tabla historial_nivel creada")
        else:
            print("✅ Tabla historial_nivel ya existe")

        if 'historial_ranking' not in tablas:
            HistorialRanking.__table__.create(db.engine)
            print("✅ Tabla historial_ranking creada")
        else:
            print("✅ Tabla historial_ranking ya existe")

    except Exception as e:
        print(f"Migración tablas: {e}")


if __name__ == '__main__':
    app.run(debug=True, port=5001)
