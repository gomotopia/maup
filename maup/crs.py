"""
    ~~/maup/crs.py~~

    Written by @maxhully in March '19 and tested in June '20'19. 
    Additional notes by @gomotopia, May 2021. 

    Simple wrapper that checks that input CRS geodataframes match.

    Used by /maup/indexed_geometries.py

    Notes
    -----

    Attributes
    ----------

    Examples
    -------

"""

from functools import wraps


def require_same_crs(f):
    """Very simple wrapper that compares parameter Coordinate Reference Systems
    and raises an error if they mismatched.

    Parameters
    ----------   
    f : function

    Returns
    -------
    function 
        Valid function whose input geopanadas.GeoDataFrames is an
        assured match. 

    Raises
    ------
    TypeError
        Raised parameter geopandas.GeoDataFrames is mismatched.

    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        geoms1, geoms2, *rest = args
        if not geoms1.crs == geoms2.crs:
            raise TypeError(
                "the source and target geometries must have the same CRS. {} {}".format(
                    geoms1.crs, geoms2.crs
                )
            )
        return f(*args, **kwargs)
    return wrapped
