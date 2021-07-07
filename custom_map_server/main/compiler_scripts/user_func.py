'''
[User Accessible]
Front End, Response Functions

Functions:
    rasterPlot(string, list, string, list, string) -> Dictionary
    setup(.basics.B, .basics.B, .basics.B, list,
        float, float, float,
        float, float, float,
        float, float, float,
        float, float, float,
        float, float, float,
        float, float, float,
        float, float, float,
        float, float, float,
        float, float, float,
        Dictionary, int) -> django.http.response
'''
import numpy as np
from PIL import Image
import cv2
import os
import lxml.etree as ET
from django.http import HttpResponse

from .helpers import norm, apply_cmap
from .core import *
from .ml import *


def rasterPlot(layer, coordinate, coord_format="EPSG:4326", bands=None, style='bar'):
    """
    Returns graph of required coordinate in a Chart.js usable format.
    
    Parameters:
        layer[string] -- Optimized-Geotiff Layer
        coordinate[list] -- coordinates to measure band data
        coord_format[string] -- Coordinate system used; default EPSG:4326
        bands[list] -- bands to be returned. On None uses all bands.
        style[string] -- graph type.
    
    Returns:
        Dictionary in Chart.js readable format.
    """
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
    ):  # sourcery no-metrics
    """
    Sets Up WMS Response Mapmap, to be viewed in frontend.

    Parameters:
        R [.basics.B] -- Band in Red position. If grayscale map, Only band passed to this argument.
        G [.basics.B] -- Band in Green position. If grayscale map, pass None.
        B [.basics.B] -- Band in Blue position. If grayscale map, pass None.
        weight [list] -- weight attributed to each band.
        op_minR [float] -- Minimum range value for normalized red band
        op_maxR [float] -- Maximum range value for normalized red band
        op_minG [float] -- Minimum range value for normalized green band
        op_maxG [float] -- Maximum range value for normalized green band
        op_minB [float] -- Minimum range value for normalized blue band
        op_maxB [float] -- Maximum range value for normalized blue band
        clip_minR [float] -- Minimum cliping value for normalized red band
        clip_maxR [float] -- Maximum cliping value for normalized red band
        clip_minG [float] -- Minimum cliping value for normalized green band
        clip_maxG [float] -- Maximum cliping value for normalized green band
        clip_minB [float] -- Minimum cliping value for normalized blue band
        clip_maxB [float] -- Maximum cliping value for normalized blue band
        ip_minR [float] -- Minimum range value for input single red band
        ip_maxR [float] -- Maximum range value for input single red band
        ip_minG [float] -- Minimum range value for input single green band
        ip_maxG [float] -- Maximum range value for input single green band
        ip_minB [float] -- Minimum range value for input single blue band
        ip_maxB [float] -- Maximum range value for input single blue band
        cmap [Dictionary] -- Custom colour map in dictionary format
        cmap_order [int] -- Values: 0 or 1. Depends on whether cmap to be applied before or after normalization
    
    Returns:
        response [django.http.response] -- 'png' media response of grayscale or rgb format depending on input bands
    """
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
    _, ar = cv2.imencode('.png',im.astype(np.uint8))
    response = HttpResponse(ar.tobytes(),content_type="image/png")
    return response
