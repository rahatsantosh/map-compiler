# Compiler Scripts
Functions implementable by front end compiler and supporting functions.

### Structure
Structure of modules within compiler script module.
```
compiler_scripts
├── core [User accessible]
|   ├── get_dataset [Function]
|   └── B [Class]
├── storage_paths [User in-accessible] [Paths to caches]
├── user_func [User accessible]
|   ├── rasterPlot [Function]
|   └── setup [Function]
├── ml [User accessible]
|   ├── RasterPCA [Class]
|   └── RandomForest [Class]
└── helpers [User in-accessible]
    ├── dict_hash [Function]
    ├── get_dataset_ [Function]
    ├── prepare_data [Function]
    ├── coord [Function]
    ├── apply_cmap [Function]
    ├── single_band_norm [Function]
    └── norm [Function]
```
`helpers` module contains user inaccessible functions used by other functions and classes internally. <br/>
`core` module contains basic arithmetic and statistical as well as functions to load GDAL datasets. <br/>
`storage_paths` module contains all paths to cache models. <br/>
`user_func` module contains output functions accesed by user to view map, or plot. Printing to console commands are handled within the django views. <br/>
`ml` module contains machine learning models that can be applied on datasets or certain bands. <br/>
<br />
Errors are also handled and returned for printing to frontend console.
<hr>
Sample scripts in Samples.md file.