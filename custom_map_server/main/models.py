from django.db import models

# Create your models here.
class Model_cache(models.Model):
    sessHash = models.CharField(max_length=200, primary_key=True, serialize=False)