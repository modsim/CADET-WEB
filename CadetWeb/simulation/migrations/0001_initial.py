# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Components',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Component', models.CharField(max_length=80)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('study_name', models.CharField(max_length=80)),
                ('json', models.TextField()),
                ('uid', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job_Double',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.FloatField()),
                ('Component_ID', models.ForeignKey(to='simulation.Components')),
                ('Job_ID', models.ForeignKey(to='simulation.Job')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job_Int',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.IntegerField()),
                ('Component_ID', models.ForeignKey(to='simulation.Components')),
                ('Job_ID', models.ForeignKey(to='simulation.Job')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job_Notes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rating', models.FloatField()),
                ('notes', models.TextField()),
                ('Job_ID', models.ForeignKey(to='simulation.Job')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job_Results',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Timestamp', models.DateTimeField(auto_now_add=True)),
                ('Attempted', models.IntegerField()),
                ('Successful', models.IntegerField()),
                ('Job_ID', models.ForeignKey(to='simulation.Job')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job_String',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.CharField(max_length=80)),
                ('Component_ID', models.ForeignKey(to='simulation.Components')),
                ('Job_ID', models.ForeignKey(to='simulation.Job')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Job_Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=80)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Models',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model', models.CharField(max_length=80)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Parameters',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('units', models.CharField(max_length=80)),
                ('description', models.CharField(max_length=2000)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Products',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('product', models.CharField(max_length=80)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sim_Double',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.FloatField()),
                ('Component_ID', models.ForeignKey(to='simulation.Components')),
                ('Parameter_ID', models.ForeignKey(to='simulation.Parameters')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sim_Int',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.IntegerField()),
                ('Component_ID', models.ForeignKey(to='simulation.Components')),
                ('Parameter_ID', models.ForeignKey(to='simulation.Parameters')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sim_Results',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Timestamp', models.DateTimeField(auto_now_add=True)),
                ('Success', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sim_String',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Data', models.CharField(max_length=80)),
                ('Component_ID', models.ForeignKey(to='simulation.Components')),
                ('Parameter_ID', models.ForeignKey(to='simulation.Parameters')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Simulation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Rel_Path', models.CharField(max_length=80)),
                ('Job_ID', models.ForeignKey(to='simulation.Job')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Steps',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Step', models.CharField(max_length=80)),
                ('Job_ID', models.ForeignKey(to='simulation.Job')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='sim_string',
            name='Simulation_ID',
            field=models.ForeignKey(to='simulation.Simulation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sim_string',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sim_results',
            name='Simulation_ID',
            field=models.ForeignKey(to='simulation.Simulation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sim_int',
            name='Simulation_ID',
            field=models.ForeignKey(to='simulation.Simulation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sim_int',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sim_double',
            name='Simulation_ID',
            field=models.ForeignKey(to='simulation.Simulation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sim_double',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job_string',
            name='Parameter_ID',
            field=models.ForeignKey(to='simulation.Parameters'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job_string',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job_int',
            name='Parameter_ID',
            field=models.ForeignKey(to='simulation.Parameters'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job_int',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job_double',
            name='Parameter_ID',
            field=models.ForeignKey(to='simulation.Parameters'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job_double',
            name='Step_ID',
            field=models.ForeignKey(to='simulation.Steps'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='Job_Type_ID',
            field=models.ForeignKey(to='simulation.Job_Type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='Model_ID',
            field=models.ForeignKey(to='simulation.Models'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='Product_ID',
            field=models.ForeignKey(to='simulation.Products'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='components',
            name='Job_ID',
            field=models.ForeignKey(to='simulation.Job'),
            preserve_default=True,
        ),
    ]
