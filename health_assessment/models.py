from datetime import datetime
import uuid

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

def upload_file_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.run_id, filename)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class Run(models.Model):
    run_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    gainsight = models.BooleanField(default=False)
    outcome_data = models.FileField(upload_to=upload_file_path)
    scorecard_history = models.FileField(upload_to=upload_file_path)
    account_details = models.FileField(upload_to=upload_file_path, blank=True) 
    preprocessed_file = models.FileField(upload_to=upload_file_path)
    id_field = models.CharField(max_length=64)
    churn_date = models.CharField(max_length=64)
    snapshot_date = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=datetime.now())

    def __str__(self):
        return str(self.user_id)+"__"+str(self.preprocessed_file)

class Report(models.Model):
    run_id = models.ForeignKey(Run, on_delete=models.CASCADE)
    report_name = models.CharField(max_length=255)
    report_path = models.CharField(max_length=1024)
