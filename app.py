from functools import wraps
from datetime import datetime, timedelta
import hashlib
import jwt 
from flask import Flask, jsonify, request, session, make_response
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import ForeignKey
from marshmallow import fields


# creamos la aplicacion
app = Flask(__name__)

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://usuario:contrasenia@host/nombreDB'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://BD2021:BD2021itec@143.198.156.171/blog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "acapongoloquequiero"

db = SQLAlchemy(app)

# Creamos una instancia Miigrate que recibe la app y db
migrate = Migrate(app, db)
ma = Marshmallow(app)




#MODELADO DE LA BASE

class Usuario(db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False, unique=True)
    estado = db.Column(db.Boolean(), nullable=False)
    fecha_creacion = db.Column(db.DateTime(), nullable=False)

    # para no pasar el id inicializamos las otras columnas
    def __init__(self, nombre, apellido, username, email, password, estado, fecha_creacion):
        self.nombre = nombre
        self.apellido = apellido
        self.username = username
        self.email = email
        self.password = password
        self.estado = estado
        self.fecha_creacion = fecha_creacion 


class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    contenido_breve = db.Column(db.String(511), nullable=False)
    contenido = db.Column(db.String(50), nullable=False)
    fecha_creacion = db.Column(db.DateTime(), nullable=False)
    estado = db.Column(db.Boolean(True), nullable=False)
    usuario_id = db.Column(db.Integer(), ForeignKey("usuario.id"))
    categoria_id = db.Column(db.Integer, ForeignKey("categoria.id"))
    

    usuario = db.relationship("Usuario")
    categoria = db.relationship("Categoria")


class Categoria(db.Model):
    __tablename__ = 'categoria'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)


class Rol(db.Model):
    __tablename__ = 'rol'

    id = db.Column(db.Integer, primary_key=True)
    rol_nombre = db.Column(db.String(255), nullable=False, unique=True)


class Usuario_rol(db.Model):
    __tablename__ = 'usuario_rol'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer(), ForeignKey("usuario.id"))
    rol_id = db.Column(db.Integer, ForeignKey("rol.id"))

    usuario = db.relationship("Usuario")
    rol = db.relationship("Rol")



# ---------- SCHEMAS ------------

class UsuarioSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nombre = fields.String()
    apellido = fields.String()
    username = fields.String()
    email = fields.String()
    # nunca mostrar la contraseña
    # password = fields.String()
    estado = fields.Boolean()
    fecha_creacion = fields.DateTime()


class PostSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    titulo = fields.String()
    contenido_breve = fields.String()
    contenido = fields.String()
    fecha_creacion = fields.DateTime()
    estado = fields.Boolean()
    usuario_id = fields.Integer()
    categoria_id = fields.Integer()


class CategoriaSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    nombre = fields.String()


class RolSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    rol_nombre = fields.String()


class UsuarioRolSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    usuario_id = fields.Integer()
    rol_id = fields.Integer()



# ------- TOKEN ------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({"ERROR":"Token is missing"}),401

        try: 
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            # userLogged = Usuario.query.filter_by(id=data['nombre']).first()
        except:
            return jsonify({"ERROR": "Token is invalid or expired"}), 401

        return f(data, *args, **kwargs)

    return decorated



# ---------- RUTAS -------------

@app.route('/usuarios')
@token_required
def get_usuario(data):
    usuario = db.session.query(Usuario).all()
    if len(usuario) == 0:
         return jsonify(dict(Mensaje = "No existen Usuarios")), 400
    usuario_schema = UsuarioSchema().dump(usuario, many=True)
    return jsonify(dict(Usuarios = usuario_schema)), 200


@app.route('/usuarios', methods=['POST'])
def add_usuario():
    if request.method == 'POST':
        data = request.json
        print('ENTRA AL PPOST')
        nombre = data['nombre']
        apellido = data['apellido']
        username = data['username']
        email = data['email']
        password = data['password'].encode('utf-8')
        estado = data['estado']
        # fecha_creacion = dato['fecha_creacion']

        contra_hash = hashlib.md5(password).hexdigest()

        try:
            nuevo_usuario = Usuario(
                nombre=nombre, 
                apellido=apellido,
                username=username,
                email=email,
                password=contra_hash, 
                estado=estado,
                fecha_creacion=datetime.now()
                
            )
            db.session.add(nuevo_usuario)
            db.session.commit()

            resultado = UsuarioSchema().dump(nuevo_usuario)

            if resultado:
                return jsonify(dict(NuevoUsuario=resultado))

        except:
            return jsonify(dict(Error = 'No es posible generar el usuario')), 201

        
@app.route('/usuarios/<id>', methods=['PUT'])
def update_usuario(id):
    if request.method == 'PUT':
        data = request.json
        nombre = data['nombre']
        apellido = data['apellido']
        username = data['username']
        email = data['email']
       
        usuario = db.session.query(Usuario).filter_by(id=id).first()
        usuario.nombre = nombre
        usuario.apellido = apellido
        usuario.username = username
        usuario.email = email
        db.session.commit()

        return '¡¡¡ Usuarioo actualizado correctamenteeee !!!'
    

@app.route('/usuarios/<id>', methods=['DELETE'])
def delete_usuario(id):
    if request.method == 'DELETE':
        try:
            usuario = db.session.query(Usuario).filter_by(id=id).first()
            db.session.delete(usuario)
            db.session.commit()

            return jsonify({"Usuario eliminado": usuario.nombre})
        
        except:
            return "No se puede eliminar el Usuario porque esta relacionado a un post"


