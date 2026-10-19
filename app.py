from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
import webbrowser 
from marshmallow import fields
import pytz

app = Flask(__name__) # Crea el objeto app de la clase Flask
CORS(app) # Permite acceder desde el front al back
# Le damos permiso explícito a DonWeb con y sin WWW para conectarse a Supabase y Render
CORS(app, origins=[
    "https://new-way.com.ar",
    "https://www.new-way.com.ar"
])
# Configuración de la base de datos apuntando a Supabase
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg://postgres.zbbjbvrljeojnuhykgra:Newway42302016@aws-0-us-east-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app)   # Crea el objeto db de la clase SQLAlchemy
ma = Marshmallow(app)   # Crea el objeto ma de la clase Marshmallow

# --------- Fin configuración -----------

# Definición de las tablas de la Base de Datos

# Base de datos de artículos
class Articulos(db.Model):
    id_articulo = db.Column(db.Integer, primary_key=True)
    rubro = db.Column(db.String(25))
    descripcion = db.Column(db.String(40))
    precio = db.Column(db.Integer)
    stock = db.Column(db.Integer)
    def __init__(self, id_articulo, rubro, descripcion, precio, stock):
        self.id_articulo = id_articulo
        self.rubro = rubro
        self.descripcion = descripcion
        self.precio = precio
        self.stock = stock

# Base de datos de los pedidos de los clientes
class Pedidos(db.Model):
    id_pedido = db.Column(db.Integer, primary_key=True)
    cod_cli = db.Column(db.Integer)
    fecha = db.Column(db.String(19))
    estado = db.Column(db.String(1))
    def __init__(self, cod_cli, fecha, estado):
        self.cod_cli = cod_cli
        self.fecha = fecha
        self.estado = estado

# Base de datos del detalle del pedido de los clientes
class DetPedidos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer)
    cod_art = db.Column(db.Integer)
    rubro = db.Column(db.String(25))
    descripcion = db.Column(db.String(40))
    cantp = db.Column(db.Integer)
    precio = db.Column(db.Integer)
    subtotal = db.Column(db.Integer)    
    def __init__(self, id_pedido, cod_art, rubro, descripcion, cantp, precio, subtotal):
        self.id_pedido = id_pedido
        self.cod_art = cod_art
        self.rubro = rubro
        self.descripcion = descripcion
        self.cantp = cantp
        self.precio = precio
        self.subtotal = subtotal

# Base de datos clientes (DESCOMENTADA Y ACTIVA)
class Clientes(db.Model):
    id_cliente = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    passw = db.Column(db.String(256))
    status = db.Column(db.Integer)
    def __init__(self, id_cliente, name, passw, status):
        self.id_cliente = id_cliente
        self.name = name
        self.passw = passw
        self.status = status

with app.app_context():
    db.create_all() # Crea las tablas en Supabase si no existen

# Definición de Esquemas de serialización (Marshmallow)

# Esquema Manual para Clientes (Evita errores de tipos con la URL del catálogo)
class ClientesSchema(ma.Schema):
    id_cliente = fields.Integer()
    name = fields.String()
    passw = fields.String()
    status = fields.String()  # Recibe la URL de producción como texto plano sin chistar

cliente_schema = ClientesSchema()
clientes_schema = ClientesSchema(many=True)

# Esquemas automáticos para el resto de las tablas
class ArticulosSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Articulos
        load_instance = True
        sqla_session = db.session
    
articulo_schema = ArticulosSchema()
articulos_schema = ArticulosSchema(many=True)

class PedidosSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Pedidos
        load_instance = True
        sqla_session = db.session
    
pedido_schema = PedidosSchema()
pedidos_schema = PedidosSchema(many=True)

class DetPedidosSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DetPedidos
        load_instance = True
        sqla_session = db.session
    
detpedido_schema = DetPedidosSchema()
detpedidos_schema = DetPedidosSchema(many=True)

#--------------------------------------------------------------------------------------#
#                                    Endpoints
#--------------------------------------------------------------------------------------#

#Trae todos los articulos
@app.route('/store',methods=['GET'])
def get_Articulos():
    all_articulos = Articulos.query.all() #heredamos del db.model
    result= articulos_schema.dump(all_articulos) #lo heredamos de ma.schema
                                                #Trae todos los registros de la tabla y los retornamos en un JSON
    return jsonify(result)

