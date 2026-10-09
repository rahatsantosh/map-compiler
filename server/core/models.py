from django.db import models


class ModelCache(models.Model):
    session_hash = models.CharField(max_length=200, primary_key=True)
    blocked = models.BooleanField(default=True)

    class Meta:
        db_table = "core_model_cache"
