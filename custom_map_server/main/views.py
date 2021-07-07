# Django views definition
from django.http import HttpResponse
import re
import requests
import json
from io import StringIO
from contextlib import redirect_stdout

# When request is meant for console or graph.
# Returns http json response
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


# When request is meant for map, as a WMS response.
# Returns http png response
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
    """
    A class to perform sandbox execution of user script. Additionaly blacklisting commands.
    Also sets up execution environment and separates requests depending on expected responses
    to different views.

    ...

    Attributes
    ----------
    request : string
        Modified user script, with added statements
    globals : builtin_function_or_method
        Global environment, to be passed for execution environment.
    console : boolean
        Checks if console print function present in script
    graph : django.http.response [json response]
        Json response for graph
    map : django.http.response [png response]
        WMS response for map
    error_check : boolean
        Check if error exists, to print to console.

    Methods
    -------
    execute: [property]
        Execute modified script in environment, and save required responses to respective attributes
    """
    def __init__(self, editor, globals, coord_sys, sess_key, projWin=None):
        """
        Constructor
        Also makes necessary additions to front end code editor script i.e. request attribute.

        Parameters
        ----------
            editor : string
                URL request from frontend
            coord_sys : string
                Coordinate system used for projWin, by leaflet.js
            sess_key : string
                Unique session hash key. Can club together multiple requests from single session.
            projWin : list
                Bounding box coordinates from WMS request.
        """
        # Extract front end code editor script from url request
        request = requests.utils.unquote(str(editor))
        regexp = re.compile(".*\&request_script=\s*([^&]*)")
        self.request = regexp.search(str(request)).group(1)
        if projWin is None:
            # If no projWin, attach coord_sys argument to get_dataset function
            self.request = re.sub("get_dataset\(",f'get_dataset(coord_sys="{coord_sys}",',self.request)
        else:
            # Attach coord_sys and projWin arguments to get_dataset function
            self.request = re.sub("get_dataset\(",f'get_dataset(projWin={projWin}, coord_sys="{coord_sys}",',self.request)
        # Attach necessary import statements
        self.request = 'from .compiler_scripts.user_func import *\n' + self.request
        # If RandomForest command exists add, session key as argument
        self.request = re.sub("RandomForest\(",f'RandomForest(sess_key="{sess_key}",',self.request)
        # If PCA command exists add, session key as argument
        self.request = re.sub("RasterPCA\(",f'RasterPCA(sess_key="{sess_key}",',self.request)
        self.globals = globals # Current host environment to be transferred to exec
        # Check if print statement exists. Comments are removed at frontend, hence doesnt account commented prints
        self.console = bool(re.search("print", self.request))
        # Map response attribute
        self.map = None
        # Graph response attribute
        self.graph = None
        # Error handler flag
        self.error_check = False
    
    @property
    def execute(self):
        """
        Execute modified script in environment, using exec statement and separate required responses
        to map, console and graph attributes. Also, perform error handling and returning to console.
        """
        _locals = {}
        if self.console:
            # If print function exists, redirect all stdout to op variable
            op = StringIO()
            with redirect_stdout(op):
                try:
                    # Execute script
                    exec(self.request, self.globals, _locals)
                except Exception as err:
                    # If error caught, set error_check flag to true
                    self.error_check = True
                    # Parse error message
                    error = parse_error(err)
                else:
                    error = ""
        else:
            try:
                # Execute script
                exec(self.request, self.globals, _locals)
            except Exception as err:
                # If error caught, set error_check flag to true
                self.error_check = True
                # Parse error message
                error = parse_error(err)
            else:
                error = ""

        try:
            self.console = op.getvalue() + "\n" + error
        except:
            self.console = error

        try:
            # map response in script stored to 'response' variable response by user
            self.map = _locals['response']
        except:
            self.map = None

        try:
            # graph response in script stored to 'graph' variable response by user
            self.graph = _locals['graph']
        except:
            self.graph = None

def parse_error(e):
    """
    Parse error message to user readable format. And remove backend information.

    Parameters
    ----------
        e : Error Class [Depending on type of error]

    Returns
    -------
        Error in user readable format.
    """
    # Convert error to string
    error = str(e)
    # Change line number accounting for added lines to front end script
    regexp = re.compile("line *([0-9]+)")
    try:
        err_lines = int(regexp.search(error).group(1)) - 2
    except:
        return error
    return re.sub("line *[0-9]+",f'line {err_lines}',error)