#Realiza la busqueda inteligente
@app.route('/store/<txtsearch>',methods=['GET'])
def get_articulo(txtsearch):
    txtsearch_format = f'%{txtsearch}%'
    
    all_articulos = Articulos.query.filter(
        Articulos.descripcion.ilike(txtsearch_format) | 
        Articulos.rubro.ilike(txtsearch_format) | 
        Articulos.id_articulo.cast(db.String).ilike(txtsearch_format)
    ).order_by(Articulos.rubro, Articulos.descripcion).all()
    
    # CORRECCIÓN DE INDENTACIÓN: Aseguramos que tengan exactamente 4 espacios desde el inicio
    result = articulos_schema.dump(all_articulos)
    return jsonify(result)

# Crea un pedido nuevo
@app.route('/store', methods=['POST']) 
def create_pedido():
    cod_cli = request.json['cod_cli']
    fecha_completa = request.json['fecha'] # Recibe '2026-10-15T13:33:51.680Z'
    estado = request.json['estado']  
    
    # Esto transformará el valor en '2026-10-15T13:33:51', midiendo exactamente 19 caracteres
    fecha_recortada = fecha_completa[:19]
    
    # Creamos el registro con la fecha adaptada al tamaño de la columna
    new_pedido = Pedidos(cod_cli, fecha_recortada, estado)
    
    db.session.add(new_pedido)
    db.session.commit()
    
    return pedido_schema.jsonify(new_pedido)

# 1. Agrega un producto al carrito activo
@app.route('/store/pedido/', methods=['POST']) 
def create_carrito():
    # Conversión preventiva a enteros para asegurar compatibilidad con Supabase
    id_pedido = int(request.json['id_pedido'])
    cod_art = int(request.json['cod_art'])
    rubro = request.json['rubro']
    descripcion = request.json['descripcion']  
    cantp = int(request.json['cantp'])
    precio = int(request.json['precio'])
    subtotal = int(request.json['subtotal'])
    
    new_carrito = DetPedidos(id_pedido, cod_art, rubro, descripcion, cantp, precio, subtotal)
    db.session.add(new_carrito)
    db.session.commit()
    return detpedido_schema.jsonify(new_carrito)

# 2. Muestra el detalle del pedido (CORREGIDO: Fuerza <int:pedido>)
@app.route('/store/detalle/<int:pedido>', methods=['GET']) 
def detalle_pedido(pedido):
    all_detalle = DetPedidos.query.filter(DetPedidos.id_pedido == pedido).all()
    result = detpedidos_schema.dump(all_detalle)
    return jsonify(result)

# 3. Elimina un producto del carrito (CORREGIDO: <int:id> y db.session.get)
@app.route('/store/<int:id>', methods=['DELETE'])
def delete_prod(id):
    producto = db.session.get(DetPedidos, id)
    if not producto:
        return jsonify({"error": "Producto no encontrado en el carrito"}), 404
        
    db.session.delete(producto)
    db.session.commit()
    # Cambiado a detpedido_schema (singular) porque borras UN solo registro, no una lista
    return detpedido_schema.jsonify(producto)

# 4. Muestra todos los pedidos STATUS (CORREGIDO: Fuerza <int:cliente>)
@app.route('/store/status/<int:cliente>', methods=['GET']) 
def detalle_status(cliente):
    all_detalle = Pedidos.query.filter(Pedidos.cod_cli == cliente, Pedidos.estado != "E").all()
    result = pedidos_schema.dump(all_detalle)
    return jsonify(result)

# 5. Eliminar pedido de forma lógica (CORREGIDO: <int:id> y db.session.get)
@app.route('/store/pedido/<int:id>', methods=['PUT'])
def delete_pedido(id):
    user = db.session.get(Pedidos, id)
    if not user:
        return jsonify({"error": "Pedido no encontrado"}), 404
        
    user.estado = "E"
    db.session.commit()
    return pedido_schema.jsonify(user)

# 6. Modificar cantidad detalle artículo (CORREGIDO: <int:id> y db.session.get)
@app.route('/store/modifica/<int:id>', methods=['PUT'])
def modifica_detpedido(id):
    detalle = db.session.get(DetPedidos, id)
    if not detalle:
        return jsonify({"error": "Detalle no encontrado"}), 404
        
    detalle.cantp = int(request.json['cantp'])
    detalle.precio = int(request.json['precio'])
    detalle.subtotal = int(request.json['subtotal'])
    db.session.commit()
    return detpedido_schema.jsonify(detalle)

