'''
[User Accessible]
Predefined Machine Learning Algorithms

Classes:
    
    RasterPCA
    RandomForest
'''
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
import os
from ..models import Model_cache
from .helpers import prepare_data, dict_hash
import time
from .core import B, get_dataset
from .storage_paths import *


class RasterPCA():
    """
    A class to perform Principal Component Analysis on multiple Raster Bands.
    Expected usage is compressing multiple bands into a single band.

    ...

    Attributes
    ----------
    pca : sklearn.decomposition._pca.PCA
        sklearn PCA object
    sess_key : string
        Session key to club together multiple requests from single session.

    Methods
    -------
    dump(path:string):
        Save PCA model
    load(path:string):
        Load dumped PCA model
    fit(data:Dictionary):
        Train PCA model
    transform(**kwargs):
        Model inference
    fit_transform(data, **kwargs):
        Perform both training and inference together
    """
    def __init__(self,sess_key,saved_path=None,**kwargs):
        """
        Constructor
        Also, contraints PCA to have only one output component.

        Parameters
        ----------
            sess_key : string
                Unique session hash key. Can club together multiple requests from single session.
            saved_path : string (or) os.path
                If loading saved PCA model, else None
            **kwargs : 
                Arguments for sklearn PCA object
        """
        self.pca = joblib.load(saved_path) if saved_path is not None else PCA(**kwargs)
        self.sess_key = sess_key
        assert self.pca.n_components == 1, "RasterPCA should have only 1 output component. n_components should be 1"
    
    def dump(self, path):
        """
        Save PCA model to custom path.
        Uses joblib.dump

        Parameters
        ----------
            path : string (or) os.path
                Model storage path
        """
        joblib.dump(self.pca, path)
    
    def load(self, path):
        """
        Loads saved PCA object. Uses joblib.load functionality

        Parameters
        ----------
            path : string (or) os.path
                Model storage path
        """
        self.pca = joblib.load(path)
    
    # Private method
    def __prepare_train_data(self,data):
        """
        [Private]
        Training data preperation.
        Loads GDAL dataset and extracts required bands.
        Returns in transposed format for PCA training.

        Parameters
        ----------
            data : Dictionary
                Training data points. Contains layer i.e. link to optimized-Geotiff to be trained
                on and bands to be compressed.
                Format:
                    {
                        'layer':layer,
                        'bands':bands_list
                    }
        
        Returns
        -------
            Training data : np.array
                Shape -> (Raster.XSize * Raster.YSize, len(data['bands']))
        """
        d = get_dataset(layer = data['layer'])
        return np.array(
            [d.GetRasterBand(i).ReadAsArray().ravel() for i in data['bands']]
        ).T
    
    # Private method
    def __prepare_infer_data(self,dataset=None,n_bands=None,bands=None):
        """
        [Private]
        Inference data preperation.
        Loads GDAL dataset and extracts required bands.

        Parameters
        ----------
            dataset : osgeo.gdal.Dataset
                GDAL Dataset object from which raster band is to be extracted
            n_bands : int
                Bands to be extracted
            bands : np.array
                Alternatively, required bands are directly given as an numpy 3D array. In this case
                dataset and band_no parameters are to be left to default
        
        Returns
        -------
            Training data : np.array
                Shape -> (Raster.XSize * Raster.YSize, len(data['bands']))
        """
        if dataset is None and bands is not None:
            X = np.asarray([band.band.ravel() for band in bands]).T
        elif bands is None and dataset is not None:
            X = np.array([dataset.GetRasterBand(i).ReadAsArray().ravel() for i in n_bands]).T
        else:
            exit(0)
        return X
    
    def fit(self, data):
        """
        Fit model to training data.
        Wrapper for sklearn.decomposition._pca.PCA.fit, with added functionality of
        training only one of the multiple requests from a single session. This removes any redundant 
        training sessions.
        Model stored as temporary cache for access by other requests from the same session, or 
        for other training sessions where the data hash is the same.

        Parameters
        ----------
            data : Dictionary
                Training data points. Contains layer i.e. link to optimized-Geotiff to be trained
                on and bands to be compressed.
                Format:
                    {
                        'layer':layer,
                        'bands':bands_list
                    }
        """
        # hash_val can point to models in cache which have been trained on same data.
        hash_val = dict_hash(data)
        modelHashId = self.sess_key + str(hash_val)

        # Finally only one request from each session enters BLOCKED SECTION and trains
        # and caches the model, the rest of the requests simply access the caches model.
        if Model_cache.objects.filter(sessHash=modelHashId).exists():
            i = 0
            m = True # Blocked section flag
            while m:
                # Wait for other requests from same session to exit BLOCKED SECTION
                if i%10000==0:
                    i = 0
                    m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                i += 1
            # Load from cache
            self.load(path=f'{PCA_CACHE}/{self.sess_key}/{hash_val}.joblib')
        else:
            try:
                Model_cache.objects.create(sessHash=modelHashId,blocked=True)
                # BLOCKED SECTION
                if not os.path.exists(f'{PCA_CACHE}/{self.sess_key}'):
                    os.mkdir(f'{PCA_CACHE}/{self.sess_key}')
                # Prepare training data
                X = self.__prepare_train_data(data)
                self.pca.fit(X)
                # Dump to cache
                self.dump(path=f'{PCA_CACHE}/{self.sess_key}/{hash_val}.joblib')
                m = Model_cache.objects.get(sessHash=modelHashId)
                m.blocked = False
                m.save()
                # END OF BLOCKED SECTION
            except:
                # To counter the case when multiple same session requests attempt to enter
                # the blocked session together.
                i = 0
                m = True # Blocked section flag
                while m:
                    # Wait for other requests from same session to exit BLOCKED SECTION
                    if i%10000==0:
                        i = 0
                        m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                    i += 1
                self.load(path=f'{PCA_CACHE}/{self.sess_key}/{hash_val}.joblib')
    
    def transform(self,**kwargs):
        """
        Transform data to single raster band.
        Wrapper for sklearn.decomposition._pca.PCA.transform, with added functionality inbuilt
        data preparation.
        
        Parameters
        ----------
            **kwargs : List
                Arguments for sklearn.decomposition._pca.PCA.transform
        
        Returns
        -------
            Transformed map as an object of .core.B
        """
        X = self.__prepare_infer_data(**kwargs)
        X = self.pca.transform(X)
        X = X.reshape((256,256,self.pca.n_components))
        return B(band=X)
    
    def fit_transform(self, data, **kwargs):
        """
        Perform both training and inference together

        Parameters
        ----------
            data : Dictionary
                Training data points. Contains layer i.e. link to optimized-Geotiff to be trained
                on and bands to be compressed.
                Format:
                    {
                        'layer':layer,
                        'bands':bands_list
                    }
            **kwargs : List
                Arguments for sklearn.decomposition._pca.PCA.transform
        
        Returns
        -------
            Transformed map as an object of .core.B
        """
        self.fit(data)
        return self.transform(**kwargs)


