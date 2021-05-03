"""
    ~~/maup/repair.py~~

    Written and commented by @maxhully and @RKBuck1
    between Jun. '19 and Mar. '20. 
    Additional commentary by @gomotopia, May 2021. 

    Base heavily on functions written by Mary Barker, @marybarker
    from July to August 2018 with contributions by @drdeford. 
    check_shapefile_connectivity.py script in @gerrymandr/Preprocessing.

    Used to repair common geometric issues like holes, gaps. Allows for
    the splitting of leveled indexes and the absorbtion of holes and 
    overlaps.
"""


import pandas

from geopandas import GeoSeries
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from .adjacencies import adjacencies
from .assign import assign_to_max
from .crs import require_same_crs
from .indexed_geometries import get_geometries
from .intersections import intersections


def holes_of_union(geometries):
    """Returns any holes in the union of the given geometries.
    
    Takes union of the entire set of geometries and uses repair.holes to
    returns the holes across the entire set of geometries. 

    Parameters
    ----------
    geometries: geopandas.GeoSeries
    
    Returns
    -------
    geopandas.GeoSeries
        Same geometries repaired to remove holes.

    Raises
    ------
    TypeError
        If data type is not of Geometries or Multipolygons
    """
    geometries = get_geometries(geometries)
    if not all(
        isinstance(geometry, (Polygon, MultiPolygon)) for geometry in geometries
    ):
        raise TypeError("all geometries must be Polygons or MultiPolygons")

    union = unary_union(geometries)
    series = holes(union)
    series.crs = geometries.crs
    return series


def holes(geometry):
    """Returns any holes in the union of the given geometries.
    
    If the geometry is a Multipolygon, we return a GeoSeries of Polygons that is
    each a hole found in polygon.interiors for each polygon within the 
    Multipolygon. 

    If the geometry is a Polygon, then we return a GeoSeries of the single
    polygon.

    Parameters
    ----------
    geometry: geopandas.MultiPolygon or geopandas.Polygon
    
    Returns
    -------
    geopandas.GeoSeries
        Shapes representing holes within the geometry parameter.

    Raises
    ------
    TypeError
        If data type is not a Geometry or Multipolygons
    """
    if isinstance(geometry, MultiPolygon):
        return GeoSeries(
            [
                Polygon(list(hole.coords))
                for polygon in geometry.geoms
                for hole in polygon.interiors
            ]
        )
    elif isinstance(geometry, Polygon):
        return GeoSeries([Polygon(list(hole.coords)) for hole in geometry.interiors])
    else:
        raise TypeError("geometry must be a Polygon or MultiPolygon to have holes")


def close_gaps(geometries, relative_threshold=0.1):
    """Closes gaps between geometries by assigning the hole to the polygon
    that shares the most perimeter with the hole.

    If the area of the gap is greater than `relative_threshold` times the
    area of the polygon, then the gap is left alone. The default value
    of `relative_threshold` is 0.1. This is intended to preserve intentional
    gaps while closing the tiny gaps that can occur as artifacts of
    geospatial operations. Set `relative_threshold=None` to close all gaps.
    
    Collects holes of the entire area, by repair.holes_of_union and 
    applies repair.absorb_by_shared_perimeter, which returns a geoSeries
    of repaired shapes. 

    Parameters
    ----------
    geometries: geopandas.GeoSeries
        Relevant geometries for repair of type Polygon or Multipolygon.
    relative_threshold: float
        Threshold of size to absorb small hole as proportion of
        larger polygon. Default, 0.1 or 10%.
    
    Returns
    -------
    geopandas.GeoSeries
        Same as parameter geometries, but with holes below certain 
        size absorbed within original set. 

    Raises
    ------
    TypeError
        If data type is not a Geometry or Multipolygons
    """
    geometries = get_geometries(geometries)
    gaps = holes_of_union(geometries)
    return absorb_by_shared_perimeter(
        gaps, geometries, relative_threshold=relative_threshold
    )


