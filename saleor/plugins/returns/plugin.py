from .credit import send_credit
import io
import os
import json
from decimal import *
from datetime import datetime, timezone

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse, FileResponse
from django.core.handlers.wsgi import WSGIRequest
from django.db import connection
from django.utils.timezone import now

from reportlab.pdfgen import canvas

from ..base_plugin import BasePlugin

from saleor.returns import models as return_models
from saleor.order import models as order_models
from saleor.product import models as p_models
from saleor.warehouse import models as warehouse_models

from . import report as re

import pytz
from datetime import datetime, timedelta

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [ dict(zip(columns, row)) for row in cursor.fetchall() ]

class ReturnsPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.returns"
    PLUGIN_NAME = "Returns Plugin"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Returns module endpoint"
    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        if path == '/webhook':
            request_dict = json.loads(request.body.decode('utf-8'))

            if request_dict['action'] == 'RETRIEVE_ORDER':
                response_dict, message = self.get_order(request_dict)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

            if request_dict['action'] == 'RETRIEVE_ORDER_FORM':
                response_file, message = self.get_form(request_dict)
                if response_file != None:
                    j = response_file
                    j["Access-Contol-Allow-Origin"] = "*"
                    return j

            if request_dict['action'] == 'SUBMIT_RETURN':
                response_file, message = self.save_return(request_dict)
                if response_file != None:
                    j = response_file
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

            if request_dict['action'] == 'RETRIEVE_RETURN':
                response_dict, message = self.get_return(request_dict)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

            if request_dict['action'] == 'RETRIEVE_RETURNS':
                response_dict, message = self.get_returns(request_dict)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

            if request_dict['action'] == 'PROCESS_RETURN':
                response_dict, message = self.process_return(request_dict)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

            j = JsonResponse(data={'error': message}, status=400)
            j["Access-Control-Allow-Origin"] = "*"
            return j

        j = JsonResponse(data={'error': 'action not found'}, status=400)
        j["Access-Control-Allow-Origin"] = "*"
        return j

    def get_form(self, request_dict):
        onum = int(request_dict["orderNumber"])
        if order_models.Order.objects.filter(pk=onum).exists():
            order_i = order_models.Order.objects.get(pk=onum)
        else:
            return None, 'Invalid Order Number'
        cursor = connection.cursor()
        cursor.execute('''SELECT * FROM account_address WHERE id = ''' + str(order_i.shipping_address_id))
        user_info = dictfetchall(cursor)[0]
        re.generate_report(
            order_number = str(order_i.id),
            name = str(user_info['first_name']) + ' ' + str(user_info['last_name']),
            address = str(user_info['street_address_1']),
            city = str(user_info['city']),
            country_area = str(user_info['country_area']),
            country = str(user_info['country']),
            zipcode = str(user_info['postal_code']),
            email = str(order_i.user_email),
            phone = str(user_info['phone'])
        )
        return FileResponse(open('/var/www/html/saleor/form.pdf', 'rb')), 'Successful'


    def process_return(self, request_dict):
        if 'returnsProcessKeyFF' not in request_dict:
            return None, 'Authentication Failed'
        if request_dict['returnsProcessKeyFF'] != 'av08er7vbo3ihjv5!@rblkjedfv0e8qr':
            return None, 'Authentication Failed'
        try:
            for i in range(len(request_dict['process_lines'])):
                l = return_models.ReturnLine.objects.get(id=request_dict['process_lines'][i]['id'])
                l.accepted_quantity = l.accepted_quantity + request_dict['process_lines'][i]['quantity_accepted']
                l.reject_quantity = l.reject_quantity + request_dict['process_lines'][i]['quantity_rejected']
                l.exchange_quantity = l.exchange_quantity + request_dict['process_lines'][i]['quantity_exchange']
                l.returned_to_stock_quantity = l.returned_to_stock_quantity + request_dict['process_lines'][i]['quantity_restock']
                l.rejected_reason = request_dict['process_lines'][i]['reject_reason']
                l.save()
        except Exception as e:
            return None, e
        r = {
            'return_info' : {
                'order_number' : request_dict['orderNumber']
            }
        }

        send_credit(request_dict['process_lines'])

        return r, 'Successful'


    def get_return(self, request_dict):
        if 'returnsProcessKeyFF' not in request_dict:
            return None, 'Authentication Failed'
        if request_dict['returnsProcessKeyFF'] != 'av08er7vbo3ihjv5!@rblkjedfv0e8qr':
            return None, 'Authentication Failed'
        try:
            onum = int(request_dict["code"].split('|', 1)[1])
        except Exception:
            return None, 'Invalid Code'

        if order_models.Order.objects.filter(pk=onum).exists():
            order_i = order_models.Order.objects.get(pk=onum)
        else:
            return None, 'Invalid Order Number'

        ffz = str(datetime.now(timezone.utc) - order_models.Fulfillment.objects.get(order_id=order_i.id).created).split(' ')
        if len(ffz) == 3:
            fulfillment_elapse = ffz[0]
        else:
            fulfillment_elapse = 0
        cursor = connection.cursor()
        cursor.execute('''SELECT * from account_address WHERE id = ''' + str(order_i.shipping_address_id))
        user_info = dictfetchall(cursor)[0]
        return_headers = return_models.ReturnHeader.objects.filter(order_id=order_i.id)
        rh_id_list = []
        for i in range(len(return_headers)):
            rh_id_list.append(return_headers[i].id)
        return_lines = return_models.ReturnLine.objects.filter(return_header_id__in=rh_id_list)
        lines = []
        for line in return_lines:
            exchangeStyle = None
            exchangeColor = None
            exchangeSize = None
            if line.return_type == 'exchange':
                exchangeStyle = line.exchange_sku.split('_')[0]
                exchangeColor = line.exchange_sku.split('_')[1]
                exchangeSize = line.exchange_sku.split('_')[2]
            style = line.return_sku.split('_')[0]
            color = line.return_sku.split('_')[1]
            size = line.return_sku.split('_')[2]
            lines.append({
                'id': line.id,
                'rh_id': line.return_header_id,
                'return_sku': line.return_sku,
                'return_type': line.return_type,
                'exchange_sku': line.exchange_sku,
                'quantity_returned': line.quantity_returned,
                'quantity_accepted': line.accepted_quantity,
                'quantity_rejected': line.reject_quantity,
                'color': color,
                'size': size,
                'style': style,
                'exchangeStyle': exchangeStyle,
                'exchangeColor': exchangeColor,
                'exchangeSize': exchangeSize,
                'return_reason': line.return_reason
            })

        r = {
                'return': {
                    'user_info': {
                        'name': str(user_info['first_name']) + ' ' + str(user_info['last_name']),
                        'address': str(user_info['street_address_1']),
                        'city': str(user_info['city']),
                        'country_area': str(user_info['country_area']),
                        'country': str(user_info['country']),
                        'zipcode': str(user_info['postal_code']),
                        'email': str(order_i.user_email),
                        'phone': str(user_info['phone']),
                    },
                    'order_number': str(order_i.id),
                    'fulfillment_elapse' : str(fulfillment_elapse),
                    'lines': lines
                }
            }
        return r, 'Successful'


    def get_returns(self, request_dict):
        if 'returnsProcessKeyFF' not in request_dict:
            return None, 'Authentication Failed'
        if request_dict['returnsProcessKeyFF'] != 'av08er7vbo3ihjv5!@rblkjedfv0e8qr':
            return None, 'Authentication Failed'

        qry = '''
select oh.id as "Order Number",
        concat(aa.first_name, ' ', aa.last_name) as "ShipTo Name",
        date(rh.date_submitted) as "Date Submitted",
        oh.user_email as "Email",
        rh."comment" as "Comment",
        string_agg(rl.return_type, ' ') as "Return/Exchange Type",
        sum(rl.quantity_returned) as "Return Qty",
        sum(rl.exchange_quantity) as "Exchange Qty"
from returns_returnline rl
        left outer join returns_returnheader rh on rh.id = rl.return_header_id
        left outer join order_order oh on oh.id = rh.order_id
        left outer join account_address aa on aa.id = oh.shipping_address_id
where (rl.quantity_returned - (rl.accepted_quantity + rl.reject_quantity)) > 0
group by oh.id, rh."comment", rh.date_submitted, aa.first_name, aa.last_name
order by rh.date_submitted asc;
        '''

        cursor = connection.cursor()
        cursor.execute(qry)
        all_unproc_returns = dictfetchall(cursor)
        rt_list = []
        for rt in all_unproc_returns:
            rt_list.append({
                'order_number': str(rt['Order Number']),
                'ship_to_name': str(rt['ShipTo Name']),
                'date_submitted': str(rt['Date Submitted']),
                'comment': str(rt['Comment']),
                'email': str(rt['Email']),
                'return_type': str(rt['Return/Exchange Type']),
                'return_qty': str(rt['Return Qty']),
                'exchange_qty': str(rt['Exchange Qty']),
            })

        return {'returns': rt_list}, 'Successful'


    def save_return(self, request_dict):
        comment = request_dict["additionalComments"]
        onum = int(request_dict["orderNumber"])

        if order_models.Order.objects.filter(pk=onum).exists():
            order_i = order_models.Order.objects.get(pk=onum)
        else:
            return None, 'Invalid Order Number'

        return_header = return_models.ReturnHeader.objects.create(
             order_id=onum,
             comment=comment
        )

        ex_lines = []

        for i in range(len(request_dict["return_lines"])):
            if request_dict["return_lines"][i]["exchangeSku"] != None:
                exchange_variant_id = p_models.ProductVariant.objects.get(sku=request_dict["return_lines"][i]["exchangeSku"]).id
            else:
                exchange_variant_id = None

            return_line = return_models.ReturnLine.objects.create(
                return_header_id = int(return_header.id),
                return_variant_id = int(request_dict["return_lines"][i]["returnVariantId"]),
                order_line_id = int(request_dict["return_lines"][i]["id"]),
                return_reason = request_dict["return_lines"][i]["reason"],
                quantity_returned = request_dict["return_lines"][i]["quantity"],
                return_type = request_dict["return_lines"][i]["returnType"].lower(),
                exchange_variant_id = exchange_variant_id,
                exchange_sku = request_dict["return_lines"][i]["exchangeSku"],
                return_sku = request_dict["return_lines"][i]["returnSku"]
            )

            line_zz = order_models.OrderLine.objects.get(id=int(request_dict["return_lines"][i]["id"]))

            if request_dict["return_lines"][i]["returnType"].lower() == 'exchange':
                request_dict["return_lines"][i]["line_instance"] = return_line
                request_dict["return_lines"][i]["order_line_instance"] = line_zz
                ex_lines.append(request_dict["return_lines"][i])

        cursor = connection.cursor()
        cursor.execute('''SELECT * FROM account_address WHERE id = ''' + str(order_i.shipping_address_id))
        user_info = dictfetchall(cursor)[0]

        # update meta to exhangeOrder=true

        # generate order lines

        re.generate_report(
            order_number = str(order_i.id),
            name = str(user_info['first_name']) + ' ' + str(user_info['last_name']),
            address = str(user_info['street_address_1']),
            city = str(user_info['city']),
            country_area = str(user_info['country_area']),
            country = str(user_info['country']),
            zipcode = str(user_info['postal_code']),
            email = str(order_i.user_email),
            phone = str(user_info['phone'])
        )

        if(len(ex_lines) > 0):
            order_i.metadata['exchangeOrder'] = 'true'
            order_i.metadata['exchangeOrderId'] = str(order_i.id)
            order_i.metadata['processedToFrogfish'] = 'false'
            order_i.pk = None
            order_i.token = None
            order_i.created = now()
            order_i.status = 'unfulfilled'

            order_i.shipping_price_net_amount = order_i.shipping_price_net_amount - order_i.shipping_price_net_amount
            order_i.shipping_price_net = order_i.shipping_price_net - order_i.shipping_price_net
            order_i.shipping_price_gross_amount = order_i.shipping_price_gross_amount = order_i.shipping_price_gross_amount
            order_i.shipping_price_gross = order_i.shipping_price_gross - order_i.shipping_price_gross
            order_i.shipping_price = order_i.shipping_price - order_i.shipping_price
            order_i.total_net_amount = order_i.total_net_amount - order_i.total_net_amount
            order_i.total_net = order_i.total_net - order_i.total_net
            order_i.total_gross_amount = order_i.total_gross_amount - order_i.total_gross_amount
            order_i.total_gross = order_i.total_gross - order_i.total_gross
            order_i.total = order_i.total - order_i.total

            order_i.save()

            for ex_line in ex_lines:
                exchange_variant_id = p_models.ProductVariant.objects.get(sku=ex_line["exchangeSku"]).id
                vz = p_models.ProductVariant.objects.get(id=exchange_variant_id)
                o_line_instance = ex_line['order_line_instance']
                lz = order_models.OrderLine.objects.create(
                    order_id=order_i.id,
                    variant=vz,
                    product_name=vz.product.name,
                    variant_name=vz.name,
                    product_sku=vz.sku,
                    is_shipping_required=True,
                    quantity=ex_line["quantity"],
                    unit_price_net_amount=o_line_instance.unit_price_net_amount,
                    unit_price_net=o_line_instance.unit_price_net,
                    unit_price_gross_amount=o_line_instance.unit_price_gross_amount,
                    unit_price_gross=o_line_instance.unit_price_gross,
                    unit_price=o_line_instance.unit_price,
                    tax_rate=o_line_instance.tax_rate
                )

        return FileResponse(open('/var/www/html/saleor/form.pdf', 'rb')), 'Successful'


    def get_order(self, request_dict):
        cursor = connection.cursor()

        try:
            onum = int(request_dict['orderNumber'])
        except Exception:
            return None, 'Invalid Order Number'

        if order_models.Order.objects.filter(pk=onum).exists():
            order_i = order_models.Order.objects.get(pk=onum)
        else:
            return None, 'Invalid Order Number'

        t = pytz.UTC.localize(datetime.today())
        w = t - timedelta(days=35)
        d = order_i.created
        if not w <= d <= t:
            return None, 'Order is not eligible for return'

        s = order_i.shipping_address.postal_code == request_dict['zip']
        b = order_i.billing_address.postal_code == request_dict['zip']
        if not (s or b):
            return None, 'Invalid Zip Code'

        if not (order_i.user_email.lower() == request_dict['email'].lower()):
            return None, 'Invalid Information'

        order_lines = order_models.OrderLine.objects.filter(order=order_i)
        lines = []
        for line in order_lines:
            color = line.product_sku.split('_')[1]
            size = line.product_sku.split('_')[2]
            image_q = line.variant.images.filter(image__icontains=color)
            print(color)
            print(line.variant.get_first_color_image(color).image)

            image = 'https://' + settings.AWS_MEDIA_BUCKET_NAME + '.s3.amazonaws.com/' + str(line.variant.get_first_color_image(color).image)

            prod = p_models.Product.objects.get(id=line.variant.product.id)
            prod_variants = p_models.ProductVariant.objects.filter(product=prod)
            variant_attrs = p_models.AttributeVariant.objects.filter(product_type=prod.product_type)

            quantity_returned = 0
            returned_lines = return_models.ReturnLine.objects.filter(order_line_id=line.id)

            for returned_line in returned_lines:
                quantity_returned += returned_line.quantity_returned

            exchangeable_variant_attrs = []
            exchangable_variants = []
            sku_quantity_map = {}

            exchangeable_assignments_list = []

            for v in prod_variants:
                qty = 0
                if warehouse_models.Stock.objects.filter(product_variant=v).exists():
                    s = warehouse_models.Stock.objects.filter(product_variant=v)[0]
                    qty = s.quantity

                cursor.execute('''SELECT * FROM product_assignedvariantattribute where variant_id =''' + str(v.id))
                for c in dictfetchall(cursor):
                    exchangeable_assignments_list.append(c['id'])

                exchangable_variants.append({
                    'id': v.id,
                    'sku': v.sku,
                    'name': v.name,
                    'price_amount': v.price_amount,
                    'currency': v.currency,
                    'quantity_available': qty
                })
                sku_quantity_map[v.sku] = qty

            for va in variant_attrs:
                a_vals = p_models.AttributeValue.objects.filter(attribute=va.attribute)
                avs = []
                for z in a_vals:
                    run = False
                    cursor.execute('''SELECT * FROM product_assignedvariantattribute_values where attributevalue_id =''' + str(z.id))
                    for q in dictfetchall(cursor):
                        if q['assignedvariantattribute_id'] in exchangeable_assignments_list:
                            run= True
                    if run:
                        im = None
                        if va.attribute.slug == 'color':
                            im = 'https://' + settings.AWS_MEDIA_BUCKET_NAME + '.s3.amazonaws.com/products/' + z.slug.lower() + '.png'
                        avs.append({
                            'id': z.id,
                            'name': z.name,
                            'value': z.value,
                            'slug': z.slug,
                            'attribute':{
                                'id': z.attribute.id
                            },
                            'image': im
                        })
                exchangeable_variant_attrs.append({
                    'id': va.id,
                    'attribute': {
                        'id': va.attribute.id,
                        'name': va.attribute.name,
                        'slug': va.attribute.slug,
                        'available_in_grid': va.attribute.available_in_grid,
                        'visible_in_storefront': va.attribute.visible_in_storefront,
                        'is_variant_only': va.attribute.is_variant_only,
                        'values': avs,
                        'metadata': va.attribute.metadata
                    }
                })

            p_return = {
                'id': prod.id,
                'name': prod.name,
                'type': prod.product_type.id,
                'metadata': prod.product_type.metadata,
                'available_for_purchase': prod.available_for_purchase,
                'exchangeable_variant_attrs': exchangeable_variant_attrs,
                'exchangable_variants': exchangable_variants,
                'sku_quantity_map': sku_quantity_map
            }

            lines.append({
                'id': line.id,
                'variant': {
                    'id': line.variant.id
                },
                'product_name': line.product_name,
                'variant_name': line.variant_name,
                'product_sku': line.product_sku,
                'is_shipping_required': line.is_shipping_required,
                'quantity': line.quantity,
                'quantity_fulfilled': line.quantity_fulfilled,
                'quantity_returned': quantity_returned,
                'currency': line.currency,
                'unit_price_net_amount': line.unit_price_net_amount,
                'unit_price_gross_amount': line.unit_price_gross_amount,
                'tax_rate': line.tax_rate,
                'color': color,
                'size': size,
                'img': image,
                'product': p_return
            })

        r = {
            'order': {
                'id': order_i.id,
                'email': order_i.user_email,
                'date': str(order_i.created),
                'total_net_amount': order_i.total_net_amount,
                'total_gross_amount': order_i.total_gross_amount,
                'shipping_price_gross_amount': order_i.shipping_price_gross_amount,
                'shipping_price_net_amount': order_i.shipping_price_net_amount,
                'lines': lines
            }
        }

        return r, 'Successful'