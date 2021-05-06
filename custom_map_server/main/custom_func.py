from osgeo import gdal, gdal_array
import numpy as np
from PIL import Image
import cv2
from django.http import HttpResponse
from .gdal_translate import *

'''
Sample script:
d = get_dataset()
r1 = B(dataset=d, band_no=3)
r2 = B(dataset=d, band_no=1)
r = r1 + r2
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
response = setup(r,g,b)

d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(ndvi)

Sample url request:
http://127.0.0.1:8000/wms/?service=WMS&
request=GetMap&
layers=&styles=&format=image%2Fjpeg&
transparent=false&
version=1.1.1&
request_script=d%20%3D%20get_dataset()%0Ar1%20%3D%20B(d%2C%203)%0Ar2%20%3D%20B(d%2C%201)%0Ar%20%3D%20r1%20%2B%20r2%0Ag%20%3D%20B(d%2C%204)%0Ab%20%3D%20B(d%2C%208)%0Asetup(r%2Cg%2Cb)&
width=256&
height=256&
srs=EPSG%3A3857&
bbox=10488383.273178745,3248267.954006849,10527519.031660756,3287403.7124888618
'''

#def ret(projWin, coord_sys):
#    print(projWin,coord_sys,'-------------------------------')
#    return HttpResponse([coord_sys, projWin])

def get_dataset(layer='http://mobileapp.nesdr.gov.in/out2019.tif', projWin=[10566654.790142765,3169996.4370428305,10605790.548624776,3209132.19552484], coord_sys="EPSG:4326"):
    projWin = coord(projWin, coord_sys)
    dataset = gdal.Open(
        '/vsicurl/'+layer,
        gdal.GA_ReadOnly
        )
    out = gdal.Warp('', dataset, width=256, height=256, outputBounds=projWin, format='MEM')
    return out

class B():
    def __init__(self,dataset=None, band_no=0, band=None, ip_minR=0, ip_maxR=2500):
        #print(band_no, dataset)
        if dataset is None:
            self._band = band
        else:
            self._band = norm(x=np.array(dataset.GetRasterBand(band_no).ReadAsArray()),ip_minR=ip_minR,ip_maxR=ip_maxR)
    
    @property
    def band(self):
        return self._band
    
    def __add__(self,y):
        return B(band=self._band+y.band)
    
    def __sub__(self, y):
        return B(band=self._band-y.band)
    
    def __mul__(self, y):
        if isinstance(y,B):
            return B(band=np.multiply(self._band,y.band))
        else:
            return B(band=self._band * y)
    
    def __truediv__(self, y):
        if isinstance(y,B):
            return B(band=np.divide(self._band, y.band, out=np.zeros_like(self._band), where=y.band!=0, casting="unsafe"))
        else:
            return B(band=self._band/y)

def setup(
    R, G=None, B=None,
    weight=None, 
    op_minR=0, op_maxR=1, 
    op_minG=0, op_maxG=1, 
    op_minB=0, op_maxB=1,  
    ip_minR=-0.5, ip_maxR=0.8, 
    ip_minG=-0.5, ip_maxG=0.8, 
    ip_minB=-0.5, ip_maxB=0.8,
    cmap='std'
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
        im = np.array(norm(
            x = weight[0]*R.band,
            op_minR=op_minR, op_maxR=op_maxR,
            ip_minR=ip_minR, ip_maxR=ip_maxR))
        im = apply_cmap(im, cmap)
    else:
        im = np.dstack(norm(
            x=weight[0]*R.band, 
            y=weight[1]*G.band, 
            z=weight[2]*B.band,
            op_minR=op_minR, op_maxR=op_maxR,
            op_minG=op_minG, op_maxG=op_maxG,
            op_minB=op_minB, op_maxB=op_maxB,
            ip_minR=ip_minR, ip_maxR=ip_maxR,
            ip_minG=ip_minG, ip_maxG=ip_maxG,
            ip_minB=ip_minB, ip_maxB=ip_maxB))
    _, ar = cv2.imencode('.png',im)
    response = HttpResponse(ar.tobytes(),content_type="image/png")
    return response

def apply_cmap(im, cmap):
    if cmap=='red':
        return np.dstack((np.zeros(im.shape),np.zeros(im.shape),im))
    elif cmap=='green':
        return np.dstack((np.zeros(im.shape),im,np.zeros(im.shape)))
    elif cmap=='blue':
        return np.dstack((im,np.zeros(im.shape),np.zeros(im.shape)))
    else:
        return im

'''def setup(R, G=None, B=None, weight=None, minR=0, maxR=1, minG=0, maxG=1, minB=0, maxB=1):
    if weight is None:
        weight = [1,1,1]
    elif len(weight) < 3:
        weight = [weights[0]] * 3
    if G is None and B is None:
        grayscale = True
        R = norm(R.band, G, B, minR, maxR, minG, maxG, minB, maxB) * weight[0]
    else:
        grayscale = False
        R = R.band
        G = G.band
        B = B.band
        R, G, B = norm(R, G, B, minR, maxR, minG, maxG, minB, maxB)
        R, G, B = R * weight[0], G * weight[1], B * weight[2]
    if G is None and B is None:
        grayscale = True
    else:
        grayscale = False
    return to_map(R=R, G=G, B=B, grayscale=grayscale)'''