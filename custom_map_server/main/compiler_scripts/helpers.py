from osgeo import gdal, osr
import numpy as np
from pyproj import CRS, Transformer
from typing import Dict, Any
import hashlib
import json

def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()

def get_dataset_(layer='http://mobileapp.nesdr.gov.in/out2019.tif'):
    return gdal.Open(
        '/vsicurl/'+layer,
        #'./main/out2019.tif',
        gdal.GA_ReadOnly
        )

def prepare_data(coord_format, data, bands, layer='http://mobileapp.nesdr.gov.in/out2019.tif'):
    coordinates = []
    labels = []
    dataset = get_dataset_(layer)
    proj = osr.SpatialReference(wkt=dataset.GetProjection())
    epsg = "EPSG:"+str(proj.GetAttrValue('AUTHORITY',1))
    for x in data:
        coordinates.append(x['coordinates'])
        labels.append(x['labels'])
    coord_format = [coord_format] * len(coordinates)
    coord_format_op = [epsg] * len(coordinates)
    coordinates = list(map(coord, coordinates, coord_format, coord_format_op))

    def prepare_data_bandwise(band):
        band = dataset.GetRasterBand(band)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize

        transform = dataset.GetGeoTransform()

        xOrigin = transform[0]
        yOrigin = transform[3]
        pixelWidth = transform[1]
        pixelHeight = -transform[5]

        data = band.ReadAsArray(0, 0, cols, rows)

        pixels = []
        for point in coordinates:
            col = int((point[0] - xOrigin) / pixelWidth)
            row = int((yOrigin - point[1] ) / pixelHeight)
            d = data[row][col]
            pixels.append(d)
        return np.asarray(pixels)

    band_data = list(map(prepare_data_bandwise,bands))
    band_data = np.asarray(band_data).T
    band_data = np.reshape(band_data, (len(coordinates), len(bands)))
    return band_data, labels
    
def coord(projWin, coord_sys, src_coord_sys="EPSG:3857"):
    if coord_sys == src_coord_sys:
        return projWin
    transformer = Transformer.from_crs(src_coord_sys, coord_sys)
    projWin[1],projWin[0] = transformer.transform(projWin[0], projWin[1])
    if len(projWin) > 2:
        projWin[3],projWin[2] = transformer.transform(projWin[2], projWin[3])
    return projWin

def apply_cmap(im, cmap):
    palette = np.zeros(shape=(256, 3), dtype=np.uint8)
    for key in cmap.keys():
        palette[key] = cmap[key]
    im_ = im.flatten().astype(np.uint)
    color_image = palette[im_]
    return np.reshape(color_image, (im.shape[0],im.shape[1],3))

def single_band_norm(
    x,
    op_min=0, op_max=1,
    ip_min=None, ip_max=None,
    clip_min=None, clip_max=None
    ):
    clip_flag = clip_min is None or clip_max is None
    ip_flag = ip_min is None or ip_max is None
    indices = np.where(x==0)
    if not ip_flag:
        x = (x-ip_min)/(ip_max-ip_min)
        x = ((op_max-op_min)*x)+op_min
    x[indices] = 0
    if not clip_flag:
        x = np.clip(x, clip_min, clip_max)
    x = x*255.0 if not ip_flag else x
    return x

def norm(
    x, y=None, z=None,
    op_minR=0, op_maxR=1,
    op_minG=0, op_maxG=1,
    op_minB=0, op_maxB=1,
    clip_minR=None, clip_maxR=None,
    clip_minG=None, clip_maxG=None,
    clip_minB=None, clip_maxB=None,
    ip_minR=None, ip_maxR=None,
    ip_minG=None, ip_maxG=None,
    ip_minB=None, ip_maxB=None
    ):
    if y is None and z is None:
        return single_band_norm(
                x=x,
                op_min=op_minR, op_max=op_maxR,
                ip_min=ip_minR, ip_max=ip_maxR,
                clip_min=clip_minR, clip_max=clip_maxR
                )
    x = single_band_norm(
                x=x,
                op_min=op_minR, op_max=op_maxR,
                ip_min=ip_minR, ip_max=ip_maxR,
                clip_min=clip_minR, clip_max=clip_maxR
                )
    y = single_band_norm(
                x=y,
                op_min=op_minG, op_max=op_maxG,
                ip_min=ip_minG, ip_max=ip_maxG,
                clip_min=clip_minG, clip_max=clip_maxG
                )
    z = single_band_norm(
                x=z,
                op_min=op_minB, op_max=op_maxB,
                ip_min=ip_minB, ip_max=ip_maxB,
                clip_min=clip_minB, clip_max=clip_maxB
                )
    return x, y, z