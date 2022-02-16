# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response, request
import json
import logging
import datetime
from datetime import date
from datetime import timedelta
from datetime import datetime
import sys
sys.path.insert(0, '/opt/odoo/custom-addons/odoo_controller/utils')
import utils

import calendar
_logger = logging.getLogger(__name__)

CORS = "*"

class OdooController(http.Controller):

    # ENDPOINT 1 (Filtra por usuario)(Ordenes de producción de hoy)(Modelo: irco.clientes.production)(Modelo: mrp.production)
    @http.route(route='/api/op/<int:userid>/<int:selector>', auth='user', methods=['GET'], type='http')
    def opbyselector(self, userid, selector, **kw):
        correct_call = True
    
        today = date.today()
        name_day = calendar.day_name[today.weekday()]
        if selector == 0:
            date_ini, date_end = str(today) + ' 00:00:00', str(today) + ' 23:59:59'
        elif selector == 1:
            date_ini, date_end = utils.interval_of_dates(name_day, today)
        elif selector == 2:
            hoy = today + timedelta(days = 7)
            date_ini, date_end = utils.interval_of_dates(name_day, hoy)
        elif selector == 3:
            hoy = today + timedelta(days=14)
            date_ini, date_end = utils.interval_op_future(name_day, hoy)
        elif selector == 4:
            date_end = str(today) + ' 00:00:00'
        else:
            correct_call = False
            response = [{
                "successful": False,
                "message": "Campo selector no válido",
                "error": "Fallo en la llamada al endpoint /api/op/<int:userid>/<int:selector>"
            }]
            
        if correct_call:
            datosalmacenes = http.request.env['res.users'].search([('id', '=', userid)]).almacenes
            if(len(datosalmacenes) == 0):
                response = [{
                    "successful": False,
                    "message": "Este usuario no tiene un almacén asignado",
                    "error": "Este usuario no tiene un almacén asignado"
                }]

            for almacen in datosalmacenes:
                stock = http.request.env['stock.warehouse'].search([('id', '=', almacen.id)])
            
                response = list()
                transformStates = {'draft': 'Borrador', 'confirmed': 'Confirmado', 'planned': 'Planificado', 'progress': 'En proceso', 'done': 'Hecho', 'cancel': 'Cancelado'}

                if selector != 4:
                    production_orders = http.request.env['mrp.production'].search([('location_src_id', '=', stock[0].lot_stock_id.id), ('date_planned_start', '>=', date_ini), ('date_planned_start', '<=', date_end)], order = "state desc, date_planned_start desc")
                else:
                    production_orders = http.request.env['mrp.production'].search([('location_src_id', '=', stock[0].lot_stock_id.id), ('date_planned_start', '<=', date_end), ('state', '!=', 'done'), ('state', '!=', 'cancel')], order="state desc, date_planned_start desc")
                
                for production_order in production_orders:
                    try:
                        date_op = str(production_order['date_planned_start'].strftime("%d/%m/%Y"))
                        past = datetime.strptime(date_op, "%d/%m/%Y")
                        present = datetime.now()
                        
                        if past.date() >= present.date() or selector == 4:
                            state = transformStates.get(production_order['state'], 'No State')
                            raw_materials = list()

                            if state is not "Borrador":
                                lista_materiales = http.request.env['stock.move'].search([('raw_material_production_id', '=', production_order['id'])])
                                
                            else:
                                lista_materiales = list()

                            for raw_material in lista_materiales:
                                lot = http.request.env['stock.move.line'].search([('move_id', '=', raw_material['id'])])
            
                                if len(lot) > 0:
                                    done = raw_material['quantity_done'] if state is not 'Borrador' else 0.0
                                    reserved = raw_material['reserved_availability'] if state is not 'Borrador' else 0.0
                                    lot_line = lot[0].id if state is not 'Borrador' else -1
                                    lot_id = lot[0].lot_id.id if state is not 'Borrador' else -1
                                    lot_name = lot[0].lot_id.name if state is not 'Borrador' else ""
                                else:
                                    reserved = 0; done = 0; lot_line = -1; lot_id = -1; lot_name = ""
                                
                                quantity = raw_material['product_uom_qty'] if state is not 'Borrador' else raw_material['product_qty']
                                
                                if lot_id == False or lot_name == False:
                                    lot_id = -1
                                    lot_name = ""
                                    
                                current_rm = {
                                    "id": raw_material['id'],
                                    "product_id": raw_material['product_id'].id,
                                    "name": raw_material['product_id'].name,
                                    "quantity": quantity,
                                    "unity": raw_material['product_uom'].name,
                                    "reserved": reserved,
                                    "done": done,
                                    "lot_line": lot_line,
                                    "lot_id": lot_id,
                                    "lot_name": lot_name
                                }

                                raw_materials.append(current_rm)

                            
                            clients = []
                            clientes = http.request.env['irco.clientes.production'].search([('mrp_production_id', '=', production_order['id'])])
                            for cliente in clientes:
                                dieta = ""
                                if cliente['dieta_id'].id:
                                    dieta = cliente['dieta_id'].name
                                obj = {
                                    "id": cliente['partner_id'].id,
                                    "name": cliente['partner_id'].name,
                                    "diet_name": dieta,
                                    "quantity": cliente["cant_prod"]
                                }
                                clients.append(obj)
                            
                            dish = {
                                "id": production_order['id'],
                                "name": production_order['name'],
                                "quantity": int(production_order['product_qty']),
                                "quantity_produced": production_order['cant_producida'],
                                "product_id": production_order['product_id'].product_tmpl_id.id,
                                "product_name": production_order['product_id'].name,
                                "state": state,
                                "clients": clients,
                                "raw_materials": raw_materials,
                                "date": str(production_order['date_planned_start'].strftime("%d/%m/%Y")),
                                "date_US": str(production_order['date_planned_start'].strftime("%Y/%m/%d")),
                            }

                            response.append(dish)

                    except Exception as e:
                        # response = [{
                        #     "message": {
                        #         "successful": False,
                        #         "message": "No se ha podido obtener las órdenes de producción",
                        #         "error": str(e) + " ID Order Production Failed = " + str(production_order['id'])
                        #     }    
                        # }]

                        _logger.error(str(e))
        
            response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
 
    @http.route(route='/api/op/id/<int:user_id>/<int:op_id>', auth='user', methods=['GET'], type='http')
    def opbyid(self, user_id, op_id, **kw):
        try:

            datosalmacenes = http.request.env['res.users'].search([('id', '=', user_id)]).almacenes

            for almacen in datosalmacenes:
                _logger.info('*************** Almacen ************ %s' %almacen.id)

                stock = http.request.env['stock.warehouse'].search([('id', '=', almacen.id)])

                response = dict()
                transformStates = {'draft': 'Borrador', 'confirmed': 'Confirmado', 'planned': 'Planificado', 'progress': 'En proceso', 'done': 'Hecho', 'cancel': 'Cancelado'}

                production_order = http.request.env['mrp.production'].search([('id', '=', op_id)])
                                        
                state = transformStates.get(production_order['state'], 'No State')
                raw_materials = list()

                if state is not "Borrador":
                    lista_materiales = http.request.env['stock.move'].search([('raw_material_production_id', '=', production_order['id'])])
                    
                else:
                    lista_materiales = http.request.env['mrp.bom.line'].search([('bom_id', '=', production_order['bom_id'].id)])

                for raw_material in lista_materiales:
                    lot = http.request.env['stock.move.line'].search([('move_id', '=', raw_material['id'])])

                    if len(lot) > 0:
                        done = raw_material['quantity_done'] if state is not 'Borrador' else 0.0
                        reserved = raw_material['reserved_availability'] if state is not 'Borrador' else 0.0
                        lot_line = lot[0].id if state is not 'Borrador' else -1
                        lot_id = lot[0].lot_id.id if state is not 'Borrador' else -1
                        lot_name = lot[0].lot_id.name if state is not 'Borrador' else ""
                    else:
                        reserved = 0.0; done = 0.0; lot_line = -1; lot_id = -1; lot_name = ""
                    
                    quantity = raw_material['product_uom_qty'] if state is not 'Borrador' else raw_material['product_qty']
                    
                    if lot_id == False or lot_name == False:
                        lot_id = -1
                        lot_name = ""
                    
                    current_rm = {
                        "id": raw_material['id'],
                        "product_id": raw_material['product_id'].id,
                        "name": raw_material['product_id'].name,
                        "quantity": quantity,
                        "unity": raw_material['product_uom'].name,
                        "reserved": reserved,
                        "done": done,
                        "lot_line": lot_line,
                        "lot_id": lot_id,
                        "lot_name": lot_name
                    }

                    raw_materials.append(current_rm)

                clients = []
                clientes = http.request.env['irco.clientes.production'].search([('mrp_production_id', '=', production_order['id'])])
                for cliente in clientes:
                    dieta = ""
                    if cliente['dieta_id'].id:
                        dieta = cliente['dieta_id'].name
                    obj = {
                        "id": cliente['partner_id'].id,
                        "name": cliente['partner_id'].name,
                        "diet_name": dieta,
                        "quantity": cliente["cant_prod"]
                    }
                    clients.append(obj)

                response = {
                    "id": production_order['id'],
                    "name": production_order['name'],
                    "quantity": int(production_order['product_qty']),
                    "quantity_produced": production_order['cant_producida'],
                    "product": production_order['product_id'].name,
                    "product_id": production_order['product_id'].product_tmpl_id.id,
                    "product_name": production_order['product_id'].name,
                    "clients": clients,
                    "state": state,
                    "raw_materials": raw_materials,
                    "date": str(production_order['date_planned_start'].strftime("%d/%m/%Y")),
                    "date_US": str(production_order['date_planned_start'].strftime("%Y/%m/%d")),
                }

        except Exception as e:
            response = [{
                "message": {
                    "successful": False,
                    "message": "Fallo al recuperar las órdenes de producción",
                    "error": str(e)
                }    
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # ENDPOINT 2 (Devuelve todas las delegaciones que hay en la base de datos)(Modelo: irco.delegacion)
    @http.route(route='/api/all/delegs', auth='user', methods=['GET'], type='http')
    def delegaciones(self, **kw):
        try:
            delegs = http.request.env['irco.delegacion'].search([])
            response = list()

            for delegacion in delegs:
                current_deleg = {
                    "id": delegacion['id'],
                    "name": delegacion['name'],
                }
                response.append(current_deleg)

            response = sorted(response, key = lambda k:k['name'])
        
        except Exception as e:
            response = [{
                "message": {
                    "status": False,
                    "message": "Ha ocurrido un problema al recuperar las delegaciones",
                    "error": str(e)
                }
            }]

            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 3 (Devuelve todos los servicios que hay en la base de datos)(Modelo: irco.servicios)
    @http.route(route='/api/all/services', auth='user', methods=['GET'], type='http')
    def servicios(self, **kw):
        try:
            lista_servicios = http.request.env['irco.servicios'].search([])

            response = list()

            for service in lista_servicios:
                current_service = {
                    "id": service['id'],
                    "name": service['name'],
                }
                
                response.append(current_service)

            response = sorted(response, key = lambda k:k['name'])
        
        except Exception as e:
            response = [{
                "message": {
                    "successful": False,
                    "message": "No se han podido recuperar los servicios",
                    "error": str(e)
                }
            }]

            _logger.error(str(e))

        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 4 (Devuelve los datos de los clientes (id, name, delegacion y servicio))(Modelo: res.partner)
    @http.route(route='/api/all/clients', auth='user', methods=['GET'], type='http')
    def obten_clientes(self, **kw):
        try:
            clients = http.request.env['res.partner'].search([('customer', '=', True), ('supplier', '=', False)])
            response = list()

            for client in clients:
                if client.delegacion and client.tipo_servicio:
                    current_client = {
                        "id": client['id'],
                        "name": client['name'],
                        "delegacion_id": client['delegacion'].id,
                        "delegacion_name": client['delegacion'].name,
                        "servicio_id": client['tipo_servicio'].id,
                        "servicio_name": client['tipo_servicio'].name,
                    }
                    
                    response.append(current_client)

                response = sorted(response, key = lambda k:k['name'])
        
        except Exception as e:
            response = [{
                "message": {
                    "successful": False,
                    "message": "Ha ocurrido un problema al recuperar los clientes",
                    "error": str(e)
                }
            }]

            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # ENDPOINT 5 (Devuelve todos los productos que van a aparecer en la APP/APK)(Modelo: product.product)
    @http.route(route='/api/all/rawmaterials/<int:deleg>/<int:service>', auth='user', methods=['GET'], type='http')
    def muestra_mp(self, deleg, service, **kw):
        try: 
            lista_productos = http.request.env['product.product'].search([('delegacion', '=', deleg), ('tipo_servicio', '=', service)])
        
            response = list()
            for producto in lista_productos:
                referencia = producto['default_code']
                name = producto['name']
                full_name = name + " ("+ str(referencia) + ")"
                raw_material = {
                    "product_id": producto['id'],
                    "full_name": full_name,
                    "name": name,
                    "unity": producto['uom_id'].name
                }
                response.append(raw_material)
            
            response = sorted(response, key = lambda k:k['full_name'])
        
        
        except Exception as e:
            response = [{
                "message": {
                    "successful": False,
                    "message": "No se han podido recuperar las materias primas de tu delegación o servicio",
                    "error": str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type='application/json;charset=utf-8', status = 200)
    
    #ENDPOINT 6 (Devuelve todos los platos asignados a una delegación y servicio)
    @http.route(route='/api/all/dishes/<int:deleg>/<int:service>', auth='user', methods=['GET'], type='http')
    def platos(self, deleg, service, **kw):
        try:
            
            dishes = http.request.env['product.template'].search([('plato_delegacion', '=', deleg), ('plato_servicio', '=', service), ('es_plato', '=', True)])
        
            response = list()
            for dish in dishes:
                current_dish = {
                    "id": dish['id'],
                    "name": dish['name']
                }
                response.append(current_dish)

            response = sorted(response, key = lambda k:k['name'])
        
        except Exception as e:
            response = [{
                "message": {
                    "successful": False,
                    "message": "No se ha podido obtener los platos de la delegación y servicio de este usuario",
                    "error": str(e)
                }
            }]

            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 7 (Devuelve la delegación y el servicio del usuario que esta usando la app)(Modelo: res.partner)
    @http.route(route='/api/metadata/<int:id>/<int:partnerid>', auth='user', methods=['GET'], type='http')
    def devuelve_deleg_service(self, id, partnerid, **kw):
        try:
            user = http.request.env['res.users'].search([('id', '=', id)])
            stores = user.almacenes
            delegaciones = user.delegaciones
            servicios = user.servicios
            stores_of_user = list()
            for store in stores:
                current_store = {
                    "id": store.id,
                    "name": store.name
                }
                
                stores_of_user.append(current_store)

            if len(delegaciones) > 0 and len(servicios) > 0:
                delegacion_id = delegaciones[0].id
                delegacion_name = delegaciones[0].name
                servicio_id = servicios[0].id
                servicio_name = servicios[0].name
            else:
                delegacion_id, servicio_id = -1, -1
                delegacion_name, servicio_name = '', ''

            companies = http.request.env['res.partner'].search([('id', '=', partnerid)])
            company = dict()

            for comp in companies:
                company["company_id"] = comp['parent_id'].id if comp['parent_id'].id != False else -1
                company["company_name"] = comp['parent_id'].name if comp['parent_id'].name != False else ""
               
            response = {
                "delegacion_id": delegacion_id,
                "delegacion_name": delegacion_name,
                "servicio_id": servicio_id,
                "servicio_name": servicio_name,
                "stores": stores_of_user,
                "company_id": company["company_id"],
                "company_name": company["company_name"]
            }

        except Exception as e:
            response = {
                "message": {
                    "successful": False,
                    "message": "No se ha podido recuperar los metadatos del usuario",
                    "error": str(e)
                }
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 8 (Devuelve un listado de lotes asignados a esa materia prima en específico)
    @http.route(route='/api/all/lots/<int:productid>/<int:store>', auth='user', methods=['GET'], type='http')
    def devuelve_lotes(self, productid, store, **kw):
        try:
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', store)])
            stock = http.request.env['stock.location'].search([('id', '=', tipo_almacen[0].lot_stock_id.id)])
            padre = http.request.env['stock.location'].search([('id', '=', stock[0].location_id.id)])

            listado_lotes = http.request.env['stock.production.lot'].search([('product_id', '=', productid)], order="id desc")

            response = list()

            for lote in listado_lotes:
                nombre_lote = lote['name'].split('/')
                if len(nombre_lote)== 5:
                    if nombre_lote[3] == padre[0].name:
                        if lote['product_qty'] > 0:
                            objeto = {
                                "id": lote['id'],
                                "name": lote['name'],
                                "quantity": str(round(lote['product_qty'], 2)),
                                "unity": str(lote['product_uom_id'].name)
                            }

                            response.append(objeto)
      
        except Exception as e:
            response = [{
                "message": {
                    "successful": False,
                    "message": "No se han podido recuperar los lotes para este producto",
                    "error": str(e)
                }
            }]

            _logger.error(str(e))
            
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 8 (Crear nueva orden de producción)
    @http.route('/api/create/op', type = 'http', auth = 'user', cors = CORS, methods = ['POST'], csrf = False)
    def crear_orden(self, **post):
        dish = int(post.get('dish'))
        client = int(post.get('client'))
        deleg = int(post.get('deleg'))
        store = int(post.get('store'))
        quantity = int(post.get('quantity'))
        fecha = post.get('date')
       
        aux = fecha.split('/')
        fecha_formateada = aux[-1] + '-' + aux[1] + '-' + aux[0] + ' 06:00:00'

        try:
            _logger.info('******* Plato Template ******** %s' %dish)
            producto = http.request.env['product.product'].search([('product_tmpl_id', '=', dish)])
            producto_id = producto[0].id
            _logger.info('******* Producto ******** %s' %producto_id)
            
            materiales =  http.request.env['mrp.bom'].search([('product_tmpl_id', '=', dish)])
            material = materiales[0].id
            
            _logger.info('******* Material ******** %s' %material)
            almacenes = http.request.env['stock.picking.type'].search([('code', '=', 'mrp_operation'), ('warehouse_id', '=', store)])
            _logger.info('************* Location Dest ID ************ %s' %almacenes[0].default_location_dest_id.id)
           
            new_order = http.request.env['mrp.production'].create({
                'delegacion': deleg,
                'date_planned_start': fecha_formateada,
                'date_start': fecha_formateada,
                'product_id': producto_id,
                'product_qty': float(quantity),
                'cant_producida': quantity,
                'bom_id': material,
                'picking_type_id': almacenes[0].id,
                'location_src_id': almacenes[0].default_location_src_id.id,
                'location_dest_id': almacenes[0].default_location_dest_id.id,
            })
            
            _logger.info('Crea la orden')
            orden = new_order[0].id
            asignar_orden = http.request.env['irco.clientes.production'].create({
                'mrp_production_id': orden,
                'partner_id': client,
                'cant_prod': 0,
                'raciones_extra_cliente': 0,
                'ruta_reparto_secuencia': 0,
                'cant_env': 'Todavia indefinida'
            })
            
            response = {
                "successful": True,
                "message": "Orden de producción creada con éxito",
                "error": ""
            }

        except Exception as e:
            response = {
                "successful": False,
                "message": "No se ha podido crear la orden de producción",
                "error": str(e)
            }

            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 10 (Cancelar Orden de produción)(Solo si la orden está en borrador, o confirmada)
    @http.route('/api/cancel/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def cancelar_orden(self, **post):
        order_id = int(post.get('id'))
        try:
            orden = http.request.env['mrp.production'].search([('id', '=', order_id)])
            orden.action_cancel()
            response = {
                'successful': True, 
                'message': 'Orden de producción cancelada correctamente', 
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False, 
                'message': 'No se ha podido cancelar la orden de producción', 
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # ENDPOINT 11 (Actualizar estado de la orden)(Borrador -> Confirmada)     (Solo se puede actualizar asi, no se debe actualizar de otra forma)
    @http.route('/api/confirm/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_estado(self, **post):
        order_id = int(post.get('id'))
        product_id = int(post.get('product'))
        quantity = float(post.get('quantity'))
        date = post.get('date')

        aux = date.split('/')
        fecha_formateada = aux[-1] + '-' + aux[1] + '-' + aux[0] + ' 06:00:00'

        try:
            order = http.request.env['mrp.production'].search([('id', '=', order_id)])
            
            if order[0].state != 'draft':
                response = { 
                    'successful': False, 
                    'message': 'Esta orden de producción ya está confirmada',
                    'error': '' 
                }
            else:
                producto = http.request.env['product.product'].search([('product_tmpl_id', '=', product_id)])
                producto_id = producto[0].id
                materiales =  http.request.env['mrp.bom'].search([('product_tmpl_id', '=', product_id)])
                material = materiales[0].id
               
                order_actualize = order.write({
                    'date_planned_start': fecha_formateada,
                    'product_id': producto_id,
                    'product_qty': quantity,
                    'bom_id': material,
                })

                if order_actualize:
                    order.action_confirm()
                    response = { 
                        'successful': True, 
                        'message': 'Se ha confirmado la orden de producción satisfactoriamente',
                        'error': '' 
                    }
                
                else:
                    response = { 
                        'successful': False, 
                        'message': 'No se ha podido confirmar la orden de producción',
                        'error': '' 
                    }

        except Exception as e:
            response = { 
                'successful': True, 
                'message': 'Se ha confirmado la orden de producción satisfactoriamente',
                'error': '' 
            }

            _logger.error(str(e))
            
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 12 (Crear nueva materia prima para la orden)
    @http.route('/api/add/mp/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_mp_de_orden(self, **post):
        try:
            producto_id = int(post.get('product'))
            orden_id = int(post.get( 'op'))
            cantidad = float(post.get('quantity'))
            producto_completo = http.request.env['product.product'].search([('id', '=', producto_id)])
            orden_completa = http.request.env['mrp.production'].search([('id', '=', orden_id)])
            nombre_orden = orden_completa[0].name
            
            nueva_mp = http.request.env['stock.move'].create({
                "product_id": producto_id,
                "name": nombre_orden,
                "origin": nombre_orden,
                "product_uom_qty": cantidad,
                "location_id": orden_completa[0].location_src_id.id,
                "product_uom": producto_completo[0].uom_id.id,
                "location_dest_id": 7,
                "raw_material_production_id": orden_id, 
            })
            
            response = {
                'successful': True, 
                'message': 'Se ha añadido la materia prima satisfactoriamente', 
                'error': '' 
            }
        
        except Exception as e:
            response = {
                'successful': False, 
                'message': 'No se ha podido añadir la materia prima a la orden de producción', 
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # ENDPOINT 13 (Actualizar materia prima de la orden)
    @http.route('/api/update/mp/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_mp_orden(self, **post):
        try:
            mp_id = int(post.get('id'))
            product_id = int(post.get('product'))
            quantity = float(post.get('quantity'))
            #reserved = float(post.get('reserved'))
            #done = float(post.get('done'))
       
            producto_completo = http.request.env['product.product'].search([('id', '=', product_id)])
            actualizar_mp = http.request.env['stock.move'].search([('id', '=', mp_id)]).write({
                "product_id": product_id,
                "product_uom_qty": quantity,
                "product_uom": producto_completo[0].uom_id.id,
                #"reserved_availability": reserved,
                #"quantity_done": done,
            })
            
            response = {
                'successful': True, 
                'message': 'La materia prima se ha actualizado satisfactoriamente',
                'error': ''
            }
        
        except Exception as e:
            response = {
                'successful': False, 
                'message': 'No se ha podido actualizar la materia prima', 
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # ENDPOINT 14 (Eliminar materia prima de la orden)
    @http.route('/api/delete/mp/op', type='http', auth = 'user', cors=CORS, methods=['POST'], csrf=False)
    def eliminar_mp(self, **post):
        id = int(post.get('id'))
        try:
            delete_mp = http.request.env['stock.move'].search([('id', '=', id)]).write({
                "product_uom_qty": 0,
                "reserved_availability": 0,
                "quantity_done": 0,
            })
            response = {
                'successful': True, 
                'message': 'La materia prima se ha eliminado satisfactoriamente', 
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False, 
                'message': 'No se ha podido eliminar la materia prima', 
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # ENDPOINT 15 (Guardar lote de producto)(Modelo: stock.move.line)
    @http.route('/api/assign/lot', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def asignar_lote(self, **post):
        try:
            id = str(post.get('id')).split('-')
            product_id = str(post.get('productid')).split('-')
            lot = str(post.get('lot')).split('-')
            quantity = str(post.get('quantity')).split('-')
            
            for i in range(len(id)):
                linea_mp = http.request.env['stock.move'].search([('id', '=', int(id[i]))])
                linea_prod = http.request.env['product.product'].search([('id', '=', int(product_id[i]))])
                if float(quantity[i]) == 0:
                    lote_creado = 0
                    buscar_lote = http.request.env['stock.production.lot'].search([('product_id', '=', int(product_id[i])), ('name', '=', 'MateriaPrimaVacia')])
                    if len(buscar_lote) > 0:
                        lote_creado = buscar_lote[0].id
                    else:
                        nuevo_lote = http.request.env['stock.production.lot'].create({
                            "name": "MateriaPrimaVacia",
                            "product_id": int(product_id[i]),
                        })
                        lote_creado = nuevo_lote[0].id

                    asignar_lote = http.request.env['stock.move.line'].create({
                        "move_id": int(id[i]), 
                        "product_id": int(product_id[i]),
                        "lot_id": lote_creado, 
                        "qty_done": float(quantity[i]),
                        "product_uom_id": linea_prod[0].uom_id.id,
                        "location_id": linea_mp[0].location_id.id,
                        "location_dest_id": linea_mp[0].location_dest_id.id,
                        "production_id": linea_mp[0].raw_material_production_id.id
                    })
                    
                
                else:
                    lote_asignado = http.request.env['stock.move.line'].create({
                        "move_id": int(id[i]), 
                        "product_id": int(product_id[i]),
                        "lot_id": int(lot[i]), 
                        "qty_done": float(quantity[i]),
                        "product_uom_id": linea_prod[0].uom_id.id,
                        "location_id": linea_mp[0].location_id.id,
                        "location_dest_id": linea_mp[0].location_dest_id.id,
                        "production_id": linea_mp[0].raw_material_production_id.id
                    })
            
            response = {
                'successful': True, 
                'message': 'Se ha asignado el lote satisfactoriamente',
                'error': ''
            }
            
        except Exception as e:
            response = {
                'successful': False, 
                'message': 'No se ha podido asignar el lote a la materia prima', 
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

     # Endpoint (Actualizar lote de la materia prima) (Modelo: stock.move.line)
    @http.route('/api/re/assign/lot', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_lote_materiaprima(self, **post):
        id_lineas = str(post.get('lotline')).split('-')
        lotes = str(post.get('lot')).split('-')
        quantitys = str(post.get('quantity')).split('-')
        products_id = str(post.get('productid')).split('-')
        try:
            for i in range(len(id_lineas)):
                linea_lote = http.request.env['stock.move.line'].search([('id', '=', int(id_lineas[i]))])
                if float(quantitys[i]) == 0:
                    lote_creado = 0
                    buscar_lote = http.request.env['stock.production.lot'].search([('product_id', '=', int(products_id[i])), ('name', '=', 'MateriaPrimaVacia')])
                    if len(buscar_lote) > 0:
                        lote_creado = buscar_lote[0].id
                    else:
                        nuevo_lote = http.request.env['stock.production.lot'].create({
                            "name": "MateriaPrimaVacia",
                            "product_id": int(products_id[i]),
                        })
                        lote_creado = nuevo_lote[0].id

                    linea_lote.write({
                        "product_id": int(products_id[i]),
                        "lot_id": lote_creado, 
                        "qty_done": float(quantitys[i]),
                    })
                else:
                    linea_lote.write({
                        "product_id": int(products_id[i]),
                        "lot_id": int(lotes[i]), 
                        "qty_done": float(quantitys[i]),
                    })
            response = {
                'successful': True,
                'message': 'Se ha actualizado el lote satisfactoriamente',
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido actualizar el lote',
                'error': str(e)
            }
            _logger.error(str(e))
        
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # ENDPOINT 16 (Producir orden)
    @http.route('/api/produce/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def producir_orden(self, **post):
        order_id = int(post.get('order'))
        try:
            
            orden = http.request.env['mrp.production'].search([('id', '=', order_id)])
            if orden[0].state == 'confirmed':
                cantidad = orden[0].product_qty
                id_producto = orden[0].product_id.id
                producto_uom = orden[0].product_uom_id.id
                nombre = orden[0].name
                lista_nombre = nombre.split('/')
                aux = int(lista_nombre[2])
                
                linea_orden = http.request.env['stock.move'].search([('production_id', '=', order_id)])
                id_linea = linea_orden[0].id
                location_id = linea_orden[0].location_id.id
                location_dest_id = linea_orden[0].location_dest_id.id
                hoy = str(date.today().strftime("%d/%m/%Y")) + '/' + str(aux)
                
                orden.write({
                    "state": "progress",
                })

                nuevo_lote = http.request.env['stock.production.lot'].create({
                    "name": hoy,
                    "product_id": id_producto,
                })

                nuevo_producto_finalizado = http.request.env['stock.move.line'].create({
                    "move_id": id_linea,
                    "product_id": id_producto,
                    "product_uom_id": producto_uom,
                    "qty_done": cantidad,
                    "lot_id": nuevo_lote[0].id,
                    "location_id": location_id,
                    "location_dest_id": location_dest_id,
                })

                response = {
                    'successful': True, 
                    'message': 'Se ha producido la orden de producción correctamente', 
                    'error': ''
                }
            else:
                response = {
                    'successful': False, 
                    'message': 'Esta orden de producción ya se encuentra en proceso', 
                    'error': ''
                }
            

        except Exception as e: 
            response = {
                'successful': False, 
                'message': 'No se ha podido producir la orden de producción', 
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # Endpoint (Editar cantidad producida/realizada)(EJECUTAR SOLO SI LA ORDEN ESTÁ EN PROCESO)(Modelo: mrp.production)
    @http.route('/api/update/produce/process', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_cantidad_hecha(self, **post):
        order_id = int(post.get('order'))
        quantity = float(post.get('quantity'))

        try:
            mi_orden = http.request.env['mrp.production'].search([('id', '=', order_id)])
            linea_sm = http.request.env['stock.move'].search([('production_id', '=', order_id)])
            linea_sm_id = linea_sm[0].id
            buscar_linea_producto_final = http.request.env['stock.move.line'].search([('move_id', '=', linea_sm_id)])
            linea_producto = http.request.env['stock.move.line'].search([('id', '=', buscar_linea_producto_final[0].id)])
            if mi_orden[0].state == 'progress':
                mi_orden_actualizada = mi_orden.write({
                    "product_qty": quantity,
                })
                linea_actualizada = linea_producto.write({
                    "qty_done": quantity,
                })
                
                response = {'successful': True, 'message': 'Cantidad de la orden actualizada', 'error': ''}
               
            else: 
                response = {'successful': False, 'message': 'Esta orden no se encuentra en estado de proceso', 'error': ''}
                
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido actualizar la cantidad producida para esta orden de producción',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Validar una orden como "Hecha")(SOLO SE PUEDE HACER SI LA ORDEN ESTÁ "EN PROCESO")
    @http.route('/api/finalize/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def marcar_orden_hecha(self, **post):
        order_id = int(post.get('order'))

        try:
            mi_orden = http.request.env['mrp.production'].search([('id', '=', order_id)])
            if mi_orden[0].state == 'progress':
                # Para encontrar el producto finalizado(En stock move)
                producto_finalizado_stock_move = http.request.env['stock.move'].search([('production_id', '=', order_id)])
                sm_id_prodfinalizado = producto_finalizado_stock_move[0].id

                # Ahora a encontrar la línea de lote (En stock move line) (pf = producto finalizado)
                pf = http.request.env['stock.move.line'].search([('move_id', '=', sm_id_prodfinalizado)])
                lote_pf = pf[0].lot_id.id

                # Ahora a recorrer todas las lineas de lote de la orden
                lineas_mp = http.request.env['stock.move.line'].search([('production_id', '=', order_id)])
                for linea in lineas_mp:
                    linea.write({
                        "lot_produced_id": lote_pf
                    })

                mi_orden.button_mark_done()
            
                response = {'successful': True, 'message': 'Orden de producción finalizada satisfactoriamente', 'error': ''}
            
            elif mi_orden[0].state == 'done':
                response = {'successful': False, 'message': 'La orden de producción ya se encuentra en estado de finalizado', 'error': ''}
            else:
                response = {'successful': False, 'message': 'La orden de producción no se encuentra en estado de proceso', 'error': ''}

            
            
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido finalizar la orden de producción', 'error': str(e)}

            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Comprobar disponibilidad de los materiales en la orden de producción)
    @http.route('/api/check/disponibility/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def comprobar_disponibilidad_orden_produccion(self, **post):
        id_orden = int(post.get('order'))
        try:
            mi_orden = http.request.env['mrp.production'].search([('id', '=', id_orden)])
            _logger.info('************ Objeto ****************** %s' %mi_orden)
            mi_orden.action_assign()
            response = {'successful': True, 'message': 'Disponibilidad comprobada satisfactoriamente', 'error': ''}

        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido comprobar la disponibilidad de esta orden de producción', 'error': str(e)}
            _logger.error(str(e))
            
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Quitar cantidades reservadas de la orden de producción) (Solo funciona en "CONFIRMADO" y "EN PROCESO")
    @http.route('/api/unreserve/op', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def quitar_cantidades_reservadas(self, **post):
        id_orden = int(post.get('order'))
        try:
            mi_orden = http.request.env['mrp.production'].search([('id', '=', id_orden)])
            _logger.info('************ Procede a llamar al metodo ************')
            mi_orden.button_unreserve()
            _logger.info('******************* Ya ha hecho el metodo *******************')
            response = {'successful': True, 'message': 'Se han quitado las cantidades reservadas', 'error': ''}

        except Exception as e:
            response = {'successful': False, 'message': 'No se han podido quitar las cantidades reservadas', 'error': str(e)}
            _logger.error(str(e))
        
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (cambiar cantidades reservadas)
    @http.route('/api/change/reserved/mp', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def cambiar_materias_primas_reservadas(self, **post):
        id_orden = int(post.get('order'))

        try:
            lineas_mp = http.request.env['stock.move'].search([('raw_material_production_id', '=', id_orden)])
            
            for linea in lineas_mp:
                linea_id = linea['id']

                lineas_lote = http.request.env['stock.move.line'].search([('move_id', '=', linea_id)])

                if len(lineas_lote) > 0:
                    for linea_lote in lineas_lote:
                        
                        if linea_lote['product_uom_qty']>0:
                            reservado = linea_lote['product_uom_qty']
                            linea_lote.write({
                                "qty_done": reservado,
                            })

            response = {'successful': True, 'message': 'Se han quitado las cantidades reservadas', 'error': ''}

        except Exception as e:
            response = {'successful': False, 'message': 'No se han podido quitar las cantidades reservadas', 'error': str(e)}
            _logger.error(str(e))
        
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)