@app.route('/post')
def get_post():
    post = db.session.query(Post).all()
    post_schema = PostSchema().dump(post, many=True )
    return jsonify(post_schema)


@app.route('/post', methods=['POST'])
def add_post():
     if request.method == 'POST':
        data = request.json
        titulo = data['titulo']
        contenido_breve = data['contenido_breve']
        contenido = data['contenido']
        #  fecha_creacion = data['fecha_creacion']
        estado = data['estado']
        usuario_id = data['usuario_id']
        categoria_id = data['categoria_id']

        try:
            nuevo_post = Post(
                titulo=titulo, 
                contenido_breve=contenido_breve,
                contenido=contenido,
                fecha_creacion=datetime.now(),
                estado=estado,
                usuario_id=usuario_id,
                categoria_id=categoria_id
                
            )
            db.session.add(nuevo_post)
            db.session.commit()

            resultado = PostSchema().dump(nuevo_post)

            if resultado:
                return jsonify(dict(NuevoPost=resultado))

        except:
            return jsonify(dict(Error = 'No es posible generar el post')), 201

        
@app.route('/post/<id>', methods=['PUT'])
def update_post(id):
    if request.method == 'PUT':
        data = request.json
        titulo = data['titulo']
        contenido_breve = data['contenido_breve']
        contenido = data['contenido']
        usuario_id = data['usuario_id']
        categoria_id = data['categoria_id']
       
        post = db.session.query(Post).filter_by(id=id).first()
        post.titulo = titulo
        post.contenido_breve = contenido_breve
        post.contenido = contenido
        post.usuario_id = usuario_id
        post.categoria_id = categoria_id
        db.session.commit()

        return 'Post actualizado correctamenteeee!!!'
    

@app.route('/post/<id>', methods=['DELETE'])
def delete_post(id):
    if request.method == 'DELETE':
        post = db.session.query(Post).filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({"Post Eliminado": post.titulo})


@app.route('/categoria')
def get_categoria():
    categoria = db.session.query(Categoria).all()
    categoria_schema = CategoriaSchema().dump(categoria, many=True)
    return jsonify(categoria_schema)


@app.route('/categoria', methods=['POST'])
def add_categoria():
     if request.method == 'POST':
        data = request.json
        nombre = data['nombre']
       
        nueva_categoria = Categoria(nombre=nombre)
        db.session.add(nueva_categoria)
        db.session.commit()

        resultado = CategoriaSchema().dump(nueva_categoria)
        return jsonify(dict(NuevoCategoria=resultado))


@app.route('/categoria/<id>', methods=['PUT'])
def update_categoria(id):
    if request.method == 'PUT':
        data = request.json
        nombre = data['nombre']
       
        categoria = db.session.query(Categoria).filter_by(id=id).first()
        categoria.nombre = nombre
        db.session.commit()

        return 'Categoria actualizada correctamente!!!'

     
@app.route('/categoria/<id>', methods=['DELETE'])
def delete_persona(id):
            if request.method == 'DELETE':
                categoria = db.session.query(Categoria).filter_by(id=id).first()
                # print(categoria.id)
                db.session.delete(categoria)
                db.session.commit()

                return jsonify({"Categoria Eliminada": categoria.nombre})


@app.route('/roles')
def get_rol():
    rol = db.session.query(Rol).all()
    rol_schema = RolSchema().dump(rol, many=True)
    return jsonify(rol_schema)


@app.route('/roles', methods=['POST'])
def add_rol():
    if request.method == 'POST':
        data = request.json
        rol_nombre = data['rol_nombre']

        nuevo_rol = Rol(rol_nombre=rol_nombre)
        db.session.add(nuevo_rol)
        db.session.commit()

        resultado = RolSchema().dump(nuevo_rol)
        return jsonify(dict(NuevoRol=resultado))


@app.route('/roles/<id>', methods=['PUT'])
def update_rol(id):
    if request.method == 'PUT':
        data = request.json
        nombre = data['rol_nombre']
       
        rol = db.session.query(Rol).filter_by(id=id).first()
        rol.rol_nombre = nombre
        db.session.commit()

        return 'Rol actualizado correctamente!!!'

@app.route('/roles/<id>', methods=['DELETE'])
def delete_rol(id):
    if request.method == 'DELETE':
            rol = db.session.query(Rol).filter_by(id=id).first()
            db.session.delete(rol)
            db.session.commit()

            return jsonify({"Rol Eliminado": rol.rol_nombre})

@app.route('/login')
def login():
    auth = request.authorization

    username = auth['username']
    # password = auth['password'].encode('utf-8')

    if not auth or not auth.username:
        return make_response("Could not verify",401, {"WWW-Authnticate":"Basic realm='Login required!'"})

    # hasheada = hashlib.md5(password).hexdigest()

    user = db.session.query(Usuario).filter_by(username=username).first()
    nombre = str(user.nombre)
    
    if not username:
        return make_response("Could not verify",401, {"WWW-Authnticate":"Basic realm='Login required!'"})

    if nombre:
        token = jwt.encode({"nombre": nombre},app.secret_key)
        return jsonify({"token": token})
    
    return jsonify({"Could not verify"}, 401, {"WWW-Authnticate":"Basic realm='Login required!'"})


# @app.route('/provincias')
# @token_required
# def get_provincias(userLogged):
#     if userLogged.idTipousuario == 2:
#         provincia = db.session.query(Provincia).all()
#         provincia_schema = ProvinciaSerializer().dump(provincia, many=True)
#         return jsonify(provincia_schema)
#     else:
#         return jsonify({"Error":"Usted no tiene permiso!!"})





if __name__ == '__main__':
    app.run(debug=True)
