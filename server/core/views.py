import json
import re
from urllib.parse import unquote

from django.http import HttpResponse, JsonResponse

from compiler import compile_and_execute
from core.raster.user_func import rasterPlot, setup
from core.raster.core import B, get_dataset
from core.raster.ml import RandomForest, RasterPCA


def _build_compiler_env(coord_sys, proj_win=None, sess_key=""):
    def _get_dataset(**kwargs):
        kwargs.setdefault("coord_sys", coord_sys)
        if proj_win is not None:
            kwargs.setdefault("projWin", proj_win)
        return get_dataset(**kwargs)

    def _random_forest(**kwargs):
        kwargs.setdefault("sess_key", sess_key)
        return RandomForest(**kwargs)

    def _raster_pca(**kwargs):
        kwargs.setdefault("sess_key", sess_key)
        return RasterPCA(**kwargs)

    return {
        "get_dataset": _get_dataset,
        "B": B,
        "setup": setup,
        "rasterPlot": rasterPlot,
        "RandomForest": _random_forest,
        "RasterPCA": _raster_pca,
        "print": print,
        "dict": dict,
        "list": list,
        "int": int,
        "float": float,
        "str": str,
        "range": range,
        "len": len,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "bool": bool,
        "tuple": tuple,
        "type": type,
    }


def _extract_param(raw_url, pattern):
    match = re.search(pattern, raw_url)
    return match.group(1) if match else None


def nonmaprequest(request):
    raw_url = request.get_full_path()
    click_hash = _extract_param(raw_url, r"click_hash=([^&]+)")
    script = _extract_param(raw_url, r"request_script=([^&]+)")

    if not script:
        return JsonResponse({"console": "No script provided", "graph": None, "error": True})

    source = unquote(script)
    env = _build_compiler_env(coord_sys="EPSG:4326", sess_key=click_hash or "")
    result = compile_and_execute(source, env)

    return JsonResponse({
        "console": result.get("console"),
        "graph": result.get("graph"),
        "error": result.get("error", False),
    })


def maprequest(request):
    raw_url = request.get_full_path()
    click_hash = _extract_param(raw_url, r"click_hash=([^&]+)")
    script = _extract_param(raw_url, r"request_script=([^&]+)")
    bbox_str = _extract_param(raw_url, r"bbox=([^&]+)")

    if not script:
        return HttpResponse(status=400)

    source = unquote(script)
    proj_win = [float(x) for x in bbox_str.split(",")] if bbox_str else None
    env = _build_compiler_env(
        coord_sys="EPSG:4326",
        proj_win=proj_win,
        sess_key=click_hash or "",
    )
    result = compile_and_execute(source, env)

    tile_response = result.get("response")
    if tile_response is not None:
        return tile_response

    return HttpResponse(status=204)


def _format_error(error):
    error_str = str(error)
    line_match = re.search(r"line *(\d+)", error_str)
    if line_match:
        corrected = int(line_match.group(1))
        error_str = re.sub(r"line *\d+", f"line {corrected}", error_str)
    return error_str
