# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulation', '0002_auto_20151123_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job_notes',
            name='Job_ID',
            field=models.OneToOneField(to='simulation.Job'),
        ),
    ]
