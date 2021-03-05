from typing import Any
from django import template

from ..models import OrderLine

register = template.Library()


@register.simple_tag()
def tracking_url_to_number(tracking_number: Any):
    # https://wwwapps.ups.com/tracking/tracking.cgi?tracknum=1Z726E010241727921
    # https://tools.usps.com/go/TrackConfirmAction?tLabels=9400111899560579638243
    try:
        return tracking_number.split("=")[1]
    except:
        return "tracking link"