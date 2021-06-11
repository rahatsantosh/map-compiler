# Samples
## Sample Scripts
d = get_dataset(resample=False)
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
#response = setup(ndvi)
#print(ndvi.band)
graph = rasterPlot(d,[94.589,27.523],'EPSG:4326')

d = get_dataset()
r = B(dataset=d, band_no=3)
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
response = setup(
  r,g,b,
  ip_minR=0,ip_maxR=12252,
  ip_minB=0,ip_maxB=12211,
  ip_minG=0,ip_maxG=12536,
)

d = get_dataset()
r1 = B(dataset=d, band_no=3)
r2 = B(dataset=d, band_no=1)
r = r1 + r2
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
response = setup(
  r,g,b,
  ip_minR=0,ip_maxR=1000,
  ip_minB=0,ip_maxB=2000,
  ip_minG=0,ip_maxG=2000,
)

d = get_dataset()
r1 = B(dataset=d, band_no=3)
r2 = B(dataset=d, band_no=1)
r = r1 + r2
response = setup(
  r,
  ip_minR=0, ip_maxR=2000
)

d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(
  ndvi,
  op_minR=0.5,
)

d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(ndvi)

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

d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(
				R=ndvi.conv2D(kernel=[[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        )

