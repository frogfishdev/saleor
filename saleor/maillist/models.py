
from django.db import models
from django.utils import timezone
    
class MailListParticipant(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.TextField()
    last_name = models.TextField()
    state = models.TextField()
    active = models.BooleanField()
    created_date = models.DateTimeField(default=timezone.now, editable=False)