# 7. Cerrar pedido y empaquetar datos para el TXT (Campos dinámicos e independientes)
@app.route('/store/cerrar/<int:id>', methods=['PUT'])
def close_pedido(id):
    # Buscamos el pedido en Supabase
    pedido = db.session.get(Pedidos, id)
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404
        
    # Cambiamos el estado a 'C' (Cerrado) y guardamos en Supabase
    pedido.estado = "C"
    db.session.commit()
    
    # Buscamos todos los artículos relacionados con este pedido en el carrito
    all_detalle = DetPedidos.query.filter(DetPedidos.id_pedido == id).all()
    
    # Obtenemos la fecha y hora de cierre real de Argentina
    zona_horaria = pytz.timezone('America/Argentina/Buenos_Aires')
    ahora = datetime.now(zona_horaria)
    
    # CONDICIÓN 1: El NOMBRE del archivo exige 5 dígitos fijos obligatorios con ceros
    codigo_cliente_5_digitos = f"{pedido.cod_cli:05d}"
    nombre_archivo = f"{ahora.strftime('%Y%m%d%H%M%S')}{codigo_cliente_5_digitos}1.txt"
    
    # CONDICIÓN 2: El CONTENIDO del archivo usa el ID natural separado por punto y coma (;)
    # Si el cliente es el 38, aquí pondrá directamente "38" sin ceros adicionales
    lineas_txt = []
    for art in all_detalle:
        # Formato exacto: 38;20608;3;0;0;;F
        linea = f"{pedido.cod_cli};{art.cod_art};{art.cantp};0;0;viaWEB;F"
        lineas_txt.append(linea)
    
    # Unimos todas las líneas con saltos de línea para armar el cuerpo del archivo
    contenido_txt = "\n".join(lineas_txt)
    
    # Retornamos el JSON para tu JavaScript en DonWeb
    return jsonify({
        "status": "success",
        "mensaje": "Pedido cerrado en Supabase correctamente",
        "nombre_archivo": nombre_archivo,
        "contenido_txt": contenido_txt
    })

#Login
@app.route('/login/<cliente>/<ps>', methods=['GET'])
def autorizar(cliente, ps):
    # 1. CONVERSIÓN CRUCIAL PARA POSTGRESQL (De string a entero)
    try:
        cliente_int = int(cliente)
    except ValueError:
        noautorizado = Clientes(0, '', 'ID de cliente inválido', 0)
        return cliente_schema.jsonify(noautorizado), 400

    # Chequeo si el password y el usuario son correctos y si tiene menos de 5 intentos
    cli = Clientes.query.filter(Clientes.id_cliente == cliente_int, Clientes.passw == ps, Clientes.status < 5).all()
    result = clientes_schema.dump(cli)
    
    # Si no coinciden el usuario y el password
    if result == []:
        # Chequeo si el usuario existe y si tiene menos de 5 intentos
        cli = Clientes.query.filter(Clientes.id_cliente == cliente_int, Clientes.status < 5).all()
        result = clientes_schema.dump(cli)
        
        # Si no existe o si intentó + de 5 no pasa, debe reintentar
        if result == []:
            print("Usuario bloqueado o inexistente")
            noautorizado = Clientes(0, '', 'Usuario bloqueado o inexistente', 0)
            return cliente_schema.jsonify(noautorizado)
        
        # Si existe, incrementamos el contador de intentos
        else:
            # 2. CORRECCIÓN DE MÉTODO (session.get en lugar de query.get)
            cli = db.session.get(Clientes, cliente_int)
            cli.status = cli.status + 1
            numint = 5 - cli.status
            est = "Clave incorrecta. " + str(numint) + " intentos restantes"
            print(est)
            db.session.commit()
            
            noautorizado = Clientes(0, '', est, 0)
            return cliente_schema.jsonify(noautorizado)
            
    else:
        print("Acceso autorizado")
        # Si usuario y clave son correctos reseteo el status
        cli = db.session.get(Clientes, cliente_int)
        cli.status = 0
        db.session.commit()
        
        # Si te llamaron desde ://new-way.com.ar, devolverá esa URL. Si fue sin www, devolverá esa.
        origen_frontend = request.headers.get('Origin')
        
        # En caso de que por alguna razón extrema no capte el origen, dejamos tu dominio por defecto
        if not origen_frontend:
            origen_frontend = 'https://new-way.com.ar'
            
        # Armamos la ruta final respetando exactamente las pestañas del navegador del usuario
        url_store = f"{origen_frontend}/store.html"
        
        # Creamos el objeto genérico para Marshmallow (el truco que ya teníamos)
        class ObjetoLogin:
            pass

        autorizado = ObjetoLogin()
        autorizado.id_cliente = cliente_int
        autorizado.name = cli.name
        autorizado.passw = 'Acceso Autorizado'
        autorizado.status = url_store # <-- Aquí viaja la URL dinámica perfecta
        
        return cliente_schema.jsonify(autorizado)

#Programa Principal
if __name__ == '__main__':
    app.run(debug=True, port=5000)

