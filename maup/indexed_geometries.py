"""
    ~~/maup/indexed_geometries.py~~

    Written by @maxhully in March '19 with corrections in March '20. 
    Contributions by @tylerjarvis and @madeleinegoertz, early '20. 

    Commentary by @gomotopia, May 2021. 

    Class used as primary shape object for performing calculations. 

    Uses Shapely PreparedGeometries "A geometry prepared for efficient
    comparison to a set of other geometries" and STRtree, that is, the
    Sort-Tile-Recursive algorithm for finding "nearby or nearest neighbors."

"""

import pandas
from shapely.prepared import prep
from shapely.strtree import STRtree
from .progress_bar import progress


def get_geometries(geometries):
    """Returns geometry as 'geometry.' Equivalent to object.geometries. 

    Parameters
    ----------   
    geometries : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame   
        Returns geometries of object or input geometries as default. 

    Raises
    ------

    Examples
    --------

    """
    return getattr(geometries, "geometry", geometries)


class IndexedGeometries:
    """Geometries for calculation with added STRTree index.

    Adds new index column to DataFrame containing geometries. 

    Attributes
    ----------
    geometry : pandas.DataFrame
        Collection of geometries for use in calculations.
    spatial_index : shapely.STRtree
        Shapely STRtree of included geometries.
    index : pandas.Series
        Reference index of cinstance shapes. 
    """    

    def __init__(self, geometries):
        """Creates IndexedGeometries object given set of geometries by generating
        incremental and STRtree indexes. 

        Parameters
        ----------
        geometries : pandas.DataFrame
            Relevant shapes that require indexing.
        """
        self.geometries = get_geometries(geometries)
        for i, geometry in self.geometries.items():
            geometry.index = i
        self.spatial_index = STRtree(self.geometries)
        self.index = self.geometries.index

    def query(self, geometry):
        """Take a geometry and returns indexes of shapes returned by
        the STRTree spatial query. 

        Relevant indicies, returned by the shapely query, are used to 
        filter out and return relevant geometries from instance geometries. 

        Parameters
        ----------
        geometry : shapely.Polygon
            Reference geometry containing extent that requests intersecting
            IndexedGeometries from spatial_index query. 

        Returns
        -------
        pandas.DataFrame
            Returns geometry objects in self.spatial_index (STRtree) whose
            extents intersect with the geometry parameter.  

        Raises
        ------

        """
        relevant_indices = [geom.index for geom in self.spatial_index.query(geometry)]
        relevant_geometries = self.geometries.loc[relevant_indices]
        return relevant_geometries

    def intersections(self, geometry):
        """Take a geometry and returns indexes of shapes returned by
        the STRTree spatial query.
        
        Relevant geometries are returned by the shapely query and  i.e.
        whose extents intersect with example geometry.

        Parameters
        ----------
        geometry : shapely.Polygon
            Reference geometry used to for creating intersections upon instance
            IndexedGeometries.

        Returns
        -------
        pandas.DataFrame
            Returns DataFrame of geometry objects from IndexedGeometries that are
            split into intersetions based on parameter geometry.  

        Raises
        ------

        """
        relevant_geometries = self.query(geometry)
        intersections = relevant_geometries.intersection(geometry) # Uses shapely intersection?
        return intersections[-(intersections.is_empty | intersections.isna())]

    def covered_by(self, container):
        """Takes a container and returns IndexedGeometries which fit completely
        inside. 

        Using container, a list of nearby shapes is queried. Then, using a 
        Prepared version of the container, relevant_geometries are filtered
        on whether shapely.Prepared determines that container covers each
        relevant geometry. 

        Parameters
        ----------
        container : shapely.BaseGeometry
            Larger shape used for query those geometries encompassed within. 

        Returns
        -------
        pandas.DataFrame
            Returns DataFrame of geometry objects contained within larger, 
            container shape.   

        Raises
        ------

        """
        relevant_geometries = self.query(container)
        prepared_container = prep(container)
        return relevant_geometries[relevant_geometries.apply(prepared_container.covers)]

    def assign(self, targets):
        """Assigns instance relevant geometries to a usually larger 
        shape within the targets DataFrame.

        The geometries of the target shapes are collected. Then, each
        larger shape is used to generate a list of instance shapes that
        it covers. These shapes are concatenated and reindexed back to
        their original designation. 

        Parameters
        ----------
        targets : pandas.DataFrame
            Larger shape used as targets of assignment. 

        Returns
        -------
        pandas.DataFrame
            Returns DataFrame of geometry objects with new assignments of
            target shapes that cover it. 

        Raises
        ------

        """
        target_geometries = get_geometries(targets)
        groups = [
            self.covered_by(container).apply(lambda x: container_index)
            for container_index, container in progress(
                target_geometries.items(), len(target_geometries)
            )
        ]
        assignment = pandas.concat(groups).reindex(self.index)
        return assignment

    def enumerate_intersections(self, targets):
        """A generator that creates an enumerated list of intersections 
        from the instance geometries generated by each usually larger target
        shape. 

        Parameters
        ----------
        targets : pandas.DataFrame
            Larger shapes used to split smaller, instance geometries. 

        Yields
        -------
        int, int, shapely.BaseGeometry
            Returns enumeration, with indicies, of each target i and each
            instance geometry j and the resulting geometry. 

        Raises
        ------

        """
        target_geometries = get_geometries(targets)
        for i, target in progress(target_geometries.items(), len(target_geometries)):
            for j, intersection in self.intersections(target).items():
                yield i, j, intersection
