from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from django.shortcuts import render
from .gdal_translate import *
from .custom_func import *
import re
import requests
from .models import Model_cache

def homepage(request):
    return HttpResponse('hello')

'''
Sample url request:
http://127.0.0.1:8000/wms/?service=WMS&request=GetMap&
layers=&styles=&format=image%2Fjpeg&
transparent=false&version=1.1.1&
input_band=B08%2CB02%2CB03&
min_threshold=0%2C0%2C0&
max_threshold=1%2C1%2C1&
grayscale=true&
weight=1%2C1%2C1&
width=256&height=256&srs=EPSG%3A3857&
bbox=10488383.273178745,3169996.4370428305,10527519.031660756,3209132.19552484
'''

def warp_mode1(request):
    request = requests.utils.unquote(str(request))

    regexp = re.compile(".*\&bbox=\s*([^\n\r'>]*)")
    projWin = regexp.search(str(request)).group(1)
    projWin = projWin.split(',')
    projWin = list(map(float, projWin))

    regexp = re.compile(".*\&input_band=\s*([^\n\r&'>]*)")
    input_band = regexp.search(str(request)).group(1)
    input_band = input_band.split(',')

    regexp = re.compile(".*\&min_threshold=\s*([^\n\r&'>]*)")
    min_threshold = regexp.search(str(request)).group(1)
    min_threshold = min_threshold.split(',')
    min_threshold = list(map(float, min_threshold))

    regexp = re.compile(".*\&max_threshold=\s*([^\n\r&'>]*)")
    max_threshold = regexp.search(str(request)).group(1)
    max_threshold = max_threshold.split(',')
    max_threshold = list(map(float, max_threshold))

    regexp = re.compile(".*\&weight=\s*([^\n\r&'>]*)")
    weight = regexp.search(str(request)).group(1)
    weight = weight.split(',')
    weight = list(map(float, weight))

    return get_translate(
        projWin,
        input_band,
        weight,
        minR=min_threshold[0], maxR=max_threshold[0],
        minG=min_threshold[1], maxG=max_threshold[1],
        minB=min_threshold[2], maxB=max_threshold[2]
    )

'''
Sample url script:
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

def warp_mode2(request):
    #global projWin, coord_sys
    regexp = re.compile(".*\&click_hash=\s*([^&\n\r'>]*)")
    clickHash = regexp.search(str(request)).group(1)

    '''EXISTS_FLAG = True
    if not Model_cache.objects.filter(sessHash=clickHash).exists():
        Model_cache.
        EXISTS_FLAG = False
    sess_key = [request.session.session_key, EXISTS_FLAG]'''

    regexp = re.compile(".*\&bbox=\s*([^\n\r'>]*)")
    projWin = regexp.search(str(request)).group(1)
    projWin = projWin.split(',')
    projWin = list(map(float, projWin))

    '''regexp = re.compile(".*\&click_hash=\s*([^\n\r'>]*)")
    clickHash = regexp.search(str(request)).group(1)'''

    coord_sys = "EPSG:4326"
    request = Script(str(request), globals=globals(), projWin=projWin, coord_sys=coord_sys,sess_key=clickHash)

    return request.execute

#TODO: src and dest srs

def warp(request):
    return warp_mode2(request)

class Script():
    def __init__(self, editor, globals, projWin, coord_sys,sess_key):
        request = requests.utils.unquote(str(editor))
        regexp = re.compile(".*\&request_script=\s*([^&]*)")
        self.request = regexp.search(str(request)).group(1)
        self.request = re.sub("get_dataset\(",f'get_dataset(projWin={projWin}, coord_sys="{coord_sys}"',self.request)
        self.request = 'from .custom_func import *\n' + self.request
        self.request = re.sub("RandomForest\(",f'RandomForest(sess_key="{sess_key}",',self.request)
        self.globals = globals
    
    @property
    def execute(self):
        _locals = {}
        exec(self.request, self.globals, _locals)
        return _locals['response']
