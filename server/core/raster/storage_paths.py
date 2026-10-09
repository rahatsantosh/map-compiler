from django.conf import settings

RANDOM_FOREST_CACHE = str(settings.MODEL_CACHE_DIR / "random_forest")
PCA_CACHE = str(settings.MODEL_CACHE_DIR / "pca")
