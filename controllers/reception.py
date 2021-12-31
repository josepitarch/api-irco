# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response, request
import json
import logging
import datetime
from datetime import date
from datetime import timedelta
import calendar
from odoo.addons.mrp.models.mrp_production import MrpProduction

_logger = logging.getLogger(__name__)

CORS = "*"
class GetControllerPedidosRecepciones(http.Controller):
    
    # Controller para manejar todas las peticiones GET a la app, sobre "Pedidos y Recepciones"
    # Controller creado por Jorge JM

    # Endpoint (Proporciona un listado de pedidos de compra que estén pendientes de recibir)(purchase.order)(stock.picking.type y stock.warehouse para el tema del almacen)
    @http.route('/api/purchase/orders/<int:almacen>', type='http', auth='user', methods=['GET'])
    def obtener_pedidos_compra(self, almacen, **kw):
        try:
            tipo_almacen = http.request.env['stock.picking.type'].search([('warehouse_id', '=', almacen), ('name', '=', 'Recepciones'), ('code', '=', 'incoming')])
            
            today = date.today()
            yesterday = today + timedelta(days=-14)
            fecha_formateada = str(yesterday) + " 00:00:00"
            
            pedidos_compra = http.request.env['purchase.order'].search([('picking_type_id', '=', tipo_almacen[0].id), ('state', '!=', 'done'), ('state', '!=', 'cancel'), ('state', '!=', 'approved'), ('date_order', '>=', fecha_formateada)])
            response = list()

            transformStates = {'draft': 'Petición Presupuesto', 'sent': 'Petición de cotización enviada', 'to_approve': 'Para aprobar', 'purchase': 'Pedido de Compra', 'done': 'Bloqueado', 'cancel': 'Cancelado', 'approved': 'Aprobado'}

            for order in pedidos_compra:
                order_id = order['id']
                state = transformStates.get(order['state'], 'Sin estado')
                products_of_order = list()
                
                products = http.request.env['purchase.order.line'].search([('order_id', '=', order_id)])
                
                for product in products:
                    current_product = {
                        'id': product['id'],
                        'product_id': product['product_id'].id,
                        'name': product['product_id'].name,
                        'quantity': product['product_qty'],
                        'unity': product['product_uom'].name
                    }
                    
                    products_of_order.append(current_product)

                purchase_maker = order['user_id'].name if order['user_id'].name is not False else ''
                
                current_order = {
                    "id": order_id,
                    "reference": order['name'],
                    "provider": order['partner_id'].name,
                    "purchase_maker": purchase_maker,
                    "date_order": str(order['date_order'].strftime("%d/%m/%Y")),
                    "origin": order['origin'],
                    "raw_materials": products_of_order,
                    "date_planned": str(order['date_planned'].strftime("%d/%m/%Y")),
                    "state": state,
                }
                
                response.append(current_order)

        except Exception as e: 
            response = [{
                'message': {
                    'successful': False, 
                    'message': 'No se han podido obtener los pedidos de compra para el almacén asignado a este usuario',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener proveedores para la futura creación del pedido) (Modelo: res.partner)
    @http.route('/api/all/providers', type='http', auth='user', methods=['GET'])
    def obtener_datos_proveedores(self, **kw):
        try:
            providers = http.request.env['res.partner'].search([('supplier', '=', 'True')])

            response = list()

            for provider in providers:
                current_provider = {
                    "id": provider['id'],
                    "name": provider['name'],
                    "display_name": provider['display_name']
                }

                response.append(current_provider)

            response = sorted(response, key = lambda k:k['name'])
            
        except Exception as e:
            response = [{
                'message': {
                    'successful': False, 
                    'message': 'No se han podido obtener los datos de los proveedores',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener todos los tipos de almacen (Exclusivo para crear la orden)) (Modelo: stock.picking.type)
    @http.route('/api/all/stores', type='http', auth='user', methods=['GET'])
    def obtener_tipos_almacenes(self, **kw):
        try:
            stores = http.request.env['stock.picking.type'].search([('code', '=', 'incoming')])

            response = list()

            for store in stores:

                real_name = str(store['warehouse_id'].name) + ' ' + str(store['name'])

                current_store = {
                    "id": store['id'],
                    "name": real_name
                }

                response.append(current_store)

            response = sorted(response, key = lambda k:k['name'])
            
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener los tipos de almacén',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener datos de usuarios)(Modelo: res.users)
    @http.route('/api/users/<int:userid>', type='http', auth='user', methods=['GET'])
    def obtener_usuarios_aprobantes(self, userid, **kw):
        try:
            users = http.request.env['res.users'].search([('id', '!=', userid)])
            response = list()

            for user in users:
                current_user = {
                    "id": user['id'],
                    "name": user['name'],
                }

                response.append(current_user)
            
            response = sorted(response, key = lambda k:k['name'])

        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener los usuarios',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
            
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener todas las solicitudes de compra creadas por el usuario)(Modelo: bom.purchase.request)(Modelo: bom.purchase.request.line)
    @http.route('/api/all/purchase/requests/<int:userid>', type='http', auth='user', methods=['GET'])
    def obtener_solicitudes_usuario(self, userid, **kw):
        try: 
            purchase_requests = http.request.env['bom.purchase.request'].search([('user_id', '=', userid)])
            response = list()
            transformStates = {'draft': 'Borrador', 'to_approve': 'Para aprobar', 'approved': 'Aprobada', 'rejected': 'Rechazada', 'done': 'Hecha'}
            
            for purchase_request in purchase_requests:
                id_solicitud = purchase_request['id']
                state = transformStates.get(purchase_request['state'], 'Sin estado')
                if state == transformStates['draft']:
                    lista_compra = []
                    productos_solicitud = http.request.env['bom.purchase.request.line'].search([('request_id', '=', id_solicitud)])

                    for product in productos_solicitud:
                        current_product = {
                            "id": product['id'],
                            "product_id": product['product_id'].id,
                            "product_name": product['name'],
                            "quantity": product['product_qty'],
                            "unity": product['product_id'].uom_id.name,
                            "request_date": str(product['request_date'].strftime("%d/%m/%Y")),
                        }
                        lista_compra.append(current_product)
                    
                    current_purchase_order = {
                        "id": id_solicitud,
                        "name": purchase_request['name'],
                        "name_apk": "Solicitud " + str(id_solicitud),
                        "approver_id": purchase_request['approver_id'].id,
                        "approver_name": purchase_request['approver_id'].name,
                        "state": state,
                        "products": lista_compra,
                    }

                    response.append(current_purchase_order)
            
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener las solicitudes de este usuario',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
            
        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener datos de productos comprables)(Modelo: product.product)
    @http.route('/api/purchase/products/<int:deleg>/<int:service>', type='http', auth='user', methods=['GET'])
    def obtener_productos_comprables(self, deleg, service, **kw):
        try:
            products = http.request.env['product.product'].search([('delegacion', '=', deleg), ('tipo_servicio', '=', service), ('purchase_ok', '=', True)])
            response = list()
            
            for product in products:
                reference = product['default_code']
                name = product['name']
                full_name = name + " ("+ str(reference) + ") "
                current_product = {
                    "id": product['id'],
                    "name": product['name'],
                    "full_name": full_name,
                    "unity": product['uom_id'].name
                }

                response.append(current_product)
            
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener los productos comprables para este usuario',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    @http.route('/api/ware/return/<int:almacen>', type='http', auth='user', methods=['GET'])
    def obtener_recepciones(self, almacen, **kw):
        try:
            tipo_almacen = http.request.env['stock.picking.type'].search([('warehouse_id', '=', almacen), ('name', '=', 'Recepciones'), ('code', '=', 'incoming')])

            today = date.today()
            yesterday = today + timedelta(days=-14)
            fecha_formateada = str(yesterday) + " 00:00:00"

            listado_recepciones = http.request.env['stock.picking'].search([('picking_type_id', '=', tipo_almacen[0].id), ('state', '=', 'done'), ('scheduled_date', '>=', fecha_formateada)])
            
            response = list()

            transformStates = {'draft': 'Borrador', 'waiting': 'Esperando otra operacion', 'confirmed': 'En espera', 'assigned': 'Preparado', 'done': 'Hecho', 'cancel': 'Cancelado'}

            for recepcion in listado_recepciones:
                recepcion_id = recepcion['id']
                cadena_formateada = "Retorno de " + str(recepcion['name'])
                buscar_devolucion = http.request.env['stock.picking'].search([('origin', '=', cadena_formateada)])

                state = transformStates.get(recepcion['state'], 'Sin estado')
                lista_productos = []
                original = ""
                if recepcion['backorder_id']: 
                    original = recepcion['backorder_id'].name
                
                delivery_note = ""
                if recepcion['albaran_proveedor']:
                    delivery_note = recepcion['albaran_proveedor']

                productos = http.request.env['stock.move'].search([('picking_id', '=', recepcion_id)])
                
                if len(buscar_devolucion) == 0:
                    for producto in productos:
                        obj = {
                            'id': producto['id'],
                            'product_id': producto['product_id'].id,
                            'product_name': producto['name'],
                            'quantity': producto['product_uom_qty'],
                            'quantity_done': producto['quantity_done'],
                            'unity': producto['product_uom'].name
                        }

                        lista_productos.append(obj) 

                    rc = {
                        "id": recepcion_id,
                        "name": recepcion['name'],
                        "date": str(recepcion['scheduled_date'].strftime("%d/%m/%Y")),
                        "supplier": recepcion['partner_id'].name,
                        "origin": recepcion['origin'],
                        "original": original,
                        "delivery_note": delivery_note,
                        "state": state,
                        "products": lista_productos,
                    }

                    response.append(rc)
               
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener las recepciones validadas del almacén asignado a este usuario',
                    'error': str(e)
                }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener recepciones de albaranes en estado hecho) (Modelo: stock.picking)
    @http.route('/api/ware/reception/<int:almacen>', type='http', auth='user', methods=['GET'])
    def obtener_recepciones_no_hechas(self, almacen, **kw):
        try:
            tipo_almacen = http.request.env['stock.picking.type'].search([('warehouse_id', '=', almacen), ('name', '=', 'Recepciones'), ('code', '=', 'incoming')])
   
            listado_recepciones = http.request.env['stock.picking'].search([('picking_type_id', '=', tipo_almacen[0].id), ('state', '!=', 'done'), ('state', '!=', 'cancel')])
            
            response = list()

            transformStates = {'draft': 'Borrador', 'waiting': 'Esperando otra operacion', 'confirmed': 'En espera', 'assigned': 'Preparado', 'done': 'Hecho', 'cancel': 'Cancelado'}

            for recepcion in listado_recepciones:
                recepcion_id = recepcion['id']

                state = transformStates.get(recepcion['state'], 'Sin estado')
                lista_productos = []
                original = ""
                if recepcion['backorder_id']: 
                    original = recepcion['backorder_id'].name

                delivery_note = ""
                if recepcion['albaran_proveedor']:
                    delivery_note = recepcion['albaran_proveedor']

                products = http.request.env['stock.move'].search([('picking_id', '=', recepcion_id)])
                
                for product in products:
                    current_product = {
                        'id': product['id'],
                        'product_id': product['product_id'].id,
                        'product_name': product['name'],
                        'quantity': product['product_uom_qty'],
                        'quantity_done': product['quantity_done'],
                        'unity': product['product_uom'].name
                    }
                    lista_productos.append(current_product) 

                rc = {
                    "id": recepcion_id,
                    "name": recepcion['name'],
                    "date": str(recepcion['scheduled_date'].strftime("%d/%m/%Y")),
                    "supplier": recepcion['partner_id'].name,
                    "origin": recepcion['origin'],
                    "original": original,
                    "delivery_note": delivery_note,
                    "state": state,
                    "products": lista_productos,
                }
                
                response.append(rc)
         
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se ha podido obtener las recepciones del almacén asignado a este usuario',
                    'error': str(e)
                }      
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Movimientos de producto) (Modelo: stock.move.line)
    @http.route('/api/move/products/<int:store>', type='http', auth='user', methods=['GET'])
    def obtener_movimientos(self, store, **kw):
        try:
            hoy = date.today()
            mes_pasado = hoy + timedelta(days=-30)
            mes_formateado = str(mes_pasado) + ' 00:00:00'
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', store)])
       
            movements = http.request.env['stock.move.line'].search(['|', ('location_id', '=', tipo_almacen[0].lot_stock_id.id), ('location_dest_id', '=', tipo_almacen[0].lot_stock_id.id), '&', ('state', '=', 'done'), ('date', '>=', mes_formateado)], order='date desc')
            response = list()

            for movement in movements:
                
                if int(movement['qty_done']) > 0:
                    current_movement = {
                        "reference": movement['reference'],
                        "date": str(movement['date'].strftime("%d/%m/%Y")),
                        "product": movement['product_id'].name,
                        "done": movement['qty_done'],
                        "unity": movement['product_uom_id'].name,
                    }

                    response.append(current_movement)
            
        except Exception as e:
            response = [{
               'message': {
                    'successful': False,
                    'message': 'No se han podido obtener los productos pendientes a recibir del almacén asignado a este usuario',
                    'error': str(e)
               }
            }]

            _logger.error(str(e))
        
        response = json.dumps(response)
        
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Crear nueva solicitud de compra) (Modelo: bom.purchase.request)
    @http.route('/api/create/purchase/request', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_pedido_compra(self, **post):
        chef_id = int(post.get('requester'))
        
        try:
            request = http.request.env['bom.purchase.request'].create({
                "user_id": chef_id,
                "status": "draft",
                "approver_id": chef_id
            })

            response = {
                "successful": True,
                "message": "Se ha creado el pedido correctamente",
                'error': ''
            }
            
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha sido posible crear el pedido',
                'error': str(e)
            }

            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Crear productos para solicitud de compra)(Modelo: bom.purchase.request.line)
    @http.route('/api/create/product/request', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def asignar_producto_solicitud(self, **post):
        request_id = int(post.get('request'))
        product_id = int(post.get('product'))
        quantity = float(post.get('quantity'))
        fecha = post.get('date')
        
        aux = fecha.split('/')
        fecha_formateada = aux[-1] + '-' + aux[1] + '-' + aux[0]
        
        try:
            producto = http.request.env['product.product'].search([('id', '=', product_id)])
            nombre_formulado = str(producto[0].name) + ' [' + str(producto[0].default_code) + ']'
            asignar_producto = http.request.env['bom.purchase.request.line'].create({
                "product_id": product_id,
                "name": nombre_formulado,
                "product_qty": quantity,
                "request_date": fecha_formateada,
                "request_id": request_id,
                "product_uom_id": producto[0].uom_id.id
            })

            response = {
                'successful': True,
                'message': 'Se ha asignado el producto a la solicitud correctamente', 
                'error': ''
            }
            
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido asignar el producto a la solicitud',
                'error': str(e)
            }

            _logger.error(str(e))
            
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Enviar como "Aprobada" la solicitud)(Modelo: bom.purchase.order)
    @http.route('/api/approved/purchase', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_estado_solicitud(self, **post):
        id_solicitud = int(post.get('request'))
        try:
            mi_solicitud = http.request.env['bom.purchase.request'].search([('id', '=', id_solicitud)])
            mi_solicitud.button_approve()
            mi_solicitud.set_approved()
            
            response = {
                'successful': True,
                'message': 'Se ha aprobado la solicitud satifactoriamente',
                'error': ''
            }

        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido aprobar la solicitud',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)
        
        return Response(response, content_type='application/json;charset=utf-8', status = 200)

    # Endpoint (Actualizar cantidad recibida del producto del albaran) (Modelo: stock.move)
    @http.route('/api/update/quantity/done', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_cant_hecha_albaran(self, **post):
        products_id = str(post.get('products')).split('-')
        quantitys = str(post.get('quantitys')).split('-')

        try:
            for i in range(len(products_id)):
                cantidad_actualizada = http.request.env['stock.move'].search([('id', '=', int(products_id[i]))]).write({
                    'quantity_done': float(quantitys[i]),
                })
            
            response = {
                'successful': True,
                'message': 'Se ha actualizado la cantidad hecha correctamente',
                'error': ''
            }
            
        except Exception as e: 
            response = {
                'successful': False,
                'message': 'No se ha podido actualizar la cantidad recibida del producto',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Actualizar el estado de una recepcion "Borrador" -> "Preparado") (Modelo: stock.move)
    @http.route('/api/update/draft/reception', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def marcar_por_realizar(self, **post):
        id_recepcion = int(post.get('id'))

        try: 
            mi_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            mi_recepcion.action_confirm()
            
            response = {
                'successful': True,
                'message': 'Se ha actualizado la recepcion a preparada satisfactoriamente', 
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido actualizar a preparada la recepcion',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type='application/json;charset=utf-8', status = 200)

    # SOLO EJECUTAR CUANDO LA CANTIDAD NORMAL Y LA CANTIDAD HECHA SEAN LA MISMA
    # Endpoint (Actualizar el estado de una recepcion "Preparado" -> "Hecho") (Modelo: stock.move) SOLO EJECUTAR CUANDO LA CANTIDAD NORMAL Y LA CANTIDAD HECHA SEAN LA MISMA (Y NO SEAN LA MISMA)
    @http.route('/api/update/normal/reception', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def validar_normal(self, **post):
        id_recepcion = int(post.get('id'))
       
        try: 
            mi_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            _logger.info([mi_recepcion.id, mi_recepcion.name, mi_recepcion.origin, mi_recepcion.note, mi_recepcion.backorder_id, mi_recepcion.move_type, mi_recepcion.state, mi_recepcion.group_id, mi_recepcion.priority, mi_recepcion.scheduled_date, mi_recepcion.date, mi_recepcion.date_done, mi_recepcion.location_id, mi_recepcion.location_dest_id, mi_recepcion.picking_type_id, mi_recepcion.partner_id, mi_recepcion.company_id, mi_recepcion.owner_id, mi_recepcion.printed, mi_recepcion.is_locked, mi_recepcion.immediate_transfer, mi_recepcion.message_main_attachment_id, mi_recepcion.create_uid, mi_recepcion.create_date, mi_recepcion.write_uid, mi_recepcion.write_date, mi_recepcion.sale_id, mi_recepcion.batch_id, mi_recepcion.customer_signature, mi_recepcion.signer_name, mi_recepcion.ruta])
            auxiliar = mi_recepcion.button_validate()

            for pick_id in mi_recepcion:
                partner_id = pick_id.partner_id.id
                alb_prov = pick_id.albaran_proveedor
                origin = pick_id.origin
                pedido_compra = http.request.env['purchase.order'].search([('name', '=', origin)])
                albaran_padre_devolucion = pick_id.parent_picking_id

                if not albaran_padre_devolucion:
                    if pedido_compra:
                        if alb_prov:
                            lines = []    
                            for linea_pedido in pedido_compra.order_line:
                                if linea_pedido.qty_to_invoice > 0:
                                    taxes = linea_pedido.product_id.supplier_taxes_id
                                    tax_ids = taxes.ids
                                    lineas = (0, 0, {'product_id' : linea_pedido.product_id.id,
                                                    'name' : linea_pedido.product_id.name,
                                                    'quantity' : linea_pedido.qty_to_invoice,
                                                    'price_unit': linea_pedido.price_unit,
                                                    'account_analytic_id': linea_pedido.account_analytic_id.id,
                                                    'account_id': 357,
                                                    'purchase_line_id': linea_pedido.id,
                                                    'uom_id': linea_pedido.product_uom.id,
                                                    'invoice_line_tax_ids': [(6, 0, tax_ids)]
                                                    })
                                    lines.append(lineas)
                            data_factura = {
                                    'partner_id': partner_id,
                                    'reference': alb_prov,
                                    'type': 'in_invoice',
                                    'origin': origin,
                                    'account_id': pick_id.partner_id.property_account_payable_id.id,
                                    'payment_mode_id': pick_id.partner_id.supplier_payment_mode_id.id,
                                    'purchase_id': pedido_compra.id,
                                    'picking_id': pick_id.id,
                                    'fecha_recep_alb': pick_id.date_done,
                                    'invoice_line_ids': lines,
                            }
                            factura = http.request.env['account.invoice'].create(data_factura) 
                        else:
                            response = {
                                'successful': False,
                                'message': 'Se ha podido validar la recepcion, pero no se ha podido realizar la factura',
                                'error': 'No dispone del albarán de proveedor'
                            }
                else:
                    factura = http.request.env['account.invoice'].search([('picking_id', '=', albaran_padre_devolucion.id)])
                    if factura:
                        if factura.state == 'draft':
                            for linea_albaran in pick_id.move_ids_without_package:
                                cantidad = (linea_albaran.product_uom._compute_quantity(linea_albaran.quantity_done, linea_albaran.product_id.uom_po_id))*-1
                                precio_linea_factura = http.request.env['account.invoice.line'].search([('invoice_id', '=', factura.id),('product_id', '=', linea_albaran.product_id.id)])
                                taxes = linea_albaran.product_id.supplier_taxes_id
                                tax_ids = taxes.ids
                                linea_devolucion = {
                                            'invoice_id': factura.id,
                                            'product_id': linea_albaran.product_id.id,
                                            'name' : linea_albaran.product_id.name,
                                            'quantity' : cantidad,
                                            'uom_id': linea_albaran.unidad_medida_compra.id,
                                            'price_unit': precio_linea_factura.price_unit,
                                            'account_analytic_id': linea_albaran.analytic_account_id.id,
                                            'account_id': 357,
                                            'invoice_line_tax_ids': [(6, 0, tax_ids)]
                                        }
                                factura_act = http.request.env['account.invoice.line'].create(linea_devolucion)
                            factura._onchange_invoice_line_ids()
                            factura._compute_amount()                     
                        else:
                            data_refund = 'refund'
                            http.request.env['account.invoice.refund'].genera_factura_rectificativa_desde_albaranes(factura, data_refund)

            response = {
                'successful': True,
                'message': 'Se ha validado la recepción satisfactoriamente',
                'error': ''
            }
           
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido validar la recepción',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # SOLO EJECUTAR CUANDO LA CANTIDAD NORMAL Y LA CANTIDAD HECHA NO SEAN LA MISMA (Y LA OPCION EN LA APP SEA "REALIZAR ENTREGA")
    # Endpoint (Actualizar el estado de una recepcion "Preparado" -> "Hecho") (Modelo: stock.picking) 
    @http.route('/api/update/parcial/reception', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def validar_parcial(self, **post):
        id_recepcion = int(post.get('id'))
       
        try:
            mi_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            mis_productos = http.request.env['stock.move'].search([('picking_id', '=', id_recepcion)])

            for producto in mis_productos:
                cant_original = producto['product_uom_qty']
                cant_hecha = producto['quantity_done']
                resto = cant_original - cant_hecha

                if resto > 0:
                    # 1r paso, actualizar el registro con cantidad hecha
                    actualiza_producto = http.request.env['stock.move'].search([('id', '=', producto['id'])]).write({
                        "product_uom_qty": cant_hecha,
                        "quantity_done": cant_hecha,
                    })

                    # 2n paso, crear nueva recepcion con datos de la anterior
                    nueva_recepcion = http.request.env['stock.picking'].create({
                        "location_dest_id": mi_recepcion[0].location_dest_id.id,
                        "partner_id": mi_recepcion[0].partner_id.id,
                        "group_id": mi_recepcion[0].group_id.id,
                        "picking_type_id": mi_recepcion[0].picking_type_id.id,
                        "scheduled_date": str(mi_recepcion[0].scheduled_date),
                        # "origin": "Entrega parcial de " + str(mi_recepcion[0].name),
                        "origin": mi_recepcion[0].origin,
                        "location_id": mi_recepcion[0].location_id.id,
                        "backorder_id": mi_recepcion[0].id,
                    })
                    # 3r paso, crear el producto de la nueva recepcion
                    re_id = nueva_recepcion[0].id
                    
                    nuevo_producto = http.request.env['stock.move'].create({
                        "picking_id": re_id,
                        "product_id": producto['product_id'].id,
                        "product_uom_qty": resto,
                        "product_uom": producto['product_uom'].id,
                        "name": producto['name'],
                        "location_id": producto['location_id'].id,
                        "location_dest_id": producto[0].location_dest_id.id,
                    })
                   
                    nueva_recepcion.action_confirm()
                
                elif resto < 0:
                    actualiza_producto_mayor = http.request.env['stock.move'].search([('id', '=', producto['id'])]).write({
                        "product_uom_qty": cant_hecha,
                        "quantity_done": cant_hecha,
                    })
                    _logger.info('Actualiza la cantidad correctamente')

            response = {
                'successful': True,
                'message': 'Se ha validado la recepción parcial satisfactoriamente',
                'error': ''
            }
        
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido validar la recepción parcial',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Actualizar el estado de una recepcion "Borrador" -> "Cancelada") (Modelo: stock.picking)
    @http.route('/api/cancel/reception', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def cancelar_recepcion(self, **post):
        id_recepcion = int(post.get('id'))

        try: 
            mi_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            mi_recepcion.action_cancel()
            
            response = {
                'successful': True,
                'message': 'Se ha cancelado la recepción satisfactoriamente',
                'error': ''
            }
            
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido cancelar la recepción',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Devuelve una recepcion) (Modelo: stock.picking)
    @http.route('/api/update/return/reception', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def devolver_recepcion(self, **post):
        id_recepcion = int(post.get('reception'))
        
        try:
            datos_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            datos_productos_recepcion = http.request.env['stock.move'].search([('picking_id', '=', id_recepcion)])
            
            mi_almacen = datos_recepcion[0].picking_type_id.warehouse_id.id
            tipo_localizacion = http.request.env['stock.picking.type'].search([('warehouse_id', '=', mi_almacen), ('name', '=', 'Órdenes de entrega')])
            nuevo_picking_type_id = tipo_localizacion[0].id
            
            nueva_devolucion = http.request.env['stock.picking'].create({
                "origin": "Retorno de " + str(datos_recepcion[0].name),
                "picking_type_id": nuevo_picking_type_id,
                "group_id": datos_recepcion[0].group_id.id,
                "date": str(datos_recepcion[0].date),
                "location_id": datos_recepcion[0].location_dest_id.id,
                "location_dest_id": datos_recepcion[0].location_id.id,
                "partner_id": datos_recepcion[0].partner_id.id,
            })

            for producto in datos_productos_recepcion:
                nuevo_producto = http.request.env['stock.move'].create({
                    "picking_id": nueva_devolucion[0].id,
                    "date": str(producto['date']),
                    "product_id": producto['product_id'].id,
                    "product_uom_qty": producto['product_uom_qty'],
                    "product_uom": producto['product_uom'].id,
                    "name": producto['name'],
                    "location_id": producto['location_dest_id'].id,
                    "location_dest_id": producto['location_id'].id,
                    "origin_returned_move_id": producto['id'],
                })

                nueva_devolucion.action_confirm()
                nueva_devolucion.action_assign()

            response = {'successful': True, 'message': 'Se ha creado una devolución satisfactoriamente', 'error': ''}
            
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido crear la devolución', 'error': str(e)}
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Comprobar si existe una orden de devolucion asociada a una recepcion hecha)
    @http.route('/api/exists/return', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def comprobar_devolucion_existente(self, **post):
        id_recepcion = int(post.get('reception'))

        try:
            mi_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            cadena_formateada = "Retorno de " + str(mi_recepcion[0].name)

            buscar_devolucion = http.request.env['stock.picking'].search([('origin', '=', cadena_formateada)])

            if len(buscar_devolucion) > 0:
                response = {'successful': True, 'message': 'Existe una devolución asociada a esta recepción', 'error': '', 'exists': True}
            else:
                response = {'successful': True, 'message': 'No existe una devolución asociada a esta recepción', 'error': '', 'exists': False}
                
        except Exception as e:
            objeto = {'successful': False, 'message': 'No se ha podido verificar si existe la devolcuión de esta recepción', 'error': str(e)}
        
        response = json.dumps(response)
        return Response(response, content_type='application/json;charset=utf-8', status = 200)

    # SOLO EJECUTAR CUANDO LA RECEPCION NO SEA ORIGINAL (ORIGINAL = FALSE). ESTE METODO SECRETAMENTE ASIGNARA EL LOTE NUEVO
    # Endpoint (Asignar nuevo lote a recepcion parcial (No original) y tenerlo creado en la base de datos)
    @http.route('/api/parcial/reception/lot/assign', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def asignar_lote_recepcion_parcial(self, **post):
        id_recepcion = int(post.get('reception'))
        
        # Aqui va la logica de sacar el nuevo lote
        try:
            mi_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])

            id_original = mi_recepcion[0].backorder_id.id
            

            productos_original = http.request.env['stock.move'].search([('picking_id', '=', id_original)])
            _logger.info('*************** Id primer producto ************** %s'%productos_original[0].id)

            linea_producto = http.request.env['stock.move.line'].search([('move_id', '=', productos_original[0].id)])
            lote_name = linea_producto[0].lot_id.name
            _logger.info('*************** Nombre lote ************** %s'%lote_name)

            if lote_name != False:
                lote_aux = lote_name.split('/')
                numero_lote = int(lote_aux[4]) + 1
                parte_aux = ""
                nombre_lote = ""
                if numero_lote < 10:
                    parte_aux = "0" + str(numero_lote)
                    nombre_lote = str(lote_aux[0]) + "/" + str(lote_aux[1]) + "/" + str(lote_aux[2]) + "/" + str(lote_aux[3]) + "/" + parte_aux
                else: 
                    nombre_lote = str(lote_aux[0]) + "/" + str(lote_aux[1]) + "/" + str(lote_aux[2]) + "/" + str(lote_aux[3]) + "/" + str(numero_lote)

                _logger.info('************ Nombre del nuevo lote ************ %s'%nombre_lote)

                mis_productos = http.request.env['stock.move'].search([('picking_id', '=', id_recepcion)])

                for producto in mis_productos:
                    line_id = producto['id']
                    product_id = producto['product_id'].id
                    mi_linea_de_lote = http.request.env['stock.move.line'].search([('move_id', '=', line_id)])
                    for linea in mi_linea_de_lote:
                        nuevo_lote = http.request.env['stock.production.lot'].create({
                            "name": nombre_lote,
                            "product_id": product_id,
                        })
                    
                        linea.write({
                            "lot_id": nuevo_lote[0].id,
                        })

                response = {
                    'successful': True,
                    'message': 'Se ha asignado el lote a los productos satisfactoriamente',
                    'error': ''
                }
            else:
                response = {
                    'successful': False,
                    'message': 'Ha ocurrido un problema con el lote de esta recepción',
                    'error': ''
                }
            
        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido asignar el lote a los productos de la recepcion',
                'error': str(e)
            }

            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # SOLO EJECUTAR CUANDO LA RECEPCION SEA ORIGINAL (ORIGINAL = TRUE) Y EJECUTAR SIEMPRE DESPUES DE RECEPCION PARCIAL. ESTE METODO SECRETAMENTE ASIGNARA EL LOTE NUEVO A LA ORDEN ORIGINAL
    # Endpoint (Añadir lote a la recepcion ORIGINAL)
    @http.route('/api/original/reception/lot/assign', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def asignar_lote_recepcion_original(self, **post):
        id_recepcion = int(post.get('reception'))
        almacen = int(post.get('almacen'))
        
        # Aqui va la logica de sacar el nuevo lote para la original
        try:
            productos = http.request.env['stock.move'].search([('picking_id', '=', id_recepcion)])
            
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', almacen)])
            al_stock = tipo_almacen[0].lot_stock_id.id
            ubicacion_padre = http.request.env['stock.location'].search([('id', '=', al_stock)])
            # Nombre del padre
            parent_name = ubicacion_padre[0].location_id.name

            productos = http.request.env['stock.move'].search([('picking_id', '=', id_recepcion)])
            # Parte de la fecha de hoy
            hoy = str(date.today().strftime("%d/%m/%Y"))

            listado_lotes = http.request.env['stock.production.lot'].search([], order="id desc")
            
            encontrado = False
            numero_lote = ""
            fecha_lote = ""
            for lote in listado_lotes:
                array_nombre = lote['name'].split('/')
                if len(array_nombre)== 5:
                    if array_nombre[3] == parent_name:
                        encontrado = True
                        numero_lote = array_nombre[4]
                        fecha_lote = array_nombre[0] + '/' + array_nombre[1] + '/' + array_nombre[2]
                        break

            nombre_lote = ""

            if encontrado == True:
                if fecha_lote == hoy: 
                    numero_real = int(numero_lote)
                    numero_real += 1
                    nombre_lote = fecha_lote + '/' + parent_name + '/' + str(numero_real)
                else: 
                    numero_real = "01"
                    nombre_lote = hoy + '/' + parent_name + '/' + numero_real
            else:
                numero_real = "01"
                nombre_lote = hoy + '/' + parent_name + '/' + numero_real
            
            for producto in productos:
                line_id = producto['id']
                product_id = producto['product_id'].id
                mi_linea_de_lote = http.request.env['stock.move.line'].search([('move_id', '=', line_id)])
                for linea in mi_linea_de_lote:
                    nuevo_lote = http.request.env['stock.production.lot'].create({
                        "name": nombre_lote,
                        "product_id": product_id,
                    })
                    _logger.info('Lote creado')
                    linea.write({
                        "lot_id": nuevo_lote[0].id,
                    })
                    _logger.info('Linea actualizada')

            response = {'successful': True, 'message': 'Se ha asignado el lote a los productos de la recepción satisfactoriamente', 'error': ''}
           
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido asignar el lote a los productos de la recepcion', 'error': str(e)}
        
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)
    
    # Endpoint (Actualizar datos del producto de la recepcion)
    @http.route('/api/update/reception/product/data', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_datos_producto_recepcion(self, **post):
        products_id = int(post.get('products')).split('-')
        lots = str(post.get('lots')).split('-')
        dates = str(post.get('dates')).split('-')

        try:
            for i in range(len(products_id)):
                aux = dates[i].split('/')
                fecha_formateada = aux[-1] + '-' + aux[1] + '-' + aux[0]
           
                linea_producto = http.request.env['stock.move'].search([('id', '=', products_id[i])]).write({
                    "lote_prov": str(lots[i]),
                    "fecha_caducidadd": str(fecha_formateada),
                })
                response = {
                    'successful': True,
                    'message': 'Se han actualizado los datos del producto satisfactoriamente',
                    'error': ''
                }

        except Exception as e:
            response = {
                'successful': False,
                'message': 'No se ha podido actualizar los datos del producto',
                'error': str(e)
            }
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # EJECUTAR PARA ASIGNAR LOS LOTES EN LAS RECEPCIONES (TANTO ORIGINALES COMO PARCIALES) 
    # ******Pendiente de pruebas******
    @http.route('/api/reception/lot/assign', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def asignar_lote_recepcion(self, **post):
        id_recepcion = int(post.get('reception'))
        almacen = int(post.get('almacen'))

        # Aqui va la logica de sacar el numero de lote, para asignarlo en la recepción
        try:
            # De aqui se saca el nombre (Se necesita el numero en el nombre)
            datos_recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            nombre = datos_recepcion[0].name
            _logger.info('********* Nombre de la recepcion ********* %s' %nombre)
            # Aqui se saca el listado de productos de la recepcion
            productos = http.request.env['stock.move'].search([('picking_id', '=', id_recepcion)])
            
            # Aqui va todo lo de sacar la parte del nombre de la ubicacion del almacen, para el lote
            tipo_almacen = http.request.env['stock.warehouse'].search([('id', '=', almacen)])
            al_stock = tipo_almacen[0].lot_stock_id.id
            ubicacion_padre = http.request.env['stock.location'].search([('id', '=', al_stock)])
            # Nombre de la ubicacion padre
            parent_name = ubicacion_padre[0].location_id.name

            # Parte de la fecha de hoy
            hoy = str(date.today().strftime("%d/%m/%Y"))

            # Sacar el numero del nombre de la recepcion
            array_nombre = nombre.split('/')
            aux = int(array_nombre[2])
            numero_nombre = str(aux)

            # Aqui ya tenemos el lote formado
            nombre_lote = hoy + '/' + parent_name + '/' + numero_nombre
            _logger.info('************ Lote ************ %s' %nombre_lote)

            # Recorremos los productos
            for producto in productos:
                line_id = producto['id']
                product_id = producto['product_id'].id
                fecha_cad = producto['fecha_caducidadd']
                # Tambien recorremos la linea de lote, y procedemos a asignar el lote. Hay que tener en cuenta si este tiene fecha de caducidad
                mi_linea_de_lote = http.request.env['stock.move.line'].search([('move_id', '=', line_id)])
                for linea in mi_linea_de_lote:
                    if fecha_cad:
                        fecha_total = str(fecha_cad) + " 00:00:00"
                        nuevo_lote = http.request.env['stock.production.lot'].create({
                            "name": nombre_lote,
                            "product_id": product_id,
                            "life_date": fecha_total,
                        })
                        _logger.info('Lote creado')
                        linea.write({
                            "lot_id": nuevo_lote[0].id,
                        })
                        _logger.info('Linea actualizada')
                    else:
                        nuevo_lote = http.request.env['stock.production.lot'].create({
                            "name": nombre_lote,
                            "product_id": product_id,
                        })
                        _logger.info('Lote creado')
                        linea.write({
                            "lot_id": nuevo_lote[0].id,
                        })
                        _logger.info('Linea actualizada')
            
            response = {'successful': True, 'message': 'Se ha asignado el lote al producto satisfactoriamente', 'error': ''}
            
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido asignar el lote a la recepcion', 'error': str(e)}
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # SOLO EJECUTAR CUANDO EN UNA RECEPCIÓN CON DIFERENTES CANTIDADES, EL USUARIO DIGA QUE NO QUIERE ENTREGA PARCIAL
    # Endpoint (Actualizar el estado de una recepcion "Proceso" -> "Hecho") (Modelo: stock.picking) 
    @http.route('/api/update/no/parcial/reception', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def validar_entrega_no_parcial(self, **post):
        id_recepcion = int(post.get('reception'))

        try: 
            mis_productos = http.request.env['stock.move'].search([('picking_id', '=', id_recepcion)])
        
            for producto in mis_productos:
                cant_original = producto['product_uom_qty']
                cant_hecha = producto['quantity_done']
                resto = cant_original - cant_hecha

                if resto != 0:
                    # Actualizar el registro con cantidad hecha
                    actualiza_producto = http.request.env['stock.move'].search([('id', '=', producto['id'])]).write({
                        "product_uom_qty": cant_hecha,
                        "quantity_done": cant_hecha,
                    })
                    _logger.info('Actualiza la cantidad correctamente')
                else: 
                    pass
                    
            response = {'successful': True, 'message': 'Se han actualizado de la recepción las cantidades satisfactoriamente', 'error': ''}
          
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido crear una entrega no parcial de esta recepción', 'error': str(e)}
            _logger.error(str(e))
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Actualizar campo "Albarán de proveedor" en la recepción)
    @http.route('/api/update/provider/reception', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def actualizar_albaran_de_proveedor_recepcion(self, **post):
        id_recepcion = int(post.get('reception'))
        albaran_proveedor = post.get('albcode')

        try:
            recepcion = http.request.env['stock.picking'].search([('id', '=', id_recepcion)])
            recepcion.write({
                'albaran_proveedor': albaran_proveedor,
            })
            response = {'successful': True, 'message': 'Se ha actualizado el albarán del proveedor satisfactoriamente', 'error': ''}
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido actualizar el albarán de proveedor', 'error': str(e)}
            _logger.error(str(e))

        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)