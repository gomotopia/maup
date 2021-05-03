"""
    ~~/maup/adjacencies.py~~

    Written and commented by @maxhully between April '19 and March '20. 
    Addditional commentary by @gomotopia, May 2021. 

    Used by maup/repair.py

    Uses geopandas.GeoSeries.intersection to check if a pair of shapes have
    an intersection. An intersection can be similiar points or lines. If the
    areas of these intersetions are non-zero, then they are overlapped. If the
    If there is only one zero-area intersection, they are Queen adjacent.
     _ _ _ 
    |_|_|_|<- Corner pieces are often only Queen adjacencies  
    |_|_|_|<- whereas side pieces are both Rook and Queen adjacencies
    |_|_|_|   becaues they share both corners and sides as zero-area intersections. 
    
"""

import warnings

from geopandas import GeoSeries

from .indexed_geometries import IndexedGeometries
from .progress_bar import progress


class OverlapWarning(UserWarning):
    """Raises UserWarning if any shapes overlap. To be expanded
    later. 


    Raises
    ------
    UserWarning, in time. 

    Returns
    -------
    null
    """
    pass


class IslandWarning(UserWarning):
    """Raises UserWarning if any shape is an island, without
    adjacencies. To be expanded later. 


    Raises
    ------
    UserWarning, in time. 

    Returns
    -------
    null
    """
    pass


def iter_adjacencies(geometries):
    """A generator that creates an enumerated list of adjacent shapes. 

    Takes a list of of geometries and creates a query of possible neighboring
    shapes. We then filter our shapes we've looked at before to prevent double-
    counting. If a possible intersection is found to be non-empty or null,
    is is yielded. 

    Parameters
    ----------
    geometries : pandas.geoDataFrame
        Candidates for adjacent shapes. 

    Yields
    -------
    int, int, shapely.BaseGeometry
        Returns enumeration, with indicies, of a tuple of a 
        pair of geometries and their intersection. 

    Raises
    ------

    """
    indexed = IndexedGeometries(geometries)
    for i, geometry in progress(indexed.geometries.items(), len(indexed.geometries)):
        possible = indexed.query(geometry)
        possible = possible[possible.index > i]
        inters = possible.intersection(geometry)
        inters = inters[-(inters.is_empty | inters.isna())]
        for j, inter in inters.items():
            yield (i, j), inter


def adjacencies(
    geometries, adjacency_type="rook", *, warn_for_overlaps=True, warn_for_islands=True
):
    """Returns adjacencies between geometries. The return type is a
    `GeoSeries` with a `MultiIndex`, whose (i, j)th entry is the pairwise
    intersection between geometry `i` and geometry `j`. We ensure that
    `i < j` always holds, so that any adjacency is represented just once
    in the series.

    Combines iterated adjacencies into a geopandas.GeoSeries. 

    Note
    ----
    A rook adjacency exists if two or more intersections exist between
    border i and j, especially if one is a point! Queen adjacencies may
    only have one point in overlap.  

    Returns
    -------
    geopandas.GeoSeries
        Multi-indexed series of intersections described by the index of two 
        shapes.

    Raises
    ------
    ValueError
        Ensures that the type of adjacency is "rook" or "queen." 
    OverlapWarning
        If the intersection is more than just a point or line, 
        there is an overlap! 
    IslandWarning  
        Takes the set of all indexes and removes any that belongs
        to an intersected pair. If any index is not part of a pair,
        then its geometry is an island and the IslandWarning is raised. 
    """
    if adjacency_type not in ["rook", "queen"]:
        raise ValueError('adjacency_type must be "rook" or "queen"')

    index, geoms = zip(*iter_adjacencies(geometries))
    inters = GeoSeries(geoms, index=index, crs=geometries.crs)

    if adjacency_type == "rook":
        inters = inters[inters.length > 0]

    if warn_for_overlaps:
        overlaps = inters[inters.area > 0]
        if len(overlaps) > 0:
            warnings.warn(
                "Found overlapping polygons while computing adjacencies.\n"
                "This could be evidence of topological problems.\n"
                "Indices of overlaps: {}".format(set(overlaps.index)),
                OverlapWarning,
            )

    if warn_for_islands:
        islands = set(geometries.index) - set(i for pair in inters.index for i in pair)
        if len(islands) > 0:
            warnings.warn(
                "Found islands.\n" "Indices of islands: {}".format(islands),
                IslandWarning,
            )

    return inters
