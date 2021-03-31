import json
import time
from decimal import *
import base64

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.core.handlers.wsgi import WSGIRequest

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import createTransactionController

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
            if request.POST['action'] == 'MERCHANTVERIFY':
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
                t = json.loads(r.content)
                j = JsonResponse(data=json.loads(r.content))
                j["Access-Control-Allow-Origin"] = "*"
                return j
            elif request.POST['action'] == 'COMPLETEPAYMENT':
                r, error = self.apple_pay_transaction(request)
                if error is None:
                    j = JsonResponse(data=r)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j
                else:
                    failed = HttpResponse('Transaction Failed', status=400)
                    failed["Access-Control-Allow-Origin"] = "*"
                    return failed
                
        return HttpResponseNotFound()



    def apple_pay_transaction(self, request):
        merchantAuth = apicontractsv1.merchantAuthenticationType()
        merchantAuth.name = settings.AUTHORIZENET_API_LOGIN_ID
        merchantAuth.transactionKey = settings.AUTHORIZENET_TRANSACTION_KEY

        opaquedata = apicontractsv1.opaqueDataType()
        opaquedata.dataDescriptor = "COMMON.APPLE.INAPP.PAYMENT"
        opaquedata.dataValue = request.POST['token']

        paymentOne = apicontractsv1.paymentType()
        paymentOne.opaqueData = opaquedata

        transactionrequest = apicontractsv1.transactionRequestType()
        transactionrequest.transactionType = "authCaptureTransaction"
        transactionrequest.amount = Decimal(request.POST['amount'])
        transactionrequest.payment = paymentOne

        retail = apicontractsv1.transRetailInfoType()
        retail.marketType = '0'
        retail.deviceType = '1'
        transactionrequest.retail = retail

        request = apicontractsv1.createTransactionRequest()
        request.merchantAuthentication = merchantAuth
        request.refId = str("ref {}".format(time.time())).split('.')[0]
        request.transactionRequest = transactionrequest

        controller = createTransactionController(request)
        controller.setenvironment(settings.AUTHORIZENET_ENVIRONMENT)
        controller.execute()

        response = controller.getresponse()

        error = None
        ret = {}

        if response is not None:
            if response.messages.resultCode == "Ok":
                if hasattr(response.transactionResponse, 'messages') == True:
                    print ('Successfully created transaction with Transaction ID: %s' % response.transactionResponse.transId)
                    print ('Transaction Response Code: %s' % response.transactionResponse.responseCode)
                    print ('Message Code: %s' % response.transactionResponse.messages.message[0].code)
                    print ('Description: %s' % response.transactionResponse.messages.message[0].description)
                else:
                    print ('Failed Transaction.')
                    if hasattr(response.transactionResponse, 'errors') == True:
                        print ('Error Code:  %s' % str(response.transactionResponse.errors.error[0].errorCode))
                        print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                        error = response.transactionResponse.errors.error[0].errorText
            else:
                print ('Failed Transaction.')
                if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                    print ('Error Code: %s' % str(response.transactionResponse.errors.error[0].errorCode))
                    print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText)
                    error = response.transactionResponse.errors.error[0].errorText
                else:
                    print ('Error Code: %s' % response.messages.message[0]['code'].text)
                    print ('Error message: %s' % response.messages.message[0]['text'].text)
                    error = response.messages.message[0]['text'].text
            if error is None:
                ret = {
                    "transaction_id": str(response.transactionResponse.transId),
                }
        else:
            print ('Null Response.')

        return ret, error