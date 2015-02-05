name = "Main KA"

def run(isotherm, components, steps):
    """return a path inside the hdf5 file to the required attribute and an index.
    If the item is not a sequence return a None for the index."""
    if isotherm != 'STERIC_MASS_ACTION':
        return None, None
    if 'Main' not in components:
        return None, None
    return '/input/model/adsorption/SMA_KA', components.index('Dimer')