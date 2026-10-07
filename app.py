from flask import Flask,jsonify,request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
import webbrowser 

app=Flask(__name__) #Crea el objeto app de la clase Flask
CORS(app) #permite acceder desde el front al back

# configuro la base de datos, con el nombre el usuario y la clave
# app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://user:password@localhost/proyecto'
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:Newway42302016@db.zbbjbvrljeojnuhykgra.supabase.co:5432/postgres'
# URI de la BBDD                          driver de la BD  user:clave@URLBBDD/nombreBBDD
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False #none
db= SQLAlchemy(app)   #crea el objeto db de la clase SQLAlquemy
ma=Marshmallow(app)   #crea el objeto ma de de la clase Marshmallow

# ---------fin configuracion-----------

#Definicion y creacion de las tablas
#Base de datos de articulos
class Articulos(db.Model):
    id_articulo=db.Column(db.Integer, primary_key=True)
    rubro=db.Column(db.String(25))
    descripcion=db.Column(db.String(40))
    precio=db.Column(db.Integer)
    stock=db.Column(db.Integer)
    def __init__(self,id_articulo,rubro,descripcion,precio,stock):
        self.id_articulo = id_articulo
        self.rubro = rubro
        self.descripcion = descripcion
        self.precio = precio
        self.stock = stock
#Base de datos de los pedidos de los clientes
class Pedidos(db.Model):
    id_pedido=db.Column(db.Integer, primary_key=True)
    cod_cli=db.Column(db.Integer)
    fecha=db.Column(db.String(19))
    estado=db.Column(db.String(1))
    def __init__(self,cod_cli,fecha,estado):
        self.cod_cli = cod_cli
        self.fecha = fecha
        self.estado = estado
#Base de datos del detalle del pedido de los clientes
class DetPedidos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer)
    cod_art = db.Column(db.Integer)
    rubro=db.Column(db.String(25))
    descripcion = db.Column(db.String(40))
    cantp = db.Column(db.Integer)
    precio = db.Column(db.Integer)
    subtotal = db.Column(db.Integer)    
    def __init__(self,id_pedido,cod_art,rubro,descripcion,cantp,precio,subtotal):
        self.id_pedido = id_pedido
        self.cod_art = cod_art
        self.rubro = rubro
        self.descripcion = descripcion
        self.cantp = cantp
        self.precio = precio
        self.subtotal = subtotal

#Base de datos clientes
class Clientes(db.Model):
    id_cliente = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    passw = db.Column(db.String(256))
    status = db.Column(db.Integer)
    def __init__(self,id_cliente,name,passw,status):
        self.id_cliente = id_cliente
        self.name = name
        self.passw = passw
        self.status = status

with app.app_context():
    db.create_all() #Crea las tablas

class ArticulosSchema(ma.Schema):
    class Meta:
        fields=('id_articulo','rubro','descripcion','precio','stock')
    
articulo_schema=ArticulosSchema()
articulos_schema=ArticulosSchema(many=True)

class PedidosSchema(ma.Schema):
    class Meta:
        fields=('id_pedido','cod_cli','fecha','estado')
    
pedido_schema=PedidosSchema()
pedidos_schema=PedidosSchema(many=True)

class DetPedidosSchema(ma.Schema):
    class Meta:
        fields=('id','id_pedido','cod_art','rubro','descripcion','cantp','precio','subtotal')
    
detpedido_schema=DetPedidosSchema()
detpedidos_schema=DetPedidosSchema(many=True)

class ClientesSchema(ma.Schema):
    class Meta:
        fields=('id_cliente','name','passw','status')
    
cliente_schema=ClientesSchema()
clientes_schema=ClientesSchema(many=True)

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
    all_articulos = Articulos.query.filter(Articulos.descripcion.ilike(f'%{txtsearch}%') | Articulos.rubro.ilike(f'%{txtsearch}%') | Articulos.id_articulo.ilike(f'%{txtsearch}%')).order_by(Articulos.rubro , Articulos.descripcion).all()
    result= articulos_schema.dump(all_articulos) #lo heredamos de ma.schema
                                                #Trae todos los registros de la tabla y los retornamos en un JSON
    return jsonify(result)

# Crea un pedido nuevo
@app.route('/store', methods=['POST']) 
def create_pedido():
    cod_cli=request.json['cod_cli']
    fecha=request.json['fecha']
    estado=request.json['estado']  
    new_pedido=Pedidos(cod_cli,fecha,estado)
    db.session.add(new_pedido)
    db.session.commit()
    new_pedido=pedido_schema.jsonify(new_pedido)
    return  new_pedido

