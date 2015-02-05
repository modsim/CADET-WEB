name = "Velcoity"

def run(isotherm, components, steps):
    """return a path inside the hdf5 file to the required attribute and an index.
    If the item is not a sequence return a None for the index."""
    return '/input/model/VELOCITY', None