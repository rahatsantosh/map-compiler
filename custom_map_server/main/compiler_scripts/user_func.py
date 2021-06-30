'''
Front End, User Accessible Wrapper Functions
'''
from osgeo import osr
import numpy as np
from PIL import Image
import cv2
import os
import lxml.etree as ET
from django.http import HttpResponse

from .helpers import coord, norm, apply_cmap
from .basics import *
from .ml import *


'''def rasterPlot(dataset, coordinate, coord_format, bands=None, style='bar'):
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

    return graph'''

# gdal loc info terminal
def rasterPlot(layer, coordinate, coord_format="EPSG:4326", bands=None, style='bar'):
    if bands is None:
        command = f"gdallocationinfo -xml -l_srs \"{coord_format}\" {layer} {coordinate[0]} {coordinate[1]}"
    else:
        command = f"gdallocationinfo -xml"
        for b in bands:
            command += f" -b {b} "
        command += f"-l_srs \"{coord_format}\" {layer} {coordinate[0]} {coordinate[1]}"
    pc = os.popen(command).read()
    parser = ET.XMLParser(recover=True)
    tree = ET.ElementTree(ET.fromstring(pc, parser=parser))
    labels = []
    data = []
    for elem in tree.iter():
        if elem.tag=='BandReport':
            labels.append(int(elem.attrib['band']))
        elif elem.tag=='Value':
            data.append(int(elem.text))
    return {
        'type':style,
        'data':{
            'labels':labels,
            'datasets':[{
                'data':data
            }]
        }
    }

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
    clip_minR=None, clip_maxR=None,
    clip_minG=None, clip_maxG=None,
    clip_minB=None, clip_maxB=None,
    ip_minR=None, ip_maxR=None, 
    ip_minG=None, ip_maxG=None, 
    ip_minB=None, ip_maxB=None,
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
            ip_minR=ip_minR, ip_maxR=ip_maxR,
            clip_minR=clip_minR, clip_maxR=clip_maxR,
            op_minR=op_minR, op_maxR=op_maxR
        ))
        if cmap is not None and cmap_order==0:
            im = apply_cmap(im, cmap)
    else:
        im = np.dstack(norm(
            R.band,G.band,B.band,
            op_minR=op_minR, op_maxR=op_maxR,
            op_minG=op_minG, op_maxG=op_maxG,
            op_minB=op_minB, op_maxB=op_maxB,
            clip_minR=clip_minR, clip_maxR=clip_maxR,
            clip_minG=clip_minG, clip_maxG=clip_maxG,
            clip_minB=clip_minB, clip_maxB=clip_maxB,
            ip_minR=ip_minR, ip_maxR=ip_maxR,
            ip_minG=ip_minG, ip_maxG=ip_maxG,
            ip_minB=ip_minB, ip_maxB=ip_maxB
        ))
    print(im.min(),im.max(),'==============================')
    _, ar = cv2.imencode('.png',im)
    response = HttpResponse(ar.tobytes(),content_type="image/png")
    return response
