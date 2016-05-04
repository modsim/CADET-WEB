from django.db import models

# Create your models here.

class Parameters(models.Model):
    name = models.CharField(max_length=80, unique=True)
    units = models.CharField(max_length=80)
    description = models.CharField(max_length=2000)

    class Meta:
        ordering = ['id']

class Job_Type(models.Model):
    type = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Products(models.Model):
    product = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Models(models.Model):
    model = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Job(models.Model):
    Product_ID = models.ForeignKey('Products')
    Job_Type_ID = models.ForeignKey('Job_Type')
    Model_ID = models.ForeignKey('Models')
    created = models.DateTimeField(auto_now_add=True)
    study_name = models.CharField(max_length=80)
    json = models.TextField()
    uid = models.CharField(max_length=64)
    username = models.CharField(max_length=30, default='cadet')

    class Meta:
        ordering = ['id']

class Steps(models.Model):
    Job_ID = models.ForeignKey('Job')
    Step = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Components(models.Model):
    Job_ID = models.ForeignKey('Job')
    Component = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Job_String(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Job_ID = models.ForeignKey('Job')
    Data = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Job_Int(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Job_ID = models.ForeignKey('Job')
    Data = models.IntegerField()

    class Meta:
        ordering = ['id']

class Job_Double(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Job_ID = models.ForeignKey('Job')
    Data = models.FloatField()

    class Meta:
        ordering = ['id']

class Job_Blob(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Job_ID = models.ForeignKey('Job')
    Data = models.TextField()

    class Meta:
        ordering = ['id']

class Simulation(models.Model):
    Job_ID = models.ForeignKey('Job')
    Rel_Path = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Isotherms(models.Model):
    Name = models.CharField(max_length=80, unique=True)
    Isotherm = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Sim_String(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Simulation_ID = models.ForeignKey('Simulation')
    Data = models.CharField(max_length=80)

    class Meta:
        ordering = ['id']

class Sim_Int(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Simulation_ID = models.ForeignKey('Simulation')
    Data = models.IntegerField()

    class Meta:
        ordering = ['id']

class Sim_Double(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Simulation_ID = models.ForeignKey('Simulation')
    Data = models.FloatField()

    class Meta:
        ordering = ['id']

class Sim_Blob(models.Model):
    Step_ID = models.ForeignKey('Steps')
    Parameter_ID = models.ForeignKey('Parameters')
    Component_ID = models.ForeignKey('Components')
    Simulation_ID = models.ForeignKey('Simulation')
    Data = models.TextField()

    class Meta:
        ordering = ['id']

class Job_Results(models.Model):
    Job_ID = models.OneToOneField('Job')
    Timestamp = models.DateTimeField(auto_now_add=True)
    Attempted = models.IntegerField()
    Successful = models.IntegerField()

    class Meta:
        ordering = ['id']

class Sim_Results(models.Model):
    Simulation_ID = models.OneToOneField('Simulation')
    Timestamp = models.DateTimeField(auto_now_add=True)
    Success = models.IntegerField()

    class Meta:
        ordering = ['id']

class Job_Notes(models.Model):
    Job_ID = models.OneToOneField('Job')
    rating = models.FloatField()
    notes = models.TextField()

    class Meta:
        ordering = ['id']
