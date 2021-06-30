from django.http import HttpResponse
import re
import requests
import json
from io import StringIO
from contextlib import redirect_stdout


def nonmaprequest(request):
    regexp = re.compile(".*click_hash=\s*([^&\n\r'>]*)")
    clickHash = regexp.search(str(request)).group(1)

    coord_sys = "EPSG:4326"
    request = Script(str(request), globals=globals(), coord_sys=coord_sys,sess_key=clickHash)
    request.execute
    
    response = {
        "console":request.console,
        "graph":request.graph,
        "error":request.error_check,
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

class Script():
    def __init__(self, editor, globals, coord_sys, sess_key, projWin=None):
        request = requests.utils.unquote(str(editor))
        regexp = re.compile(".*\&request_script=\s*([^&]*)")
        self.request = regexp.search(str(request)).group(1)
        if projWin is None:
            self.request = re.sub("get_dataset\(",f'get_dataset(coord_sys="{coord_sys}",',self.request)
        else:
            self.request = re.sub("get_dataset\(",f'get_dataset(projWin={projWin}, coord_sys="{coord_sys}",',self.request)
        self.request = 'from .compiler_scripts.user_func import *\n' + self.request
        self.request = re.sub("RandomForest\(",f'RandomForest(sess_key="{sess_key}",',self.request)
        self.request = re.sub("RasterPCA\(",f'RasterPCA(sess_key="{sess_key}",',self.request)
        self.globals = globals
        self.console = bool(re.search("print", self.request))
        self.map = None
        self.graph = None
        self.error_check = False
    
    @property
    def execute(self):
        _locals = {}
        if self.console:
            op = StringIO()
            with redirect_stdout(op):
                try:
                    exec(self.request, self.globals, _locals)
                except Exception as err:
                    self.error_check = True
                    error = parse_error(err)
                else:
                    error = ""
        else:
            try:
                exec(self.request, self.globals, _locals)
            except Exception as err:
                self.error_check = True
                error = parse_error(err)
            else:
                error = ""

        try:
            self.console = op.getvalue() + error
        except:
            self.console = error

        try:
            self.map = _locals['response']
        except:
            self.map = None

        try:
            self.graph = _locals['graph']
        except:
            self.graph = None

def parse_error(e):
    error = str(e)
    regexp = re.compile("line *([0-9]+)")
    try:
        err_lines = int(regexp.search(error).group(1)) - 2
    except:
        return error
    return re.sub("line *[0-9]+",f'line {err_lines}',error)