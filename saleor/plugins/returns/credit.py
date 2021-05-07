
import json
from requests import Session
import json
import requests

import django
django.setup()

from saleor import settings

from saleor.returns import models as return_models
from saleor.order import models as order_models
from saleor.account import models as account_models

def send_credit(process_lines):
    print('sending credit to ff')
    print(settings.FROGFISH_API_TOKEN)
    print(settings.FROGFISH_API_URL)

    '''
    process_lines = [
        {
            "exchange_sku": None,
            "id": 39,
            "quantity_accepted": 2,
            "quantity_available": 3,
            "quantity_exchange": 0,
            "quantity_rejected": 1,
            "quantity_restock": 1,
            "return_sku": "3500_Nude_34C",
            "return_type": "refund",
            "rh_id": 22,
        }, {

            "exchange_sku": None,
            "id": 40,
            "quantity_accepted": 1,
            "quantity_available": 1,
            "quantity_exchange": 0,
            "quantity_rejected": 0,
            "quantity_restock": 1,
            "return_sku": "3500_Nude_34C",
            "return_type": "refund",
            "rh_id": 23,
        }
    ]
    '''


    item_list = []

    for line in process_lines:
        r_l = return_models.ReturnLine.objects.get(id=line['id'])
        o_l = order_models.OrderLine.objects.get(id=r_l.order_line_id)
        p_type = o_l.variant.product.product_type.slug
        sku = line["return_sku"]

        # ff size descriptions have commas
        if p_type == 'bras':
          split = sku.split('_')
          l = list(split[2])
          l.insert(2, ',')
          split[2] = "".join(l)
          sku = "_".join(split)

        line_obj = {
            "sku" : sku,
            "qty_returned" : str(r_l.quantity_returned),
            "qty_accepted" : str(line["quantity_accepted"]),
            "to_stock" : str(line["quantity_restock"]),
            "reason_name" : r_l.return_reason,
            "reason_name_rejected" : r_l.rejected_reason,
            "ammount" : str(o_l.unit_price_net_amount),
            "product_ammount" : str(o_l.unit_price_net_amount),
            "ticket" : None,
            "taxes" : [],
            "discounts" : [],
            "return_type": line["return_type"]
        }
        item_list.append(line_obj)

    r_h = return_models.ReturnHeader.objects.get(id=process_lines[0]["rh_id"])
    o_h = order_models.Order.objects.get(id=r_h.order.id)
    o_fulfillment = order_models.Fulfillment.objects.get(order=o_h)
    shipping_address = account_models.Address.objects.get(id=o_h.shipping_address.id)
    billing_address = account_models.Address.objects.get(id=o_h.billing_address.id)
    r_l = return_models.ReturnLine.objects.get(id=process_lines[0]['id'])
    
    shipping_method = None
    if 'Standard' in o_h.shipping_method.name:
        shipping_method = 'USPS-FC'
    if 'Expedited' in o_h.shipping_method.name:
        shipping_method = 'USPS-PM'
    if 'Express' in o_h.shipping_method.name:
        shipping_method = 'UPS-Blue'

    rma_obj = {
        "rma_id" : str(r_h.order.id),
        "order_id" : str(r_h.order.id),
        "customer_id" : "DA111",
        "status_id" : None,
        "tracking_code" : o_fulfillment.tracking_number,
        "is_resolved" : None,
        "return_address" : None,
        "customer_name" : shipping_address.first_name + ' ' + shipping_address.last_name,
        "ship_via_code": shipping_method,
        "reason": r_l.return_reason,
        "items": item_list,

        "address" : shipping_address.street_address_1,
        "address2" : shipping_address.street_address_2,
        "address3" : None,
        "city" : shipping_address.city,
        "state" : shipping_address.country_area,
        "zip" : shipping_address.postal_code,
        "phone" : str(shipping_address.phone),
        "email" : o_h.user_email,
        "country" : "US",

        "address_billing" : billing_address.street_address_1,
        "address2_billing" : billing_address.street_address_2,
        "address3_billing" : None,
        "city_billing" : billing_address.city,
        "state_billing" : billing_address.country_area,
        "zip_billing" : billing_address.postal_code,
        "phone_billing" : str(billing_address.phone),
        "email_billing" : o_h.user_email,
        "country_billing" : "US",

        "receiptUrl" : None,
        "freightCharge" : str(o_h.shipping_price_gross_amount)
    }

    rma_send = {"rmas": [rma_obj]}

    print (json.dumps(rma_send, sort_keys=True, indent=4))

    ff_cli = FrogfishClient(settings.FROGFISH_API_TOKEN)

    # ff_cli.credits.create(credits=rma_send)



class Response(object):
    def __init__(self, status_code, text):
        self.content = text
        self.cached = False
        self.status_code = status_code
        self.ok = self.status_code < 400

    @property
    def text(self):
        return self.content

    def __repr__(self):
        return 'HTTP {} {}'.format(self.status_code, self.content)



class HttpClient(object):
    def __init__(self, pool_connections=True):
        self.session = Session() if pool_connections else None

    def post_ff(self, url, key, query):
        request = requests.post(url, headers={'Authorization': key}, json=query)
        if(request.status_code == 201):
            print("Response 201")
            print(request.text)
            return request.text
        else:
            print(request.text)
            print("Failed with status code " + str(request.status_code))


class FrogfishClient(object):

    def __init__(self, token):
        self.token = token

    @property
    def credits(self):
        return Credits(self.token)



class Credits(HttpClient):
    def __init__(self, token):
      self.token = token
    
    def create(self, **kwargs):
        response = self.post_ff(
            settings.FROGFISH_API_URL, 
            self.token, kwargs['credits']
        )
        return response
