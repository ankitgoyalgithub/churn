# Generated by Django 2.2.2 on 2019-07-06 09:32

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('health_assessment', '0002_auto_20190706_1430'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='run_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
