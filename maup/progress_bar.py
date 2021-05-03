"""
    ~~/maup/progress_bar.py~~

    Written and commented by @RKBuck1 and merged on Thu., March 12, 2020. 
    Addditional commentary by @gomotopia, May 2021. 

    Used by maup/repair.py

    Implementation of https://github.com/tqdm/tqdm for progress bars.
    Wrapper written to implement 'with' functionality. 
    
    Example
    -------
    Turn on for the script:

    > maup.progress.enabled = True

    Turn on temporarily:
    
    > with maup.progress():
    >    assignment = maup.assign(precincts, districts)
    
"""


from tqdm import tqdm

class ProgressBar:
    """tqdm produces progress bars that recieve an iterator and
        produces progress bars. 

        Attributes
        ----------
        enabled: bool
            Whether progress bar is active
        _previous_value: bool
            Whether previously toggled
    """
    def __init__(self):
        """To start, progress bar neither nor was enabled.
        """
        self.enabled = False
        self._previous_value = False

    def __call__(self, generator=None, total=None):
        """Add an optional progress bar to a generator. A tqdm progress bar
        will display if the `ProgressBar` is enabled.

        If there's no generator, it returns itself and nothing happens.
        If there's a generator, a tqdm progress bar is created up to
        the total number of the given. 
        """
        if generator is None:
            return self
        if self.enabled:
            return tqdm(generator, total=total)
        return generator

    def __enter__(self):
        """When we begin the 'with' statement, we 
        set the previous value and declare itself
        enabled.
        """
        self._previous_value = self.enabled
        self.enabled = True

    def __exit__(self, *args):
        """When we end a with statement, we reset
        the enabled to the previous value, which could
        be true in the case of nested with statements.
        """
        self.enabled = self._previous_value

progress = ProgressBar()
