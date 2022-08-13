from turtle import title
from django.db import models

# Create your models here.
class WSBPosts(models.Model):
    ticker = models.CharField(max_length=5)
    name = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    score = models.IntegerField()
    link = models.CharField(max_length=255)
    created = models.DateTimeField()

    class Meta:
        unique_together = ["ticker", "name"]


