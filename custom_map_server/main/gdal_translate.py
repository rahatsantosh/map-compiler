from osgeo import gdal, gdal_array
import numpy as np
from PIL import Image
import cv2
from pyproj import CRS, Transformer
from django.http import HttpResponse
from sklearn.preprocessing import MinMaxScaler

    
def coord(projWin, coord_sys):
    transformer = Transformer.from_crs("EPSG:3857", coord_sys)
    projWin[1],projWin[0] = transformer.transform(projWin[0], projWin[1])
    projWin[3],projWin[2] = transformer.transform(projWin[2], projWin[3])
    return projWin

def to_map(R, G=None, B=None, A=None, include_alpha=False, grayscale=False):
    if grayscale:
        im = R
    else:
        im = np.dstack([R, G, B])
    im = im.astype(np.uint8) * 255
    if include_alpha and A is None:
        alpha = (np.mean(im, axis=2)+1) * 2
        im = np.dstack([im,alpha.astype(np.uint8)])
        img = Image.fromarray(im, mode='RGBA')
    elif include_alpha:
        alpha = A * 255
        im = np.dstack([im,alpha.astype(np.uint8)])
        img = Image.fromarray(im, mode='RGBA')
    elif grayscale:
        img = Image.fromarray(im, mode='L')
    else:
        img = Image.fromarray(im, mode='RGB')
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response

'''def norm(x, y=None, z=None, minR=0, maxR=1, minG=0, maxG=1, minB=0, maxB=1, ip_minR=0, ip_maxR=2500, ip_minG=0, ip_maxG=2500, ip_minB=0, ip_maxB=4000):
    if y is None and z is None:
        x = (x-ip_minR)/(ip_maxR-ip_minR)
        x = ((maxR-minR)*x)+minR
        return x * 255.0
    x = (x-ip_minB)/(ip_maxB-ip_minB)
    y = (x-ip_minG)/(ip_maxG-ip_minG)
    z = (x-ip_minR)/(ip_maxB-ip_minR)
    x = ((maxB-minB)*x)+minB
    y = ((maxG-minG)*y)+minG
    z = ((maxR-minR)*z)+minR
    return x * 255.0, y * 255.0, z * 255.0'''

def norm(x, op_minR=0, op_maxR=1, ip_minR=0, ip_maxR=2500):
    indices = np.where(x==0)
    x = (x-ip_minR)/(ip_maxR-ip_minR)
    x = ((op_maxR-op_minR)*x)+op_minR
    x[indices] = 0
    return x * 255.0

def convert_band(band):
    return int(band[1:])

def convert_bands(bands):
    return list(map(convert_band, bands))

def get_translate(projWin, input_band, weight, coord_sys="EPSG:4326", minR=0, maxR=1, minG=0, maxG=1, minB=0, maxB=1):
    # '/vsicurl/http://landsat-pds.s3.amazonaws.com/c1/L8/042/034/LC08_L1TP_042034_20170616_20170629_01_T1/LC08_L1TP_042034_20170616_20170629_01_T1_B4.TIF')
    projWin = coord(projWin, coord_sys)
    input_band = convert_bands(input_band)
    dataset = gdal.Open(
        '/vsicurl/http://mobileapp.nesdr.gov.in/out2019.tif',
        gdal.GA_ReadOnly
        )
    out = gdal.Warp('', dataset, width=256, height=256, outputBounds=projWin, format='MEM')
    if weight is None or not weight:
        weight = [1,1,1]
    if len(input_band) < len(weight):
        weight = weight + weight[:len(weight)%len(input_band)]
    if len(input_band)==3:
        im = np.stack((
                    out.ReadAsArray()[input_band[0]+1,...]*weight[0],
                    out.ReadAsArray()[input_band[1]+1,...]*weight[1],
                    out.ReadAsArray()[input_band[2]+1,...]*weight[2]
                    ),axis=2)
    else:
        im = np.array(out.ReadAsArray()[input_band[0]+1,...]*weight[0])
    
    if np.max(im)==0:
        im = np.zeros((256,256,4))
        img = Image.fromarray(im, mode='RGBA')
        response = HttpResponse(content_type="image/png")
        img.save(response, "PNG")
        return response
    im = np.dstack(norm(im[:,:,0],im[:,:,1],im[:,:,2], minR, maxR, minG, maxG, minB, maxB)) * 255
    _, ar = cv2.imencode('.png',im)
    response = HttpResponse(ar.tobytes(),content_type="image/png")
    return response