# Agrega un producto al carrito activo
@app.route('/store/pedido/', methods=['POST']) 
def create_carrito():
    id_pedido=request.json['id_pedido']
    cod_art=request.json['cod_art']
    rubro=request.json['rubro']
    descripcion=request.json['descripcion']  
    cantp=request.json['cantp']
    precio=request.json['precio']
    subtotal=request.json['subtotal']
    new_carrito=DetPedidos(id_pedido,cod_art,rubro,descripcion,cantp,precio,subtotal)
    db.session.add(new_carrito)
    db.session.commit()
    new_carrito=detpedido_schema.jsonify(new_carrito)
    return  new_carrito

# Muestra el detalle del pedido
@app.route('/store/detalle/<pedido>', methods=['GET']) 
def detalle_pedido(pedido):
    all_detalle = DetPedidos.query.filter(DetPedidos.id_pedido == pedido).all()
    result= detpedidos_schema.dump(all_detalle) #lo heredamos de ma.schema
                                                #Trae todos los registros de la tabla y los retornamos en un JSON
    return jsonify(result)

# Elimina un producto del carrito
@app.route('/store/<id>',methods=['DELETE'])
def delete_prod(id):
    producto=DetPedidos.query.get(id)
    db.session.delete(producto)
    db.session.commit()
    return detpedidos_schema.jsonify(producto)   # me devuelve un json con el registro eliminado

# Muestra todos los pedidos (STATUS)
@app.route('/store/status/<cliente>', methods=['GET']) 
def detalle_status(cliente):
    all_detalle = Pedidos.query.filter(Pedidos.cod_cli == cliente, Pedidos.estado != "E").all()
    result= pedidos_schema.dump(all_detalle) #lo heredamos de ma.schema  and 
                                                #Trae todos los registros de la tabla y los retornamos en un JSON
    return jsonify(result)

# Eliminar pedido (No lo borro, le cambio el estado a E eliminado)
@app.route('/store/pedido/<id>' ,methods=['PUT'])
def delete_pedido(id):
    user=Pedidos.query.get(id)
    user.estado="E"
    db.session.commit()
    return pedidos_schema.jsonify(user)

# Modificar cantidad detalle articulo
@app.route('/store/modifica/<id>' ,methods=['PUT'])
def modifica_detpedido(id):
    detalle=DetPedidos.query.get(id)
    detalle.cantp=request.json['cantp']
    detalle.precio=request.json['precio']
    detalle.subtotal=request.json['subtotal']
    db.session.commit()
    return detpedido_schema.jsonify(detalle)

# Cerrar pedido
@app.route('/store/cerrar/<id>' ,methods=['PUT'])
def close_pedido(id):
    user=Pedidos.query.get(id)
    user.estado="C"
    db.session.commit()
    return pedidos_schema.jsonify(user)

#Login
@app.route('/login/<cliente>/<ps>',methods=['GET'])
def autorizar(cliente,ps):
    # Chequeo si el password y el usuario son correctos y si tiene menos de 5 intentos
    cli = Clientes.query.filter(Clientes.id_cliente == cliente , Clientes.passw == ps, Clientes.status < 5).all()
    result= clientes_schema.dump(cli)
    #Si no coinciden el usuario y el password
    if result==[]:
        # Chequeo si el usuario existe y si tiene menos de 5 intentos
        cli = Clientes.query.filter(Clientes.id_cliente == cliente, Clientes.status < 5).all()
        result= clientes_schema.dump(cli)
        # Si no existe o si intento + de 5 no pasa, debe reintentar
        if result==[]:
            print("Usuario bloqueado o inexistente")
            noautorizado=Clientes('','','Usuario bloqueado o inexistente',0)
            noautorizado=cliente_schema.jsonify(noautorizado)
            return  noautorizado
        # Si existe tiene 5 intentos
        else:
            cli=Clientes.query.get(cliente)
            cli.status=cli.status+1
            numint= 5 - cli.status
            est="Clave incorrecta. " + str(numint) + " intentos restantes"
            print(est)
            db.session.commit()
            noautorizado=Clientes('','',est,0)
            noautorizado=cliente_schema.jsonify(noautorizado)
            return  noautorizado
    else:
        print("Acceso autorizado")
        # Si usuario y clave son correctos reseteo el status
        cli=Clientes.query.get(cliente)
        cli.status=0
        db.session.commit()
        # fields=('id_cliente','name','passw','status')
        autorizado=Clientes(cliente,cli.name,'','http://127.0.0.1:5500/store.html')
        autorizado=cliente_schema.jsonify(autorizado)
        return  autorizado 

#Programa Principal
if __name__ == '__main__':
    app.run(debug=True, port=5000)

