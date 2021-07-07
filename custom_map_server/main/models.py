from django.db import models

# Create your models here.
class Model_cache(models.Model):
    """
    Model for caching ML models to prevent retraining by multiple requests per session.

    Parameters
    ----------
        sessHash -- Hash containing unique session hash as well as a dataset hash to differentiate between
                    models trained of different datasets.
        blocked  -- Boolean to determine whether any request from session is in blocking section. 
    """
    sessHash = models.CharField(max_length=200, primary_key=True, serialize=False)
    blocked = models.BooleanField()