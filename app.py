
from getpass import getpass

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from urllib.parse import quote_plus
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave-local-desarrollo")


# CONFIGURACION DE MONGODB

basedatos = "ITMg1"

# Usuarios registrados en MongoDB
usuarios = ["Bryan", "Angel", "Ruben", "Luis"] 

# Usuario seleccionado
usuario = os.environ.get("Bryan") or input("Usuario: ")
password = os.environ.get("MONGO_PASSWORD")  or getpass(
    "Contraseña: "
)
if usuario not in usuarios:
    raise ValueError("El usuario no esta registrado en la lista")

if not password:
    raise ValueError("Debes configurar MONGO_PASSWORD")

# URL de conexion
uri = (
    f"mongodb://{quote_plus(usuario)}:"
    f"{quote_plus(password)}@localhost:27017/"
    f"{basedatos}?authSource={basedatos}"
)

client = MongoClient(uri, serverSelectionTimeoutMS=5000)

# Verificar conexion
client.admin.command("ping")

db = client[basedatos]

# Colecciones
col_alumnos = db["alumnos"]
col_materias = db["materias"]


# PAGINA PRINCIPAL

@app.route('/')
def index():
    alumnos = list(col_alumnos.find())
    return render_template('index.html', alumnos=alumnos)


# CONSULTAR Y BUSCAR ALUMNOS

@app.route('/alumnos', methods=['GET', 'POST'])
def alumnos():

    ncontrol = (
        request.values.get('Ncontrol')
        or request.values.get('ncontrol')
        or ''
    ).strip()

    if ncontrol:
        lista_alumnos = list(
            col_alumnos.find({"ncontrol": ncontrol})
        )
    else:
        lista_alumnos = list(col_alumnos.find())

    return render_template(
        'alumnos.html',
        alumnos=lista_alumnos
    )


# AGREGAR ALUMNO

@app.route('/agregar_alumno', methods=['POST'])
def agregar_alumno():

    try:
        ncontrol = request.form.get('ncontrol', '').strip()
        nombre = request.form.get('nombre', '').strip()
        paterno = request.form.get('paterno', '').strip()
        materno = request.form.get('materno', '').strip()
        carrera = request.form.get('carrera', '').strip()
        sexo = request.form.get('sexo', '').strip()

        edad = int(request.form.get('edad', '0'))

        calificaciones = [
            int(valor.strip())
            for valor in request.form.get(
                'calificaciones', ''
            ).split(',')
            if valor.strip()
        ]

        if not all([ncontrol, nombre, paterno, materno, carrera, sexo]):
            flash("Completa todos los campos obligatorios.")
            return redirect(url_for('alumnos'))

        if not 0 <= edad <= 120:
            flash("La edad no es valida.")
            return redirect(url_for('alumnos'))

        if any(cal < 0 or cal > 100 for cal in calificaciones):
            flash("Las calificaciones deben estar entre 0 y 100.")
            return redirect(url_for('alumnos'))

        if col_alumnos.find_one({"ncontrol": ncontrol}):
            flash("El numero de control ya existe.")
            return redirect(url_for('alumnos'))

        nuevo_alumno = {
            "ncontrol": ncontrol,
            "nombre": nombre,
            "paterno": paterno,
            "materno": materno,
            "carrera": carrera,
            "sexo": sexo,
            "edad": edad,
            "calificaciones": calificaciones
        }

        col_alumnos.insert_one(nuevo_alumno)

        flash("Alumno agregado correctamente.")

    except (ValueError, TypeError):
        flash("Verifica la edad y las calificaciones.")
    except DuplicateKeyError:
        flash("El alumno ya esta registrado.")

    return redirect(url_for('alumnos'))


# MODIFICAR ALUMNO

@app.route('/editar_alumno/<id>', methods=['POST'])
def editar_alumno(id):

    if not ObjectId.is_valid(id):
        flash("Identificador invalido.")
        return redirect(url_for('alumnos'))

    alumno_id = ObjectId(id)

    if not col_alumnos.find_one({"_id": alumno_id}):
        flash("El alumno no existe.")
        return redirect(url_for('alumnos'))

    try:
        datos = {}

        campos = [
            "ncontrol",
            "nombre",
            "paterno",
            "materno",
            "carrera",
            "sexo"
        ]

        for campo in campos:
            if campo in request.form:
                datos[campo] = request.form[campo].strip()

        if any(not valor for valor in datos.values()):
            flash("Los campos no pueden estar vacios.")
            return redirect(url_for('alumnos'))

        if 'edad' in request.form:
            edad = int(request.form['edad'])

            if not 0 <= edad <= 120:
                raise ValueError("Edad invalida")

            datos['edad'] = edad

        if 'calificaciones' in request.form:
            calificaciones = [
                int(valor.strip())
                for valor in request.form[
                    'calificaciones'
                ].split(',')
                if valor.strip()
            ]

            if any(cal < 0 or cal > 100 for cal in calificaciones):
                raise ValueError("Calificacion invalida")

            datos['calificaciones'] = calificaciones

        if 'ncontrol' in datos:
            existente = col_alumnos.find_one({
                "ncontrol": datos['ncontrol'],
                "_id": {"$ne": alumno_id}
            })

            if existente:
                flash("Ese numero de control ya existe.")
                return redirect(url_for('alumnos'))

        if datos:
            col_alumnos.update_one(
                {"_id": alumno_id},
                {"$set": datos}
            )

            flash("Alumno actualizado correctamente.")

    except (ValueError, TypeError):
        flash("Verifica los datos ingresados.")
    except DuplicateKeyError:
        flash("Numero de control duplicado.")

    return redirect(url_for('alumnos'))


