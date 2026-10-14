import re
from pathlib import Path
from urllib.parse import unquote

from compiler import compile_and_execute
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.raster.core import B, get_dataset
from core.raster.ml import RandomForest, RasterPCA
from core.raster.user_func import rasterPlot, setup


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


def list_datasets(request):
    data_dir = Path(settings.DATA_DIR)
    if not data_dir.exists():
        return JsonResponse({"datasets": []})

    paths = sorted(
        p for p in data_dir.rglob("*") if p.suffix.lower() in {".tif", ".tiff"}
    )
    datasets = [
        {"name": p.name, "path": str(p), "size_mb": round(p.stat().st_size / (1024 * 1024), 1)}
        for p in paths
    ]

    return JsonResponse({"datasets": datasets})


@csrf_exempt
def upload_dataset(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "No file provided"}, status=400)

    if not uploaded.name.lower().endswith((".tif", ".tiff")):
        return JsonResponse({"error": "Only .tif/.tiff files are supported"}, status=400)

    data_dir = Path(settings.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    dest = data_dir / uploaded.name

    with open(dest, "wb") as f:
        for chunk in uploaded.chunks():
            f.write(chunk)

    return JsonResponse({"path": str(dest), "name": uploaded.name})
