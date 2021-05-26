
from decimal import Decimal
import json

from django.conf import settings
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
            r, error = self.paypal_express_transaction(request)
            if error is None:
                j = JsonResponse(data=r)
                j["Access-Control-Allow-Origin"] = "*"
                return j
            else:
                failed = HttpResponse('Transaction Failed', status=400)
                failed["Access-Control-Allow-Origin"] = "*"
                return failed

        return HttpResponseNotFound()

    def paypal_express_transaction(self, request):
        merchantAuth = apicontractsv1.merchantAuthenticationType()
        merchantAuth.name = settings.AUTHORIZENET_API_LOGIN_ID
        merchantAuth.transactionKey = settings.AUTHORIZENET_TRANSACTION_KEY

        paypal = apicontractsv1.payPalType()
        paypal.successUrl = "http://www.merchanteCommerceSite.com/Success/TC25262"
        paypal.cancelUrl = "http://www.merchanteCommerceSite.com/Success/TC25262"

        payment = apicontractsv1.paymentType()
        payment.payPal = paypal

        transactionrequest = apicontractsv1.transactionRequestType()
        transactionrequest.amount = Decimal(0.8)
        transactionrequest.transactionType = apicontractsv1.transactionTypeEnum.authOnlyTransaction
        transactionrequest.payment = payment

        request = apicontractsv1.createTransactionRequest()
        request.merchantAuthentication = merchantAuth
        request.refId = "Sample"
        request.transactionRequest = transactionrequest

        controller = createTransactionController(request)
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