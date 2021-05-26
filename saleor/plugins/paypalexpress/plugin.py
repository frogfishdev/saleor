
import json

from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.core.handlers.wsgi import WSGIRequest

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import createTransactionController

from ..base_plugin import BasePlugin

class PaypalExpressPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.paypalexpress"
    PLUGIN_NAME = "Paypal Express"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Paypal Express Authorize Net integration"

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        if path == '/webhook':
            j = JsonResponse(data=json.loads('{"TEST": "TEST"}'))
            j["Access-Control-Allow-Origin"] = "*"
            return j

        return HttpResponseNotFound()