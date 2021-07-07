# map-compiler
### Folder Structure
```
map-compiler
├── custom_map_server [Django Server]
├── nbs [Jupyter notebook]
└── front_end [html]
```
### Django Server
Django server runs on PostgreSQL, custom username and password can be changed or a change of SQL server can be made in `./custom_map_server/custom_map_server/settings.py` on line 98.
```
custom_map_server
├── custom_map_server [Project folder]
└── main [Application Folder]
    ├── compiler_scripts
    └── Standard Django files
```
compiler_scripts -- contains functions accessible by front end compiler and supporting functions.<br />
Other files are the standard django files, including `views` and `models` modules.
<br />
Cached models stored in `./custom_map_server/cache` folder. Path can be changed from `./custom_map_server/main/compiler_scripts/storage_paths`
<br />
For more info <a href="https://github.com/rahatsantosh/map-compiler/blob/main/custom_map_server/main/compiler_scripts/README.md"> Compiler_scripts README.md</a>

### NBS
Jupyter Notebooks for testing compiler_scripts modules and Cloud Optimized Geotiff access from GDAL, and for RandomForest implementation on GDAL Datasets.

### Front End
html file for front end compiler. Sends WMS or standard http requests to django backend depending on user script format.