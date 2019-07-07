import datetime
import uuid

from django.db import models

def upload_file_path(instance, filename):
    print(instance)
    print(filename)
    return 'user_{0}/{1}'.format(instance.run_id, filename)

class Run(models.Model):
    run_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    gainsight = models.BooleanField(default=False)
    outcome_data = models.FileField(upload_to=upload_file_path)
    scorecard_history = models.FileField(upload_to=upload_file_path)
    account_details = models.FileField(upload_to=upload_file_path) 
    preprocessed_file = models.FileField(upload_to=upload_file_path)
    id_field = models.CharField(max_length=64)
    churn_date = models.DateField(default=datetime.date.today)
    snapshot_date = models.DateField(default=datetime.date.today)
