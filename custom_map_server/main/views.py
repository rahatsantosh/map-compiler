from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from django.shortcuts import render
from .gdal_translate import *
from .user_func import *
import re
import requests
import json
from io import StringIO
from contextlib import redirect_stdout

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

def nonmaprequest(request):
    regexp = re.compile(".*click_hash=\s*([^&\n\r'>]*)")
    clickHash = regexp.search(str(request)).group(1)

    coord_sys = "EPSG:4326"
    request = Script(str(request), globals=globals(), coord_sys=coord_sys,sess_key=clickHash)
    request.execute
    
    response = {
        "console":request.console,
        "graph":request.graph
    }
    return HttpResponse(json.dumps(response), content_type="application/json")



def maprequest(request):
    regexp = re.compile(".*\&click_hash=\s*([^&\n\r'>]*)")
    clickHash = regexp.search(str(request)).group(1)

    regexp = re.compile(".*\&bbox=\s*([^\n\r'>]*)")
    projWin = regexp.search(str(request)).group(1)
    projWin = projWin.split(',')
    projWin = list(map(float, projWin))

    coord_sys = "EPSG:4326"
    request = Script(str(request), globals=globals(), projWin=projWin, coord_sys=coord_sys,sess_key=clickHash)

    request.execute

    return request.map

#TODO: src and dest srs

class Script():
    def __init__(self, editor, globals, coord_sys, sess_key, projWin=None):
        request = requests.utils.unquote(str(editor))
        regexp = re.compile(".*\&request_script=\s*([^&]*)")
        self.request = regexp.search(str(request)).group(1)
        if projWin is None:
            self.request = re.sub("get_dataset\(",f'get_dataset(coord_sys="{coord_sys}",',self.request)
        else:
            self.request = re.sub("get_dataset\(",f'get_dataset(projWin={projWin}, coord_sys="{coord_sys}",',self.request)
        self.request = 'from .custom_func import *\n' + self.request
        self.request = re.sub("RandomForest\(",f'RandomForest(sess_key="{sess_key}",',self.request)
        self.globals = globals
        self.console = None
        self.map = None
        self.graph = None
        #self.request = self.request[:-1]
    
    @property
    def execute(self):
        _locals = {}
        op = StringIO()
        with redirect_stdout(op):
            exec(self.request, self.globals, _locals)

        try:
            self.console = op.getvalue()
        except:
            self.console = None

        try:
            self.map = _locals['response']
        except:
            self.map = None

        try:
            self.graph = _locals['graph']
        except:
            self.graph = None
