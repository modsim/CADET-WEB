name = "Salt Concentration During Elution"

def run():
    settings = {}
    settings["SENS_ABSTOL"] = 1.0e-12
    settings["SENS_COMP"] = 0
    settings["SENS_FD_DELTA"] = 0.01
    settings["SENS_NAME"] = "CONST_COEFF"
    settings["SENS_SECTION"] = 2
    return settings