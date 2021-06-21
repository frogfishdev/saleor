
from decimal import *

from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.core.handlers.wsgi import WSGIRequest


from ..base_plugin import BasePlugin


class MailListPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.maillist"
    PLUGIN_NAME = "Mail List Plugin"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Mail list signup endpoint"
    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        if path == '/webhook':
            if request.POST['action'] == 'SAVEEMAIL':
                response_dict, message = self.save_email(request)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

                j = JsonResponse(data={'error': message}, status=400)
                j["Access-Control-Allow-Origin"] = "*"
                return j            
                
        return HttpResponseNotFound()



    def save_email(self, request):
        
        message = 'Email saved'
        ret = {}

        return ret, message