class RandomForest(object):
    """
    A class to perform Random Forest Prediction on GDAL dataset.

    ...

    Attributes
    ----------
    rf : sklearn.ensemble._forest.RandomForestClassifier
        sklearn Random Forest ensemble classifier
    sess_key : string
        Session key to club together multiple requests from single session.
    class_prediction : np.array
        Prediction output

    Methods
    -------
    dump(path:string):
        Save Random Forest Classifier model
    load(path:string):
        Load dumped Random Forest Classifier model
    fit(data:Dictionary):
        Train Random Forest Classifier model
    predict(**kwargs):
        Model inference
    prediction_map:
        Returns prediction map for dataset as an object of .core.B
    """
    def __init__(self,sess_key,saved_path=None,**kwargs):
        self.rf = joblib.load(saved_path) if saved_path is not None else RandomForestClassifier(**kwargs)
        self.class_prediction = None
        self.sess_key = sess_key
    
    def dump(self, path):
        """
        Save RandomForest model to custom path.
        Uses joblib.dump

        Parameters
        ----------
            path : string (or) os.path
                Model storage path
        """
        joblib.dump(self.rf, path)
    
    def load(self, path):
        """
        Loads saved RandomForest object. Uses joblib.load functionality

        Parameters
        ----------
            path : string (or) os.path
                Model storage path
        """
        self.rf = joblib.load(path)
    
    def fit(self, data):
        """
        Fit model to training data.
        Wrapper for sklearn.ensemble._forest.RandomForestClassifier.fit, with added functionality of
        training only one of the multiple requests from a single session. This removes any redundant 
        training sessions.
        Model stored as temporary cache for access by other requests from the same session, or 
        for other training sessions where the data hash is the same.

        Parameters
        ----------
            data : Dictionary
                Training data points. Contains layer i.e. link to optimized-Geotiff to be trained
                on and bands to be compressed.
                Format:
                    {
                        'layer':layer,
                        'coord_format':coord_format,
                        'bands':bands_list
                        'data':[
                            {'coordinates':X,'labels':y},
                            ...
                        ]
                    }
        """
        # hash_val can point to models in cache which have been trained on same data. 
        hash_val = dict_hash(data)
        modelHashId = self.sess_key + str(hash_val)

        # Finally only one request from each session enters BLOCKED SECTION and trains
        # and caches the model, the rest of the requests simply access the caches model.
        if Model_cache.objects.filter(sessHash=modelHashId).exists():
            time.sleep(15)
            i = 0
            m = True # Blocked section flag
            while m:
                # Wait for other requests from same session to exit BLOCKED SECTION
                if i%10000==0:
                    i = 0
                    m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                i += 1
            # Load from cache
            self.load(path=f'{RANDOM_FOREST_CACHE}/{self.sess_key}/{hash_val}.joblib')
        
        else:
            try:
                Model_cache.objects.create(sessHash=modelHashId,blocked=True)
                t = time.time()
                # BLOCKED SECTION
                if not os.path.exists(f'{RANDOM_FOREST_CACHE}/{self.sess_key}'):
                    os.mkdir(f'{RANDOM_FOREST_CACHE}/{self.sess_key}')
                # Prepare training data
                X, y = prepare_data(
                    layer=data['layer'],coord_format=data['coord_format'],data=data['data'],bands=data['bands']
                )
                t = time.time()
                self.rf.fit(X, y)
                # Dump to cache
                self.dump(path=f'{RANDOM_FOREST_CACHE}/{self.sess_key}/{hash_val}.joblib')
                m = Model_cache.objects.get(sessHash=modelHashId)
                m.blocked = False
                m.save()
                # END OF BLOCKED SECTION
            except:
                # To counter the case when multiple same session requests attempt to enter
                # the blocked session together.
                i = 0
                m = True # Blocked section flag
                while m:
                    # Wait for other requests from same session to exit BLOCKED SECTION
                    if i%10000==0:
                        i = 0
                        m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                    i += 1

                self.load(path=f'{RANDOM_FOREST_CACHE}/{self.sess_key}/{hash_val}.joblib')
    
    def predict(self, img, bands):
        """
        Predict class for dataset.
        Wrapper for sklearn.ensemble._forest.RandomForestClassifier.predict, with added functionality inbuilt
        data preparation.
        
        Parameters
        ----------
            **kwargs : List
                Arguments for sklearn.decomposition._pca.PCA.transform
        """
        img = img.ReadAsArray()
        img = np.moveaxis(img, 0, -1)
        img_as_array = np.take(img, bands, 2).reshape(-1,len(bands))
        self.class_prediction = self.rf.predict(img_as_array)
        self.class_prediction = self.class_prediction.reshape(img[:, :, 0].shape)
        
        return self
    
    @property
    def prediction_map(self):
        """
        Returns predicted class map as an object of .core.B
        """
        return B(band=self.class_prediction)

