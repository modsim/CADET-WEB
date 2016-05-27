# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulation', '0004_auto_20160525_0827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job_status',
            name='end',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
