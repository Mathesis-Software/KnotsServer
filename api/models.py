from django.db import models

class Knot(models.Model):
    identifier = models.CharField(max_length=16, unique=True)
    dtcode = models.CharField(max_length=19)
