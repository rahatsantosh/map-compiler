'''
[User Inacessible]
Helper function, used by compiler script functions. Can be accessed only by compiler scripts,
and not directly by users.

Functions:

    dict_hash(dictionary) -> string
    get_dataset_(string) -> osgeo.gdal.Dataset
    prepare_data(string, list[dictionary], list[int], string) -> list, list
    coord(list[int], string, string) -> list[int]
    apply_cmap(np.array, dictionary) -> np.array
    single_band_norm(np.array, int, int, int, int, int, int) -> np.array
    norm(np.array, np.array, np.array, int, int, int, int, int, int
        , int, int, int, int, int, int
        , int, int, int, int, int, int) -> np.array, np.array, np.array
'''
from osgeo import gdal, osr
import numpy as np
from pyproj import CRS, Transformer
from typing import Dict, Any
import hashlib
import json

def dict_hash(dictionary):
    """
    MD5 hash of a dictionary.

        Arguments:
            dictionary[Dict[str, Any]] -- Dictionary to be hashed
        
        Returns:
            String hash of dictionary
    """
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()

def get_dataset_(layer='http://mobileapp.nesdr.gov.in/out2019.tif'):
    """
    Wrapper function for simple GDAL.Open() functionality
        
        Arguments:
            layer[string] -- Optimized GeoTIFF dataset link
        
        Returns:
            Object of type osgeo.gdal.Dataset
    """
    return gdal.Open(
        #'/vsicurl/'+layer,
        #'/media/kitoo/Pers/nesac/2019_NOV_DEC_compressed.tif',
        './main/2019_NOV_DEC_compressed_resample.tif',
        #'./main/out2019.tif', # Path to Local Optimized-Geotiff for testing purposes
        gdal.GA_ReadOnly
        )

def prepare_data(coord_format, data, bands, layer='http://mobileapp.nesdr.gov.in/out2019.tif'):
    """
    Bandwise data extraction for set of coordinates
    [Used by RandomForest Algorithm]

        Parameters:
            coord_format[string] -- Coordinate system used
            data[list] -- List of format:
                'data':[
                    {'coordinates':coordinate,'labels':label},
                    ...
                ]
            bands[list] -- List of bands to be used
            layer[string] -- Geotiff layer being used

        Returns:
            band_data -- bands values of the required coordinates
            labels -- associated labels to band values
    """
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
    """
    Transform coordinates between systems

        Parameters:
            projWin[list] -- Coordinate system to be transformed. List of length 2 or 4
            coord_sys[string] -- Destination coordinate system
            src_coord_sys[string] -- Source/Input coordinate system

        Return:
            projWin[list] -- Transformed coordinate system
    """
    if coord_sys == src_coord_sys:
        return projWin
    transformer = Transformer.from_crs(src_coord_sys, coord_sys)
    projWin[1],projWin[0] = transformer.transform(projWin[0], projWin[1])
    if len(projWin) > 2:
        projWin[3],projWin[2] = transformer.transform(projWin[2], projWin[3])
    return projWin

def apply_cmap(im, cmap):
    """
    Applying custom colourmap to grayscale image

        Parameters:
            im[np.array] -- Input grayscale format image
            cmap[Dictionary] -- Custom colour map

        Returns:
            Coloured format image, with applied cmap
    """
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
    """
    Normalization and clipping functionality for single band. Used to modularize norm.
    For ip_min, ip_max, clip_min and clip_max, default value of None, in which case clipping
    and normalizing of images is skipped.

        Parameters:
            x[np.array] -- Input single band image
            op_min[int] -- Minimum range value for normalized band
            op_max[int] -- Maximum range value for normalized band
            ip_min[int] -- Minimum range value for input single band
            ip_max[int] -- Maximum range value for input single band
            clip_min[int] -- Minimum cliping value for normalized band
            clip_max[int] -- Maximum cliping value for normalized band

        Returns:
            x[np.array] -- Normalized band
    """
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
    """
    Normalization and clipping functionality. Modularized by using single_band_norm.
    x, ip_minR, ip_maxR, op_minR, op_maxR, clip_minR, clip_maxR values to be used in case of
    grayscale single band, rest to be left to default.
    For colour multi band cases, default values of None are handled in single_band_norm.

        Parameters:
            x[np.array] -- Input red single band image
            y[np.array] -- Input green single band image
            z[np.array] -- Input blue single band image
            op_minR[int] -- Minimum range value for normalized red band
            op_maxR[int] -- Maximum range value for normalized red band
            op_minG[int] -- Minimum range value for normalized green band
            op_maxG[int] -- Maximum range value for normalized green band
            op_minB[int] -- Minimum range value for normalized blue band
            op_maxB[int] -- Maximum range value for normalized blue band
            ip_minR[int] -- Minimum range value for input single red band
            ip_maxR[int] -- Maximum range value for input single red band
            ip_minG[int] -- Minimum range value for input single green band
            ip_maxG[int] -- Maximum range value for input single green band
            ip_minB[int] -- Minimum range value for input single blue band
            ip_maxB[int] -- Maximum range value for input single blue band
            clip_minR[int] -- Minimum cliping value for normalized red band
            clip_maxR[int] -- Maximum cliping value for normalized red band
            clip_minG[int] -- Minimum cliping value for normalized green band
            clip_maxG[int] -- Maximum cliping value for normalized green band
            clip_minB[int] -- Minimum cliping value for normalized blue band
            clip_maxB[int] -- Maximum cliping value for normalized blue band

        Returns:
            x -- Normalized Red band or single normalized band, if grayscale input
            y -- Normalized Green band, output only if colour image
            z -- Normalized Blue band, output only if colour image
    """
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