import io
import os
import json
from decimal import *

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse, FileResponse
from django.core.handlers.wsgi import WSGIRequest
from django.db import connection

from reportlab.pdfgen import canvas

from ..base_plugin import BasePlugin

from saleor.order import models as order_models
from saleor.product import models as p_models
from saleor.warehouse import models as warehouse_models

from . import report as r

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

            if request_dict['action'] == 'SUBMIT_RETURN':
                response_file, message = self.save_return(request_dict)
                if response_file != None:
                    j = response_file
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

            j = JsonResponse(data={'error': message}, status=400)
            j["Access-Control-Allow-Origin"] = "*"
            return j

        j = JsonResponse(data={'error': 'action not found'}, status=400)
        j["Access-Control-Allow-Origin"] = "*"
        return j


    def save_return(self, request_dict):
        print(json.dumps(request_dict, sort_keys=True, indent=4))

        onum = int(request_dict["orderNumber"])
        i = 1
        order_i = None
        order_l = order_models.Order.objects.all().order_by("created")
        for o in order_l:
            if onum == i:
                order_i = o
                break
            i = i + 1


        cursor = connection.cursor()
        cursor.execute('''SELECT * FROM account_address WHERE id = ''' + str(order_i.shipping_address_id))
        user_info = dictfetchall(cursor)[0]

        r.generate_report(
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


    def get_order(self, request_dict):
        cursor = connection.cursor()

        try:
            onum = int(request_dict['orderNumber'])
        except Exception:
            return None, 'Invalid Order Number'

        # find the order by number
        i = 1
        order_i = None
        order_l = order_models.Order.objects.all().order_by("created")
        for o in order_l:
            if onum == i:
                order_i = o
                break
            i = i + 1

        if order_i == None:
            return None, 'Invalid Order Number'

        # check date window, currently set to 35 days, need to get delivered date from USPS/UPS
        t = pytz.UTC.localize(datetime.today())
        w = t - timedelta(days=35)
        d = order_i.created
        if not w <= d <= t:
            return None, 'Order is outside window'

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
            image = 'https://' + settings.AWS_MEDIA_BUCKET_NAME + '.s3.amazonaws.com/' + str(line.variant.get_first_image().image)

            prod = p_models.Product.objects.get(id=line.variant.product.id)
            prod_variants = p_models.ProductVariant.objects.filter(product=prod)
            variant_attrs = p_models.AttributeVariant.objects.filter(product_type=prod.product_type)
            
            
            exchangeable_variant_attrs = []
            exchangable_variants = []
            sku_quantity_map = {}

            exchangeable_assignments_list = []

            for v in prod_variants:
                s = warehouse_models.Stock.objects.filter(product_variant=v)[0]
                
                cursor.execute('''SELECT * FROM product_assignedvariantattribute where variant_id =''' + str(v.id))
                for c in dictfetchall(cursor):
                    exchangeable_assignments_list.append(c['id'])

                exchangable_variants.append({
                    'id': v.id,
                    'sku': v.sku,
                    'name': v.name,
                    'price_amount': v.price_amount,
                    'currency': v.currency,
                    'quantity_available': s.quantity
                })
                sku_quantity_map[v.sku] = s.quantity

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
