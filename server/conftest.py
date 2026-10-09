import sys
from unittest.mock import MagicMock

osgeo_mock = MagicMock()
osgeo_mock.gdal.GA_ReadOnly = 0

for mod_name in ["osgeo", "osgeo.gdal", "osgeo.osr", "cv2"]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = osgeo_mock
