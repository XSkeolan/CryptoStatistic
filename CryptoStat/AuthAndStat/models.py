from django.db import models


class Info(models.Model):
    date = models.DateField()
    currency = models.CharField(max_length=3)
    equity = models.FloatField()
