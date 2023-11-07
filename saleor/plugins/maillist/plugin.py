from decimal import *

from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.core.handlers.wsgi import WSGIRequest


from ..base_plugin import BasePlugin

from templated_email import send_templated_mail

from saleor.maillist import models as maillist_models
from saleor.maillist import emails

class MailListPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.maillist"
    PLUGIN_NAME = "Mail List Plugin"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Mail list signup endpoint"
    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        if path == '/webhook':
            if request.POST['action'] == 'ACTIVATE' or request.POST['action'] == 'DEACTIVATE':
                response_dict = self.handle_activation(request)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j
            if request.POST['action'] == 'CHECKACTIVE':
                response_dict = self.check_active(request)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j
            if request.POST['action'] == 'SAVEEMAIL':
                response_dict, error = self.save_email(request)
                if response_dict != None:
                    j = JsonResponse(data=response_dict)
                    j["Access-Control-Allow-Origin"] = "*"
                    return j

                j = JsonResponse(data={'error': error}, status=400)
                j["Access-Control-Allow-Origin"] = "*"
                return j

        return HttpResponseNotFound()

    def check_active(self, request):
        email = request.POST['email']
        ret = {}
        query = maillist_models.MailListParticipant.objects.filter(email=email)
        active_status = query[0].active
        ret['active'] = active_status
        return ret

    def save_email(self, request):

        error = None
        ret = {}
        email = request.POST['email']
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        state = request.POST.get('state')

        if maillist_models.MailListParticipant.objects.filter(email=email):
            return None, "Email already in mailing list"

        maillist_models.MailListParticipant.objects.create(
            email = email,
            first_name = first_name,
            last_name = last_name,
            state = state,
            active = True
        )

        # emails.send_promotion(email, '6PBYHWSHIP')

        ret['message'] = 'Success! You have signed up to receive promotional emails from City Distilling'

        return ret, error

    def handle_activation(self, request):
        action_type = request.POST['action']
        email = request.POST['email']
        if maillist_models.MailListParticipant.objects.filter(email=email):
            maillist_models.MailListParticipant.objects.filter(email=email).update(
                    active = False if action_type == "DEACTIVATE" else True
                )
        return self.check_active(request)