# ELIMINAR ALUMNO

@app.route('/eliminar_alumno', methods=['POST'])
def eliminar_alumno():

    id = request.form.get('id', '')

    if not ObjectId.is_valid(id):
        flash("Identificador invalido.")
        return redirect(url_for('alumnos'))

    resultado = col_alumnos.delete_one({
        "_id": ObjectId(id)
    })

    if resultado.deleted_count > 0:
        flash("Alumno eliminado correctamente.")
    else:
        flash("Alumno no encontrado.")

    return redirect(url_for('alumnos'))


# CONSULTAR Y BUSCAR MATERIAS

@app.route('/materias', methods=['GET', 'POST'])
def materias():

    id_materia = request.values.get('id_materia', '').strip()

    if id_materia:
        lista_materias = list(
            col_materias.find({"id_materia": id_materia})
        )
    else:
        lista_materias = list(col_materias.find())

    return render_template(
        'materias.html',
        materias=lista_materias
    )


# AGREGAR MATERIA

@app.route('/agregar_materia', methods=['POST'])
def agregar_materia():

    try:
        id_materia = request.form.get('id_materia', '').strip()
        nombre = request.form.get('nombre', '').strip()
        carrera = request.form.get('carrera', '').strip()
        semestre = int(request.form.get('semestre', '0'))

        if not id_materia or not nombre or not carrera:
            flash("Completa todos los campos.")
            return redirect(url_for('materias'))

        if semestre < 1 or semestre > 12:
            flash("El semestre debe estar entre 1 y 12.")
            return redirect(url_for('materias'))

        if col_materias.find_one({"id_materia": id_materia}):
            flash("La clave de materia ya existe.")
            return redirect(url_for('materias'))

        nueva_materia = {
            "id_materia": id_materia,
            "nombre": nombre,
            "carrera": carrera,
            "semestre": semestre
        }

        col_materias.insert_one(nueva_materia)

        flash("Materia agregada correctamente.")

    except (ValueError, TypeError):
        flash("Verifica los datos ingresados.")
    except DuplicateKeyError:
        flash("La materia ya existe.")

    return redirect(url_for('materias'))


# MODIFICAR MATERIA

@app.route('/editar_materia/<id>', methods=['POST'])
def editar_materia(id):

    if not ObjectId.is_valid(id):
        flash("Identificador de materia inválido.")
        return redirect(url_for('materias'))

    materia_id = ObjectId(id)

    if not col_materias.find_one({"_id": materia_id}):
        flash("La materia no existe.")
        return redirect(url_for('materias'))

    try:
        id_materia = request.form.get('id_materia', '').strip()
        nombre = request.form.get('nombre', '').strip()
        carrera = request.form.get('carrera', '').strip()
        semestre = int(request.form.get('semestre', '0'))

        if not id_materia or not nombre or not carrera:
            flash("Completa todos los campos.")
            return redirect(url_for('materias'))

        if semestre < 1 or semestre > 12:
            flash("El semestre debe estar entre 1 y 12.")
            return redirect(url_for('materias'))

        existente = col_materias.find_one({
            "id_materia": id_materia,
            "_id": {"$ne": materia_id}
        })

        if existente:
            flash("La clave de materia ya está registrada.")
            return redirect(url_for('materias'))

        datos_actualizados = {
            "id_materia": id_materia,
            "nombre": nombre,
            "carrera": carrera,
            "semestre": semestre
        }

        col_materias.update_one(
            {"_id": materia_id},
            {"$set": datos_actualizados}
        )

        flash("Materia actualizada correctamente.")

    except (ValueError, TypeError):
        flash("Verifica los datos ingresados.")
    except DuplicateKeyError:
        flash("La clave de materia ya existe.")

    return redirect(url_for('materias'))


# ELIMINAR MATERIA

@app.route('/eliminar_materia', methods=['POST'])
def eliminar_materia():

    id = request.form.get('id', '')

    if not ObjectId.is_valid(id):
        flash("Identificador inválido.")
        return redirect(url_for('materias'))

    resultado = col_materias.delete_one({
        "_id": ObjectId(id)
    })

    if resultado.deleted_count > 0:
        flash("Materia eliminada correctamente.")
    else:
        flash("No se encontró la materia.")

    return redirect(url_for('materias'))


# MOSTRAR IMAGEN

@app.route('/imagen')
def imagen():

    return send_from_directory(
        app.static_folder,
        'img/logo_tec_mina.jpg',
        mimetype='image/jpeg'
    )


# EJECUTAR SERVIDOR

if __name__ == '__main__':
    app.run(debug=True, port=5001)
