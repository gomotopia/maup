"""
    ~~/maup/assign.py~~

    Written by @maxhully between March '19 and March '20. 
    With contributions by @RKBuck1.
    Commentary by @gomotopia, May 2021. 

    Notes
    -----
    Suppress some unhelpful warnings with the following...
    import warnings; warnings.filterwarnings('ignore', 'GeoSeries.isna', UserWarning)

    Attributes
    ----------

    Examlpes
    -------

"""

from .indexed_geometries import IndexedGeometries
from .intersections import intersections
from .crs import require_same_crs


@require_same_crs
def assign(sources, targets):
    """Assign source geometries to targets. A source is assigned to the
    target that covers it, or, if no target covers the entire source, the
    target that covers the most of its area.

    Receieves first assignment using assign_by_covering. Unassigned
    sources are collected and are then assigned_by_area. Original assignment
    is then updated, the assignment name is reset and assignment is returned. 

    Parameters
    ----------   
    sources : geopandas.geodataframe.GeoDataFrame
        Source units to be assigned up, usually smaller districts.

    targets : geopandas.geodataframe.GeoDataFrame
        Target units for smaller units to be assigned to, usually 
        larger districts.

    Returns
    -------
    geopandas.geodataframe.GeoDataFrame
        Assignments returned, following target data type. Errors are ignored. 

    Raises
    ------

    """
    assignment = assign_by_covering(sources, targets)
    unassigned = sources[assignment.isna()]
    assignments_by_area = assign_by_area(unassigned, targets)
    assignment.update(assignments_by_area)
    assignment.name = None
    return assignment.astype(targets.index.dtype, errors="ignore")


def assign_by_covering(sources, targets):
    """Creates Indexed Geometry object from sources and returns a class 
    method assignment assigning smaller units that are 100% within target
    unit. 

    Parameters
    ----------   
    sources : geopandas.geodataframe.GeoDataFrame
        Source units to be assigned up, usually smaller districts.

    targets : geopandas.geodataframe.GeoDataFrame
        Target units for smaller units to be assigned to, usually 
        larger districts.

    Returns
    -------
    maup.IndexedGeometries 
        Assignments returned, following target data type. Errors are ignored. 

    Raises
    ------

    """
    indexed_sources = IndexedGeometries(sources)
    return indexed_sources.assign(targets)


def assign_by_area(sources, targets):
    """Wraps assign_to_max function with default parameters of using area 
    intersections as weight, with area_cutoff set to zero. 

    Parameters
    ----------   
    sources : geopandas.geodataframe.GeoDataFrame
        Source units to be assigned up, usually smaller districts.

    targets : geopandas.geodataframe.GeoDataFrame
        Target units for smaller units to be assigned to, usually 
        larger districts.

    Returns
    -------
    maup.IndexedGeometries ?

    Raises
    ------

    """
    return assign_to_max(intersections(sources, targets, area_cutoff=0).area)


def assign_to_max(weights):
    """Assigns smaller unit to inteserction with heaviest weight. Drops source
    label using drop_source_label.

    Parameters
    ----------   
    weights : geopandas.geodataframe.GeoDataFrame ? result of intersections?
        Intersections carrying value by which to weight assignments. 

    Returns
    -------
    maup.IndexedGeometries ?

    Raises
    ------

    """
    return weights.groupby(level="source").idxmax().apply(drop_source_label) # parameter here?


def drop_source_label(index):
    """Replaces source label with next value in index. 

    Parameters
    ----------   
    index : geopandas.geodataframe.GeoDataFrame, optional? 
        Index column to replace  

    Returns
    -------
    ?
        Next value of index?

    Raises
    ------

    """
    return index[1]
