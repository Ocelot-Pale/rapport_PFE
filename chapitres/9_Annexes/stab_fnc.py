import numpy as np

def evaluate_stab_ImEx222(ze , zi): 
    GAMMA = (2-np.sqrt(2))/2
    DELTA = 1 - 1/(2*GAMMA)
    u1 = (1 + GAMMA * ze)/(1 - GAMMA * zi) 
    u2 = (1 + (1-GAMMA) * zi * u1 + DELTA * ze + (1-DELTA) * ze * u1) / (1 - GAMMA * zi)
    return np.abs(u2)

def evaluate_stab_ImEx232(ze,zi) : 
    GAMMA = (2-np.sqrt(2))/2
    DELTA = -2 * np.sqrt(2) / 3
    u1 = (1 + GAMMA * ze)/ (1 - GAMMA * zi)
    u2 = (1 + DELTA * ze + (1-DELTA) * ze *u1 + (1-GAMMA) * zi * u1) / (1 - GAMMA*zi)
    u_fin = 1 + (1-GAMMA)*zi*u1 + GAMMA*zi*u2 + (1-GAMMA)*ze*u1 + GAMMA*ze*u2
    return np.abs(u_fin)

def evaluate_stab_RKE2(ze,zi) : 
    z = ze+zi
    return np.abs(1+z+(z**2)/2)

def evaluate_stab_RKI2(ze,zi) : 
    ze = ze/2
    GAMMA=1 - np.sqrt(2)/2
    z = ze+zi
    u1 = 1/(1-GAMMA*z)
    u2 = (1 + (1-2*GAMMA)*z*u1)/(1-GAMMA*z)
    return np.abs(1+.5*z*(u1 + u2))


def evaluate_stab_SplittingRK2(ze,zi):
    R_e = evaluate_stab_RKE2(ze,0)
    R_i = evaluate_stab_RKI2(0,zi)
    return np.maximum(R_e,R_i)