def resolve_overlaps(geometries, relative_threshold=0.1):
    """For any pair of overlapping geometries, assigns the overlapping area to the
    geometry that shares the most perimeter with the overlap. Returns the GeoSeries
    of geometries, which will have no overlaps.

    If the ratio of the overlap's area to either of the overlapping geometries'
    areas is greater than `relative_threshold`, then the overlap is ignored.
    The default `relative_threshold` is `0.1`. This default is chosen to include
    tiny overlaps that can be safely auto-fixed while preserving major overlaps
    that might indicate deeper issues and should be handled on a case-by-case
    basis. Set `relative_threshold=None` to resolve all overlaps.

    Creates IndexedGeometry from parameter geometries and filters for 
    overlaps of non-zero area, buffered to repair crossing and other errors.
    For any relative_threshold, a pair of areas assigned to each of the
    overlapped districts are created. Each side of the pair is checked
    if it meets the threshold. These overlaps are then stripped of
    their index and absorbed back into the larger polygons by 
    repair.absorb_by_shared_perimeter. 

    Parameters
    ----------
    geometries: geopandas.GeoSeries
        Relevant geometries for repair of type Polygon or Multipolygon.
    relative_threshold: float
        Threshold of size to absorb small hole as proportion of
        each larger polygon. Default, 0.1 or 10%.
    
    Returns
    -------
    geopandas.GeoSeries
        Same as parameter geometries, but with overlaps below certain 
        size absorbed within original set, each absorbed into larger
        polygon with longest shared perimeter. 

    Raises
    ------

    """
    geometries = get_geometries(geometries)
    inters = adjacencies(geometries, warn_for_islands=False, warn_for_overlaps=False)
    overlaps = inters[inters.area > 0].buffer(0)

    if relative_threshold is not None:
        left_areas, right_areas = split_by_level(geometries.area, overlaps.index)
        under_threshold = ((overlaps.area / left_areas) < relative_threshold) & (
            (overlaps.area / right_areas) < relative_threshold
        )
        overlaps = overlaps[under_threshold]

    if len(overlaps) == 0:
        return geometries

    to_remove = GeoSeries(
        pandas.concat([overlaps.droplevel(1), overlaps.droplevel(0)]), crs=overlaps.crs
    )
    with_overlaps_removed = geometries.difference(to_remove)

    return absorb_by_shared_perimeter(
        overlaps, with_overlaps_removed, relative_threshold=None
    )


def split_by_level(series, multiindex):
    """Returns a tuple of identical shapes from the series 

    Parameters
    ----------
    series: shapely.Polygon or shapely.Multipolygon
        Original set of shapes that carry multiple indexes.
    multiindex: pandas.Series
        The multi-level series of indexes. 
    
    Returns
    -------
    tuple 
        Tuple of similar Shapely.Polygons or Shapely.Multipolygons paired
        with each of its different indexes. 

    Raises
    ------

    """
    return tuple(
        multiindex.get_level_values(i).to_series(index=multiindex).map(series)
        for i in range(multiindex.nlevels)
    )


@require_same_crs
def absorb_by_shared_perimeter(sources, targets, relative_threshold=None):
    """Takes smaller shapes and absorbs it into an adjacent shape selected by
    longest shared perimeter. 

    If there are no sources, then the targets are returned as complete.

    If there are no targets, then an error is raised.

    Intersections between sources and targets are collected and 
    the number of intersections are used the weight for an assignment. 
    If there is a relative_threshold, each source is checked for
    validity. Then, all source pieces assigned to a target shape are
    combined by union into a new GeoSeries, which is then combined by
    union to the original targets. 

    Combined shapes are reindexed back to the targets together with targets
    that were left unchanged and returned.

    Parameters
    ----------
    sources: geoPandas.geoSeries
        Collection of smaller shapes to absorb into larger shapes.
    targets: geoPandas.geoSeries
        Larger shapes where smaller shapes are absorbed.
    relative_threshold: float
        Percentage underwhich smaller shapes are absorbed. Default, None,
        that is, all shapes large and small are absorbed. 
    
    Returns
    -------
    geoPandas.geoSeries
        Collection of Shapely.Polygons or Shapely.Multipolygons after
        smaller shapes have been absorbed. 

    Raises
    ------
    IndexError
        Arises when there are no targets to absorb the source shapes. 
    """
    if len(sources) == 0:
        return targets

    if len(targets) == 0:
        raise IndexError("targets must be nonempty")

    inters = intersections(sources, targets, area_cutoff=None).buffer(0)
    assignment = assign_to_max(inters.length)

    if relative_threshold is not None:
        under_threshold = (
            sources.area / assignment.map(targets.area)
        ) < relative_threshold
        assignment = assignment[under_threshold]

    sources_to_absorb = GeoSeries(
        sources.groupby(assignment).apply(unary_union), crs=sources.crs,
    )

    result = targets.union(sources_to_absorb)

    # The .union call only returns the targets who had a corresponding
    # source to absorb. Now we fill in all of the unchanged targets.
    result = result.reindex(targets.index)
    did_not_absorb = result.isna() | result.is_empty
    result.loc[did_not_absorb] = targets[did_not_absorb]

    return result
