# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulation', '0003_auto_20160504_1158'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job_Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('seen', models.BooleanField()),
                ('successful', models.BooleanField()),
                ('running', models.BooleanField()),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('end', models.DateTimeField()),
                ('Job_ID', models.OneToOneField(to='simulation.Job')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.AlterField(
            model_name='job_results',
            name='Job_ID',
            field=models.OneToOneField(to='simulation.Job'),
        ),
        migrations.AlterField(
            model_name='sim_results',
            name='Simulation_ID',
            field=models.OneToOneField(to='simulation.Simulation'),
        ),
    ]
