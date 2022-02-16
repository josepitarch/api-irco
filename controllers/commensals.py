# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response, request
import datetime
from datetime import date
import calendar
import json
import logging

_logger = logging.getLogger(__name__)

CORS = '*'

class Commensals(http.Controller):

    # Endpoint (Obtener las dietas disponibles de los pedidos de catering del cliente) (Modelo: irco.menu.clientes)
    @http.route('/api/catering/diets/<int:company>', type='http', auth='user', methods=['GET'])
    def obtener_dietas_pedidos_catering(self, company, **kw):
        try:
            listado_catering = http.request.env['irco.menu.clientes'].search([('partner_id', '=', company)])
            response = list()

            for pedido in listado_catering:
                current_order = {
                    "id": pedido['tipo_menu_ids'].id,
                    "name": pedido['tipo_menu_ids'].name,                
                }
                response.append(current_order)
            
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se han podido obtener las dietas para la compañía asignada a este usuario',
                    'error': str(e)
                }
            }]
        
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener todas las dietas posibles) (Modelo: irco.dietas)
    @http.route('/api/all/diets', type='http', auth='user', methods=['GET'])
    def obtener_dietas(self, **kw):
        try:
            diets = http.request.env['irco.dietas'].search([('mostrar', '=', True)])
            response = list()

            for diet in diets:
                current_diet = {
                    "id": diet['id'],
                    "name": diet['name'],
                }
                
                response.append(current_diet)
        
        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se han podido obtener las dietas existentes',
                    'error': str(e)
                }
            }]
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Crear pedido manual de catering) (Modelo: irco.pedidos.catering.manual)
    @http.route('/api/create/catering/order', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_pedido_catering(self, **post):
        fecha = post.get('date')
        id_cliente = int(post.get('client'))

        aux = fecha.split('/')
        fecha_formateada = aux[-1] + '-' + aux[1] + '-' + aux[0]
        
        try:
            nuevo_pedido = http.request.env['irco.pedidos.catering.manual'].create({
                "fecha_servicio": str(fecha_formateada),
                "partner_id": id_cliente,
            })

            response = {
                'successful': True,
                'message': nuevo_pedido[0].id,
                'error': ''
            }
           
        except Exception as e:
            response = {'successful': False, 'message': 'No se ha podido crear el pedido de catering', 'error': str(e) }
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)  

    # Endpoint (Crear lineas del pedido de catering) (Modelo: irco.pedidos.catering.manual.detalle)
    @http.route('/api/create/catering/order/line', type='http', auth='user', cors=CORS, methods=['POST'], csrf=False)
    def crear_lineas_pedido_catering(self, **post):
        date = post.get('date')
        id_cliente = int(post.get('company'))
        diets_id = str(post.get('diets')).split('-')
        quantitys = str(post.get('quantitys')).split('-')

        aux = date.split('/')
        fecha_formateada = aux[-1] + '-' + aux[1] + '-' + aux[0]

        try:
            lineas = list()
            for i in range(len(diets_id)):
                if int(quantitys[i]) > 0:
                    lineas.append((0, 0, { "menu_id": diets_id[i], "cantidad_pedida": quantitys[i] }))
            
            nuevo_pedido = http.request.env['irco.pedidos.catering.manual'].create({
                "fecha_servicio": str(fecha_formateada),
                "partner_id": id_cliente,
                "menus_ids": lineas,
            })
                  
            response = {'successful': True, 'message': 'Se han añadido los menús satisfactoriamente', 'error': ''}
            
        except Exception as e:
            response = {'successful': False, 'message': 'No se han podido añadir los menús', 'error': str(e)}
        
        response = json.dumps(response)

        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener pedidos de venta de comensales) (TODOS LOS DEL USUARIO) (Modelo: sale.order / sale.order.line)
    @http.route('/api/catering/all/sale/orders/<int:partnerid>', type='http', auth='user', methods=['GET'])
    def obtener_todos_pedidos_venta_catering(self, partnerid, **kw):
        try:
            listado_pedidos = http.request.env['sale.order'].search([('partner_id', '=', partnerid), ('state', '!=', 'cancel')], order="fecha_pedido desc")
            
            response=[]
            for pedido in listado_pedidos:
                id_pedido = pedido['id']

                lineas_pedido = http.request.env['sale.order.line'].search([('order_id', '=', id_pedido), ('display_type', '=', 'line_section')])
                array_lineas = []
                for linea in lineas_pedido:
                    datos_linea = {
                        'name': linea['name'],
                        'quantity': linea['quantity'],
                        'uom': linea['uom'],
                        'menu_price': linea['menu_price'],
                        'tax': linea['tax'],
                        'total': linea['section_total']
                    }
                    array_lineas.append(datos_linea)

                datos_pedido = {
                    'name': pedido['name'],
                    'client_name': pedido['partner_id'].name,
                    'date': str(pedido['fecha_pedido'].strftime("%d/%m/%Y")),
                    'order_lines': array_lineas,
                }
                response.append(datos_pedido)

        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se han podido obtener los pedidos de venta para este cliente',
                    'error': str(e)
                }
            }]
        
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)

    # Endpoint (Obtener pedidos de venta de comensales) (DE UN MES ESPECÍFICO) (Modelo: sale.order / sale.order.line)
    @http.route('/api/catering/sale/orders/<int:year>/<int:month>/<int:partnerid>', type='http', auth='user', methods=['GET'])
    def obtener_pedidos_venta_catering_mes_actual(self, year, month, partnerid, **kw):
        try:
            
            response=[]

            tupla_dias_mes = calendar.monthrange(year, month)
            dias_mes = tupla_dias_mes[1]
            primer_dia_mes = str(year) + '-' + str(month) + '-01'
            ultimo_dia_mes = str(year) + '-' + str(month) + '-' + str(dias_mes)
            
            listado_pedidos = http.request.env['sale.order'].search([('partner_id', '=', partnerid), ('state', '!=', 'cancel'), ('fecha_pedido', '>=', primer_dia_mes), ('fecha_pedido', '<=', ultimo_dia_mes), ('pedido_catering_manual_id', '!=', False)], order="fecha_pedido desc")
            
            once_pedidos = dict()
            for pedido in listado_pedidos:
                date = str(pedido['fecha_pedido'].strftime("%d/%m/%Y"))
                client_name = pedido['partner_id'].name
                value = once_pedidos.get(date, None)

                if value is None:
                    once_pedidos[date] = (pedido['id'], pedido['name'], client_name)
                else:
                    if pedido['name'][2:] > value[1][2:]:
                        once_pedidos[date] = (pedido['id'], pedido['name'], client_name)

            for key in once_pedidos:
                lineas_pedido = http.request.env['sale.order.line'].search([('order_id', '=', once_pedidos[key][0]), ('display_type', '=', 'line_section')])
                
                array_lineas = list()
                for linea in lineas_pedido:
                    datos_linea = {
                        'name': linea['name'],
                        'quantity': linea['quantity'],
                        'uom': linea['uom'],
                        'menu_price': linea['menu_price'],
                        'tax': linea['tax'],
                        'total': linea['section_total']
                    }
                    array_lineas.append(datos_linea)

                datos_pedido = {
                    'name': once_pedidos[key][1],
                    'client_name': once_pedidos[key][2],
                    'date': key,
                    'order_lines': array_lineas,
                }

                response.append(datos_pedido)

        except Exception as e:
            response = [{
                'message': {
                    'successful': False,
                    'message': 'No se han podido obtener los pedidos de venta para este cliente',
                    'error': str(e)
                }
            }]
        
        response = json.dumps(response)
        return Response(response, content_type = 'application/json;charset=utf-8', status = 200)