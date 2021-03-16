from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.core.handlers.wsgi import WSGIRequest
from urllib.parse import urljoin

import requests

from ..base_plugin import BasePlugin


class ApplePayPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.applepay"
    PLUGIN_NAME = "Apple Pay"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Apple Pay Authorize Net integration"
    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        # check if plugin is active
        # check signatures and headers.
        print(request.POST)
        if path == '/webhook':
            # '{"merchantIdentifier": "merchant.authorize.net.test.dev15","domainName": "accept-sample.azurewebsites.net","displayName":"ApplePayDemoTestDev15"}';
            validation_payload = {
                "merchantIdentifier":settings.APPLE_PAY_MERCHANT_ID,
                "domainName": settings.APPLE_PAY_DOMAIN,
                "displayName": settings.APPLE_PAY_DISPLAY_NAME
            }
            r =  requests.post(
                request.POST['validationUrl'],
                headers={'Content-Type': 'application/json'},
                json=validation_payload,
                cert=('./merchant_id.pem', './applepay_merchant.key')
            )
            print(vars(r))

            return JsonResponse(data=r)
        return HttpResponseNotFound()