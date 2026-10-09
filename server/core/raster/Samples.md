# Samples
## Sample URLs
### Sample request
http://127.0.0.1:8000/wms/?service=WMS&request=GetMap&layers=&styles=&format=image%2Fjpeg&transparent=false&version=1.1.1&request_script=d%20%3D%20get_dataset()%0Ar%20%3D%20B(dataset%3Dd%2C%20band_no%3D3)%0Ag%20%3D%20B(dataset%3Dd%2C%20band_no%3D4)%0Ab%20%3D%20B(dataset%3Dd%2C%20band_no%3D8)%0Aresponse%20%3D%20setup(%0A%20%20r%2Cg%2Cb%0A)&click_hash=1625623494166&width=256&height=256&srs=EPSG%3A3857&bbox=10527519.031660756,3248267.954006849,10566654.790142765,3287403.7124888618

<strong>Separated:</strong><br />
http://127.0.0.1:8000/wms/?<br />
service=WMS&<br />
request=GetMap&<br />
layers=&<br />
styles=&<br />
format=image%2Fjpeg&<br />
transparent=false&<br />
version=1.1.1&<br />
request_script=d%20%3D%20get_dataset()%0Ar%20%3D%20B(dataset%3Dd%2C%20band_no%3D3)%0Ag%20%3D%20B(dataset%3Dd%2C%20band_no%3D4)%0Ab%20%3D%20B(dataset%3Dd%2C%20band_no%3D8)%0Aresponse%20%3D%20setup(%0A%20%20r%2Cg%2Cb%0A)&<br />
click_hash=1625623494166&<br />
width=256&<br />
height=256&<br />
srs=EPSG%3A3857&<br />
bbox=10527519.031660756,3248267.954006849,10566654.790142765,3287403.7124888618

### URL Format
http://[Domain]/wms/?<br />
service=WMS&<br />
request=GetMap&<br />
layers=&<br />
styles=&<br />
format=image%2Fjpeg&<br />
transparent=false&<br />
version=1.1.1&<br />
request_script=[Encoded User Script]&<br />
click_hash=[Session Hash]&<br />
width=256&<br />
height=256&<br />
srs=EPSG%3A3857&<br />
bbox=10527519.031660756,3248267.954006849,10566654.790142765,3287403.7124888618<br />

Except request_script and click_hash, other field are automatically filled by leaflet as part of WMS Tile request.

## Sample Scripts

### Raster Plot
```python
graph = rasterPlot(
  layer='./main/out2019.tif',
  coordinate=[94.976,27.167],
  coord_format='EPSG:4326'
)
```

### Print Functionality
```python
d = get_dataset(resample=True)
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
print(ndvi.band)
```

### PCA
```python
d = get_dataset()
pca = RasterPCA(n_components = 1)
data = {
  'layer':'aa',
  'bands':[2,3,4,5,6,7]
}
pca.fit(data)
response = setup(R=pca.transform(dataset=d,n_bands=[2,3,4,5,6,7]))
```

### False Colour Composite
```python
d = get_dataset()
r = B(dataset=d, band_no=3)
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
response = setup(
  r,g,b
)
```

### Simple bandwise arithmetic operations
```python
d = get_dataset()
r1 = B(dataset=d, band_no=3)
r2 = B(dataset=d, band_no=1)
r = r1 + r2
response = setup(
  r,
  ip_minR=0, ip_maxR=2000
)
```

### NDVI
```python
d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(
  ndvi,
  ip_minR=-0.5,ip_maxR=3000,
)
```

### Comparison operator [Binary Result]
```python
d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
r = ndvi>0.5 # Threshold value
response = setup(
  r,
  ip_minR=-0.5,ip_maxR=3000,
)
```

### Random Forest Classifier Prediction
```python
d = get_dataset()
rf = RandomForest(saved_path='./main/model1.joblib')
colors = dict((
    (0, (0, 0, 0)),  # Nodata
    (1, (0, 150, 0)),  # Forest
    (2, (0, 0, 255)),  # Water
    (3, (0, 255, 0)),  # Herbaceous
    (4, (160, 82, 45)),  # Barren
    (5, (255, 0, 0))  # Urban
))
rf.colormap = colors
response = setup(
    R=rf.predict(d,[1,2,3,4,5,6,7]).prediction_map,
    ip_minR=1, ip_maxR=7,
    cmap=colors
)
```

### Random Forest Classifier Training
```python
d = get_dataset()
rf = RandomForest(max_depth=2, n_estimators=500)
colors = dict((
    (0, (0, 0, 0)),  # Nodata
    (1, (0, 150, 0)),  # Forest
    (2, (0, 0, 255)),  # Water
    (3, (0, 255, 0)),  # Herbaceous
    (4, (160, 82, 45)),  # Barren
    (5, (255, 0, 0))  # Urban
))
rf.colormap = colors
data = {
		'layer':'aa',
  	'coord_format':'EPSG:4326',
  	'bands':[2,3,4,5],
  	'data':[
      	{'coordinates':[94.939,27.357],'labels':1},
        {'coordinates':[95.051,27.911],'labels':2},
        {'coordinates':[94.627,27.839],'labels':1},
        {'coordinates':[94.844,27.921],'labels':3},
        {'coordinates':[95.028,27.790],'labels':2},
        {'coordinates':[95.104,27.672],'labels':2},
        {'coordinates':[95.014,27.576],'labels':3},
        {'coordinates':[94.210,27.203],'labels':1},
        {'coordinates':[94.369,27.552],'labels':1},
        {'coordinates':[94.036,27.993],'labels':3},
        {'coordinates':[94.718,27.879],'labels':3},
        {'coordinates':[94.780,27.627],'labels':1},
        {'coordinates':[94.490,27.555],'labels':2},
        {'coordinates':[94.752,27.526],'labels':1},
        {'coordinates':[95.089,27.065],'labels':2}]
}
rf.fit(data)
response = setup(
    R=rf.predict(d,[2,3,4,5]).prediction_map,
    ip_minR=1, ip_maxR=7,
    cmap=colors
)
```

### Convolution Operation
```python
d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(
				R=ndvi.conv2D(kernel=[[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        )
```
