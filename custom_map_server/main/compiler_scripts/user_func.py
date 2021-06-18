'''
Front End, User Accessible Wrapper Functions
'''
from osgeo import osr
import numpy as np
from PIL import Image
import cv2
from django.http import HttpResponse

from .helpers import coord, norm, apply_cmap
from .basics import *
from .ml import *


def rasterPlot(dataset, coordinate, coord_format, bands=None, style='bar'):
    if bands is None:
        bands = list(range(1,dataset.RasterCount+1))
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    proj = osr.SpatialReference(wkt=dataset.GetProjection())
    epsg = "EPSG:"+str(proj.GetAttrValue('AUTHORITY',1))
    coordinates = coord(coordinate, coord_sys=epsg, src_coord_sys=coord_format)

    transform = dataset.GetGeoTransform()

    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]
    col = int((coordinates[0] - xOrigin) / pixelWidth)
    row = int((yOrigin - coordinates[1] ) / pixelHeight)

    def prepare_data_bandwise(band):
        band = dataset.GetRasterBand(band)
        data = band.ReadAsArray(0, 0, cols, rows).tolist()
        return data[row][col]

    band_data = list(map(prepare_data_bandwise,bands))
    labels = bands
    graph = {
        'type':style,
        'data':{
            'labels':labels,
            'datasets':[{
                'data':band_data
            }]
        }
    }

    return graph

'''def rasterPlot(dataset, coordinate, coord_format, bands=None, style='bar'):
    proj = osr.SpatialReference(wkt=dataset.GetProjection())
    epsg = "EPSG:"+str(proj.GetAttrValue('AUTHORITY',1))
    coordinates = coord(coordinate, coord_sys=epsg, src_coord_sys=coord_format)
    d = gdal.Warp(
        '', dataset,
        width=1, height=1,
        outputBounds = [coordinates[0],coordinates[1],coordinates[0]+1,coordinates[1]+1],
        format='MEM'
    )
    if bands is None:
        data = d.ReadAsArray().ravel()
        print(data)
        data = data.tolist()
        bands = list(range(1,dataset.RasterCount+1))
    else:
        data = [int(d.GetRasterBand(band).ReadAsArray()[0][0]) for band in bands]

    labels = bands
    return {
        'type':style,
        'data':{
            'labels':labels,
            'datasets':[{
                'data':data
            }]
        }
    }'''

def setup(
    R, G=None, B=None,
    weight=None, 
    op_minR=0, op_maxR=1, 
    op_minG=0, op_maxG=1, 
    op_minB=0, op_maxB=1,  
    ip_minR=-0.5, ip_maxR=0.8, 
    ip_minG=-0.5, ip_maxG=0.8, 
    ip_minB=-0.5, ip_maxB=0.8,
    cmap=None,
    cmap_order=1
    ):
    if (np.max(R.band)==0 and G is None and B is None) or (np.max(R.band)==0 and np.max(G.band)==0 and np.max(B.band)==0):
        im = np.zeros((256,256,4))
        img = Image.fromarray(im, mode='RGBA')
        response = HttpResponse(content_type="image/png")
        img.save(response, "PNG")
        return response
    if weight is None:
        weight = [1,1,1]
    if G is None and B is None:
        im  = weight[0] * R.band
        if cmap is not None and cmap_order==1:
            im = apply_cmap(im, cmap)
        im = np.array(norm(
            x = im,
            op_minR=op_minR, op_maxR=op_maxR,
            ip_minR=ip_minR, ip_maxR=ip_maxR))
        if cmap is not None and cmap_order==0:
            im = apply_cmap(im, cmap)
    else:
        x,y,z = norm(
            x=weight[0]*R.band, 
            y=weight[1]*G.band, 
            z=weight[2]*B.band,
            op_minR=op_minR, op_maxR=op_maxR,
            op_minG=op_minG, op_maxG=op_maxG,
            op_minB=op_minB, op_maxB=op_maxB,
            ip_minR=ip_minR, ip_maxR=ip_maxR,
            ip_minG=ip_minG, ip_maxG=ip_maxG,
            ip_minB=ip_minB, ip_maxB=ip_maxB)
        im = np.dstack((R.band,G.band,B.band))
    _, ar = cv2.imencode('.png',im)
    response = HttpResponse(ar.tobytes(),content_type="image/png")
    return response
