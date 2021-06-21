
from django.db import models
from django.utils import timezone

class MailListParticipant(models.Model):
    email = models.EmailField(unique=True)
    created_date = models.DateTimeField(default=timezone.now, editable=False)