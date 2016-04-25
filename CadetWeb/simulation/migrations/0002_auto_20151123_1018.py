# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Isotherms',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Name', models.CharField(unique=True, max_length=80)),
                ('Isotherm', models.CharField(max_length=80)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Job_Blob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.TextField()),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Sim_Blob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.TextField()),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.AlterModelOptions(
            name='components',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='job',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='job_double',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='job_int',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='job_notes',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='job_results',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='job_string',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='job_type',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='models',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='parameters',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='products',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='sim_double',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='sim_int',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='sim_results',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='sim_string',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='simulation',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='steps',
            options={'ordering': ['id']},
        ),
        migrations.AddField(
            model_name='job',
            name='username',
            field=models.CharField(default=b'cadet', max_length=30),
        ),
        migrations.AlterField(
            model_name='parameters',
            name='name',
            field=models.CharField(unique=True, max_length=80),
        ),
        migrations.AddField(
            model_name='sim_blob',
            name='Component_ID',
            field=models.ForeignKey(to='simulation.Components'),
        ),
        migrations.AddField(
            model_name='sim_blob',
            name='Parameter_ID',
            field=models.ForeignKey(to='simulation.Parameters'),
        ),
        migrations.AddField(
            model_name='sim_blob',
            name='Simulation_ID',
            field=models.ForeignKey(to='simulation.Simulation'),
        ),
        migrations.AddField(
            model_name='sim_blob',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
        ),
        migrations.AddField(
            model_name='job_blob',
            name='Component_ID',
            field=models.ForeignKey(to='simulation.Components'),
        ),
        migrations.AddField(
            model_name='job_blob',
            name='Job_ID',
            field=models.ForeignKey(to='simulation.Job'),
        ),
        migrations.AddField(
            model_name='job_blob',
            name='Parameter_ID',
            field=models.ForeignKey(to='simulation.Parameters'),
        ),
        migrations.AddField(
            model_name='job_blob',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
        ),
    ]
