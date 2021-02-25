from typing import Any
from django import template

from ..models import OrderLine

register = template.Library()


@register.simple_tag()
def tracking_url_to_number(tracking_number: Any):
    # https://tools.usps.com/go/TrackConfirmAction?tLabels=${9400111899560540303156}
    return (tracking_number.split("${"))[1].split("}")[0]