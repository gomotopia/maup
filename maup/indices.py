"""
    ~~/maup/crs.py~~

    Written by @maxhully in March 2019.
    Commentary notes by @gomotopia, May 2021. 

    Takes geometries and applies simple, sequential indexes.
    Used by /maup/indexed_geometries.py

    Notes
    -----

    Attributes
    ----------

    Examples
    -------

"""

import geopandas
import pandas

from .indexed_geometries import get_geometries


def get_geometries_with_range_index(geometries):
    """Reindexes geometries to sequential index from 0 to length
    of geometries. 

    Parameters
    ----------   
    geometries : geopandas.GeoDataFrame
        GeoDataFrame of geometries in need of simplified reindexing. 

    Returns
    -------
    geopandas.GeoDataFrame   
        Returns GeoDataFrame frame with only geometries and simple index.  

    Raises
    ------
    TypeError 
        Input must be GeoDataFrame

    Examples
    --------

    """
    gdf = geopandas.GeoDataFrame({"geometry": get_geometries(geometries)}).set_index(
        pandas.RangeIndex(len(geometries))
    )
    return gdf.geometry
