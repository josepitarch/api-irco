from odoo import http
from odoo.http import Response, request
import json
import logging
from datetime import date
from datetime import timedelta

_logger = logging.getLogger(__name__)

CORS = "*"

class Inventory(http.Controller):
    
    # Endpoint (Obtener todos los ajustes de inventario del almacen) (Modelo: stock.inventory)
    @http.route('/api/adjustments/inventory/<int:almacen>', type='http', auth='user', methods=['GET'])
    def obtener_ajustes_inventario(self, almacen, **kw):
        try:
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', almacen)])

            hoy = date.today()
            ayer = hoy + timedelta(days=-14)
            fecha_formateada = str(ayer) + " 00:00:00"

            ajustesinventario = http.request.env['stock.inventory'].search([('location_id', '=', tipo_almacen[0].lot_stock_id.id), ('date', '>=', fecha_formateada)])
            response = list()
            transformStates = {'draft': 'Borrador', 'confirm': 'En progreso', 'done': 'Validado', 'cancel': 'Cancelado'}

            for ajuste in ajustesinventario[:5]:
                id_inventario = ajuste['id']
                lista_productos = []
                state = transformStates.get(ajuste['state'], 'Sin estado')
                productos_ajustes = http.request.env['stock.inventory.line'].search([('inventory_id', '=', id_inventario)])
                
                for producto in productos_ajustes:
                    reference = ' [' + producto['product_id'].default_code + ']' if producto['product_id'].default_code else ""
                    lot_id =  producto['prod_lot_id'].id if producto['prod_lot_id'].id != False else -1
                    lot_name =  producto['prod_lot_id'].name if producto['prod_lot_id'].name != False else ""
                    
                    quantity_theoretical = producto['theoretical_qty']
                    if float(quantity_theoretical) >= 0:
                        obj = {
                            "id": producto['id'],
                            "product_id": producto['product_id'].id,
                            "product_name": producto['product_id'].name + reference,
                            "lot_id": lot_id,
                            "lot_name": lot_name,
                            "quantity_theoretical": producto['theoretical_qty'],
                            "quantity_real": producto['product_qty'],
                            "unity": producto['product_uom_id'].name
                        }
                        lista_productos.append(obj)
                
                aj = {
                    "id": ajuste['id'],
                    "name": ajuste['name'],
                    "date": str(ajuste['date'].strftime("%d/%m/%Y")),
                    "state": state,
                    "products": lista_productos,
                }

                response.append(aj)
        
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener los ajustes de inventario para el almacén asignado a este usuario',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener todos los ajustes de inventario del almacen) (Modelo: stock.inventory)
    @http.route('/api/one/adjustment/inventory/<int:id>', type='http', auth='user', methods=['GET'])
    def obtener_ajuste_inventario(self, id, **kw):
        try:
            ajustesinventario = http.request.env['stock.inventory'].search([('id', '=', id)])
            response = dict()
            transformStates = {'draft': 'Borrador', 'confirm': 'En progreso', 'done': 'Validado', 'cancel': 'Cancelado'}

            for ajuste in ajustesinventario:
                id_inventario = ajuste['id']
                lista_productos = []
                state = transformStates.get(ajuste['state'], 'Sin estado')
                productos_ajustes = http.request.env['stock.inventory.line'].search([('inventory_id', '=', id_inventario)])
                
                for producto in productos_ajustes:
                    reference = ' [' + producto['product_id'].default_code + ']' if producto['product_id'].default_code else ""
                    lot_id =  producto['prod_lot_id'].id if producto['prod_lot_id'].id != False else -1
                    lot_name =  producto['prod_lot_id'].name if producto['prod_lot_id'].name != False else ""
                    
                    quantity_theoretical = producto['theoretical_qty']
                    if float(quantity_theoretical) >= 0:
                        obj = {
                            "id": producto['id'],
                            "product_id": producto['product_id'].id,
                            "product_name": producto['product_id'].name + reference,
                            "lot_id": lot_id,
                            "lot_name": lot_name,
                            "quantity_theoretical": producto['theoretical_qty'],
                            "quantity_real": producto['product_qty'],
                            "unity": producto['product_uom_id'].name
                        }
                        lista_productos.append(obj)
                
                aj = {
                    "id": ajuste['id'],
                    "name": ajuste['name'],
                    "date": str(ajuste['date'].strftime("%d/%m/%Y")),
                    "state": state,
                    "products": lista_productos,
                }

                response = aj
        
        except Exception as e:
            response = {
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener el ajuste de inventario para el almacén asignado a este usuario',
                    'error': str(e)
                }
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener listado de Mermas cuya ubicacion sea el almacen del usuario) (Modelo: stock.scrap)
    @http.route('/api/all/scraps/<int:store>', type='http', auth='user', methods=['GET'])
    def obtener_mermas(self, store, **kw):
        try:
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', store)])
            al_stock = tipo_almacen[0].lot_stock_id.id
        
            listado_mermas = http.request.env['stock.scrap'].search([('location_id', '=', al_stock)])
            response = list()
            transformStates = {'draft': 'Borrador', 'done': 'Hecho'}

            for merma in listado_mermas:
                state = transformStates.get(merma['state'], 'Sin estado')
                objeto = {
                    "id": merma['id'],
                    "name": merma['name'], 
                    "product_id": merma['product_id'].id,
                    "product_name": merma['product_id'].name,
                    "lot": merma['lot_id'].name,
                    "quantity": merma['scrap_qty'],
                    "location_name": merma['location_id'].name,
                    "location_scrap_name": merma['scrap_location_id'].name,
                    "state": state,
                }

                response.append(objeto)
     
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se han podido obtener las mermas para el almacen',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

     # Endpoint (Crear un nuevo ajuste de inventario) (Modelo: stock.inventory)
    
    @http.route('/api/create/adjustment/inventory', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_ajuste_inventario(self, **post):
        nombre = post.get('name')
        almacen = int(post.get('storeid'))

        try:
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', almacen)])
            alc_stock = tipo_almacen[0].lot_stock_id.id
         
            nuevo_ajuste = http.request.env['stock.inventory'].create({
                "name": nombre,
                "location_id": alc_stock,
                "company_id": 1,
            })

            response = {
                'successful': True,
                'message': 'Se ha creado un nuevo ajuste de inventario satisfactoriamente',
                'error': ''
            }
        
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido crear el ajuste de inventario',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ESTE METODO SOLO FUNCIONA CON EL AJUSTE EN ESTADO "BORRADOR". A PARTIR DE CAMBIAR DE ESTADO, YA SE PODRÁN AÑADIR PRODUCTOS (EXCEPTO SI EL AJUSTE ESTÁ VALIDADO)
    # Endpoint (Inicia un ajuste de inventario) (Modelo: stock.inventory)
    @http.route('/api/iniciate/adjustment/inventory', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def iniciar_ajuste_inventario(self, **post):
        id_ajuste = int(post.get('id'))

        try:
            mi_ajuste = http.request.env['stock.inventory'].search([('id', '=',id_ajuste)])
            mi_ajuste.action_start()
            
            response = {
                'successful': True,
                'message': 'Se ha iniciado el inventario satisfactoriamente',
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido inicializar el inventario',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ESTE METODO SOLO FUNCIONA CON EL AJUSTE EN ESTADO "EN PROGRESO". 
    # Endpoint (Valida un ajuste de inventario) (Modelo: stock.inventory)
    @http.route('/api/validate/adjustment/inventory', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def validar_ajuste_inventario(self, **post): 
        id_ajuste = int(post.get('id'))

        try:
            mi_ajuste = http.request.env['stock.inventory'].search([('id', '=', id_ajuste)])
            mi_ajuste.action_validate()
            response = {
                'successful': True,
                'message': 'Se ha validado el inventario satisfactoriamente',
                'error': ''
            }
         
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido validar el inventario',
                'error': str(e)
            }
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ESTE METODO SOLO FUNCIONA CON EL AJUSTE EN ESTADO "EN PROGRESO". 
    # Endpoint (Cancelar un ajuste de inventario) (Modelo: stock.inventory)
    @http.route('/api/cancel/adjustment/inventory', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def cancelar_ajuste_inventario(self, **post): 
        id_ajuste = int(post.get('id'))

        try:
            mi_ajuste = http.request.env['stock.inventory'].search([('id', '=',id_ajuste)])
            mi_ajuste.action_cancel_draft()
            response = {
                'successful': True,
                'message': 'Se ha cancelado el inventario satisfactoriamente',
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido cancelar el inventario',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ESTE METODO SOLO FUNCIONA CON EL AJUSTE EN ESTADO "EN PROGRESO". 
    # Endpoint (Añadir un producto al ajuste) (Modelo: stock.inventory.line)
    @http.route('/api/add/product/adjustment/inventory', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_producto_de_ajuste(self, **post):
        id_ajuste = int(post.get('id'))
        id_producto = int(post.get('productid'))
        cant_teorica = float(post.get('quantityTheo'))
        cant_real = float(post.get('quantityReal'))
        
        try:
            hoy = str(date.today().strftime("%d/%m/%Y"))
            ajuste_especifico = http.request.env['stock.inventory'].search([('id', '=', id_ajuste)])
            almacen = ajuste_especifico[0].location_id.id
            padre = ajuste_especifico[0].location_id.location_id.name
          
            producto = http.request.env['product.product'].search([('id', '=', id_producto)])
            tipo = producto[0].uom_id.id

            nombre_lote = hoy + '/' + str(padre) + '/99999'

            nuevo_lote = http.request.env['stock.production.lot'].create({
                "name": nombre_lote,
                "product_id": id_producto,
            })

            _logger.info('*********** Lote nuevo creado ***********')

            nuevo_producto_ajuste = http.request.env['stock.inventory.line'].create({
                "inventory_id": id_ajuste,
                "product_id": id_producto, 
                "product_uom_id": tipo,
                "location_id": almacen,
                "prod_lot_id": nuevo_lote[0].id,
                "theoretical_qty": cant_teorica,
                "product_qty": cant_real,
            })

            response = {
                'successful': True,
                'message': 'Se ha creado un nuevo producto para este ajuste',
                'error': ''
            }
     
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido añadir un producto para este ajuste',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type='application/json;charset=utf-8', status = 200)

     # Endpoint (Actualizar un producto del ajuste) (Modelo: stock.inventory.line)
    
    @http.route('/api/update/products/inventory/adjustment', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_producto_de_ajuste(self, **post):
        ids = str(post.get('ids')).split('-')
        quantitys = str(post.get('quantitys')).split('-')

        try:
            for i in range(len(quantitys)):
                producto = http.request.env['stock.inventory.line'].search([('id', '=', int(ids[i]))]).write({
                    "product_qty": float(quantitys[i]),
                })

            response = {'successful': True, 'message': 'Se ha actualizado la cantidad del producto satisfactoriamente', 'error': ''}
            
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido actualizar la cantidad del producto', 'error': str(e)}
            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # ESTE METODO SOLO FUNCIONA CON EL AJUSTE EN ESTADO "EN PROGRESO". 
    # Endpoint (Eliminar un producto de un ajuste de inventario) (Modelo: stock.inventory.line)
    @http.route('/api/delete/product/adjuntment/inventory', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def borrar_producto_de_ajuste_inventario(self, **post): 
        id_linea = int(post.get('id'))

        try:
            producto = http.request.env['stock.inventory.line'].search([('id', '=', id_linea)]).unlink()
            response = {
                'successful': True,
                'message': 'Se ha borrado el producto satisfactoriamente',
                'error': ''
            }
            
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido borrar el producto seleccionado', 
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    
    
    
    
    
    
    # Endpoint (Crear una merma cuyo almacen de desecho sea "CONSUMO PROPIO") (Modelo: stock.scrap)
    @http.route('/api/create/consumes/scrap', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_merma_consumo(self, **post):
        id_producto = int(post.get('productid'))
        cantidad = float(post.get('quantity'))
        lote = int(post.get('lot'))
        almacen = int(post.get('store'))
        
        try:
            producto = http.request.env['product.product'].search([('id', '=', id_producto)])
            tipo = producto[0].uom_id.id
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', almacen)])
            al_stock = tipo_almacen[0].lot_stock_id.id
            ubicacion_padre = http.request.env['stock.location'].search([('id', '=', al_stock)])
            parent_location = ubicacion_padre[0].location_id.id
            ubicacion_desecho = http.request.env['stock.location'].search([('location_id', '=', parent_location), ('usage', '=', 'inventory'), ('scrap_location', '=', True), ('name', '=', 'Consumo propio')])

            if len(ubicacion_desecho) > 0:
                nueva_merma = http.request.env['stock.scrap'].create({
                    "product_id": id_producto,
                    "scrap_qty": cantidad,
                    "product_uom_id": tipo,
                    "lot_id": lote,
                    "location_id": al_stock,
                    "scrap_location_id": ubicacion_desecho[0].id
                })
                response = {
                    'successful': True,
                    'message': 'Se ha creado la merma de consumo correctamente',
                    'error': ''
                }
               
            else: 
                response = {
                    'successful': False,
                    'message': 'No hay una ubicacion de desecho creada para el usuario',
                    'error': ''
                }
            
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido crear la merma',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Crear una merma cuyo almacen de desecho sea "BASURA") (Modelo: stock.scrap)
    @http.route('/api/create/trash/scrap', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_merma_basura(self, **post):
        id_producto = int(post.get('productid'))
        cantidad = float(post.get('quantity'))
        lote = int(post.get('lot'))
        almacen = int(post.get('store'))
        
        try:
            producto = http.request.env['product.product'].search([('id', '=', id_producto)])
            tipo = producto[0].uom_id.id
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', almacen)])
            al_stock = tipo_almacen[0].lot_stock_id.id
            ubicacion_padre = http.request.env['stock.location'].search([('id', '=', al_stock)])
            parent_location = ubicacion_padre[0].location_id.id
        
            ubicacion_desecho = http.request.env['stock.location'].search([('location_id', '=', parent_location), ('usage', '=', 'inventory'), ('scrap_location', '=', True), ('name', '=', 'Basura')])

            if len(ubicacion_desecho) > 0:
                nueva_merma = http.request.env['stock.scrap'].create({
                    "product_id": id_producto,
                    "scrap_qty": cantidad,
                    "product_uom_id": tipo,
                    "lot_id": lote,
                    "location_id": al_stock,
                    "scrap_location_id": ubicacion_desecho[0].id
                })

                response = {
                    'successful': True,
                    'message': 'Se ha creado la merma de basura correctamente',
                    'error': ''
                }
             
            else: 
                response = {
                    'successful': False,
                    'message': 'No hay una ubicacion de desecho creada para el usuario',
                    'error': ''
                }
     
        except Exception as e:
            response = {
                'successful': False,
                'message': 'Ha habido un error en el servidor y no se ha podido crear la merma',
                'error': str(e)
            }

            _logger.error(str(e))
       
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Validar una merma) (Modelo: stock.scrap)
    @http.route('/api/validate/scrap', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def validar_merma(self, **post): 
        id_merma = int(post.get('depletion'))

        try:
            mi_ajuste = http.request.env['stock.scrap'].search([('id', '=', id_merma)])
            mi_ajuste.action_validate()

            response = {
                'successful': True,
                'message': 'Se ha realizado una solicitud de validación correctamente',
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido realizar la solicitud de validación',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200) 