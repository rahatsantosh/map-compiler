# Map Compiler

A geospatial analytics platform for on-the-fly processing of Cloud Optimized GeoTIFF (COG) raster data. Users write analysis scripts in a browser-based code editor; the backend compiles them via a sandboxed AST pipeline and serves results as OGC-compliant WMS tiles or JSON responses.

Built during an internship at [NESAC](https://www.nesac.gov.in/) (North Eastern Space Applications Centre).

## Architecture

```
┌─────────────┐       WMS / REST        ┌─────────────────┐      HTTP range     ┌──────────────┐
│   Browser    │ ◄───────────────────► │  Django Server  │ ◄─────────────────► │  COG Rasters │
│  (React UI) │                        │  AST Compiler   │      (GDAL)         │  (local/remote)│
└─────────────┘                        └─────────────────┘                     └──────────────┘
```

- **Client**: React 19 + TypeScript, MapLibre GL JS for maps, CodeMirror 6 for the script editor, ECharts for charting.
- **Server**: Django with an AST-based script compiler. User scripts are parsed, validated against a whitelist, and executed in a sandboxed environment — no `exec()` or `eval()`.
- **Data**: Cloud Optimized GeoTIFF datasets accessed via GDAL. Internal tiling and overviews enable fast sub-region reads at any zoom level.

All raster operations are tile-wise (256×256 resampling), so response times stay consistent regardless of zoom level — a key advantage of the COG format over plain GeoTIFF.

## Features

- **Band math**: NDVI, FCC, and arbitrary band algebra via operator overloading (`B` class)
- **Machine learning**: Random Forest classification and PCA with session-based model caching
- **Convolution**: Custom kernels with configurable strides
- **Statistical plots**: Band value distribution charts via `rasterPlot`
- **Dataset selector**: Browse and load local `.tif` files from the `data/` directory

## Repository Structure

```
map-compiler/
├── server/                 # Django backend
│   ├── config/             #   Project settings & URL config
│   ├── core/               #   Main app (views, models, urls)
│   │   └── raster/         #   Geospatial domain logic (Band class, ML, helpers)
│   └── compiler/           #   AST-based script compiler (parser, validator, executor)
├── web/                    # React frontend (Vite + TypeScript)
│   └── src/
│       ├── components/     #   MapView, Editor, Console, Chart, DatasetSelector
│       └── api/            #   Backend API client
├── data/                   # Datasets directory (gitignored)
├── pyproject.toml          # Python project config, pytest & ruff settings
└── LICENSE
```

## Setup

**Prerequisites**: Python 3.10+, Node.js 20+, [uv](https://docs.astral.sh/uv/), GDAL system library (`libgdal-dev` on Debian/Ubuntu)

```bash
# Clone and enter the project
git clone <repo-url> && cd map-compiler

# System dependency (Debian/Ubuntu)
sudo apt-get install -y libgdal-dev gdal-bin python3-dev

# Python environment
uv venv
uv pip install -e .
uv pip install GDAL==$(gdal-config --version)

# Database
uv run python server/manage.py migrate

# Frontend
cd web && npm install && cd ..

# Place GeoTIFF datasets in data/
mkdir -p data
```

**Run**:

```bash
# Terminal 1: Django server
uv run python server/manage.py runserver

# Terminal 2: Vite dev server (proxies API to Django)
cd web && npm run dev
```

Open `http://localhost:5173` in a browser.

## Tooling

| Tool | Purpose |
|------|---------|
| [ruff](https://docs.astral.sh/ruff/) | Python linter and formatter |
| [pytest](https://docs.pytest.org/) | Python test runner (with pytest-django) |
| [Vite](https://vite.dev/) | Frontend build tool and dev server |
| [TypeScript](https://www.typescriptlang.org/) | Frontend type checking |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first CSS framework |

```bash
# Run Python tests
pytest

# Run frontend type check and build
cd web && npm run build
```

## Background

This platform evaluates the performance of cloud-native geospatial formats for distributed analytics. Key findings from the associated research:

- COG response times range 1.2–30.4s across zoom levels, compared to 20s–2.5hrs for plain GeoTIFF at lower scales
- Internal tiling ensures O(1) pixel access per tile regardless of dataset size
- Session-based mutex synchronization prevents redundant ML model training across concurrent tile requests

For details, see: *"Evaluating the performance of Cloud Native Geospatial format for processing geospatial data stored at distributed locations"*

## License

[MIT](LICENSE)
