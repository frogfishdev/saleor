
from urllib.parse import urlencode

from templated_email import send_templated_mail

from ..celeryconf import app
from ..core.emails import get_email_context
from ..core.utils.url import prepare_url
from .models import MailListParticipant

SEND_PROMOTION_TEMPLATE = "promotion/send_promotion"



def collect_data_for_email(
    template: str, recipient_email: str, discount_code: str, 
) -> dict:
    
    send_kwargs, email_context = get_email_context()

    email_context["recipient_email"] = recipient_email
    email_context["discount_code"] = discount_code

    print('hello')
    print(email_context)

    return {
        "recipient_list": [recipient_email],
        "template_name": template,
        "context": email_context,
        **send_kwargs,
    }

def send_promotion(recipient_email: str, discount_code: str):
    email_data = collect_data_for_email(SEND_PROMOTION_TEMPLATE, recipient_email, discount_code)
    send_templated_mail(**email_data)
    



