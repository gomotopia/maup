
"""
    ~~/maup/normalize.py~~

    Written and commented by @maxhully Thurs., Jun. 20, 2019. 
    Addditional commentary by @gomotopia, May 2021. 

    Takes a series of MultiIndexed weights and normalizes them with
    respect to one level (level 0 by default).

    Offered as standalone utility. 

    Example
    -------

    Let's take the following multi-indexed pandas.MultiIndex

    * *
    x y weight | normalized weights
    0 1 10     | 1/3 (from 10/30...)
    0 2 20     | 2/3 (20/30)
    1 2 25     | 5/8 (25/40)
    1 3 15     | 3/8 (15/40)
    1 4 0      | 0/8 ( 0/40)
    2 4 30     | 1/1 (30/30)

    First, since level=0 is the default, we take a look at column x as the
    index, which in reality could represent smaller districts. The sum of 
    weights with index 0 is 30, 1 -> 40 and 2 -> 30. Thus, the expected
    values are shown above: each value is normalize to the sum of the
    weights of their first index. 
"""

from pandas import Series

def normalize(weights, level=0):
    """Creates a pandas.Series of weights taking their index, 0-level by
    default. Then, we sum over the weights to create denominators and take
    the proportion of each weight as the new normalized weights, replacing any
    errors with zero.

    Parameters
    ----------
    weights: pandas.Series
        List of weights

    Returns
    -------
    pandas.Series
        Weights that are now normalized as proportions to the sum of the weights
        with shared index.
    """
    source_assignment = Series(
        weights.index.get_level_values(level), index=weights.index
    )
    denominators = source_assignment.map(weights.groupby(source_assignment).sum())
    return (weights / denominators).fillna(0)
