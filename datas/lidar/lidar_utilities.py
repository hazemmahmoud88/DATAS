# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 10:21:21 2022

@author: Maurice Roots

Lidar Utilities

Originally Written in Matlab by Ruben Delgado
Translated to Python by Noah Sienkiewicz
Editted and Implemented by Maurice Roots

"""
# Data Rangling
from scipy.interpolate import interp1d
import pandas as pd
import numpy as np

#%%

def calc_beta_rayleigh(wavelength, P, T, nanometers=True):
    if nanometers is True: wavelength = wavelength * 10**-9
    beta_rayleigh = 2.938e-32 * (P/T) * (wavelength**(-4.0117))
    return beta_rayleigh

def calc_number_density(pressure, temperature, celsius=True):
    """Calculate Number Density
        
        Input           
            pressure        -> array-like, profile of pressure
            temperature     -> array-like, profile of temperature
            celsius         -> True, Falce: option for Kelvin or Celius tempurature
        
        Output
            number desnsity -> array-like, profile of number density (molecules / m^-3)
    """
    
    kB = 1.38064852e-23 # (m2 kg s-2 K-1)
    if celsius is True :
        ND = pressure/(kB*(temperature+273.15))
    else: ND = pressure/(kB * temperature)
    return ND

def calc_index_refraction(wavelength):
    """the index of refraction of dry air at STP for wavelength lambda in nm"""
    ior = 1.0 + (5791817.0/(238.0185 - (10**6)/wavelength**2)+167909.0/(57.362-(10**6)/wavelength**2))*1e-8
    return ior

def calc_depol_ratio(wavelength):
    """depolarization ratio of gases as a function of the wavelength lambda in nm"""

    wavelengths = np.array([200.,  205.,  210.,  215.,  220.,
                  225.,  230.,  240.,  250.,  260.,
                  270.,  280.,  290.,  300.,  310.,  
                  320.,  330.,  340.,  350.,  360.,
                  370.,  380.,  390.,  400.,  450.,  
                  500.,  550.,  600.,  650.,  700.,  
                  800.,  850.,  900.,  950.,  1000.,
                  1064.])
    
    depolarize = np.array([0.0454545,  0.0438372,  0.0422133,  0.0411272,  0.0400381,
                  0.0389462,  0.0378513,  0.0367534,  0.0356527,  0.0345489,
                  0.033996,   0.0328878,  0.0323326,  0.0317766,  0.0317766,
                  0.0312199,  0.0306624,  0.0306624,  0.0301042,  0.0301042,
                  0.0301042,  0.0295452,  0.0295452,  0.0295452,  0.0289855,
                  0.028425,   0.028425,  0.0278638,  0.0278638,  0.0278638,
                  0.0273018,  0.0273018,  0.0273018,  0.0273018,  0.0273018,
                  0.0273018])
    
    depol = interp1d(wavelengths,depolarize,kind='linear')(wavelength)
    return depol

def calc_rayleigh_scat_cross(wavelength):
    """ Calculates the Rayleigh scattering cross section per molecule [m^-3] for lambda in nm.
    """
    nstp = 2.54691e25
    rs = (1e36*24*np.pi**3*(calc_index_refraction(wavelength)**2-1)**2)
    rs /= (wavelength**4*nstp**2*(calc_index_refraction(wavelength)**2+2)**2)
    rs *= ((6+3*calc_depol_ratio(wavelength))/(6-7*calc_depol_ratio(wavelength)))
    return rs

def calc_rayleigh_extinction(wavelength, numberDensity):
    """This calculates the Rayleigh extinction coefficient in [km^-1]
        
        Input
            numberDensity       -> array-like, number density profile (molecules / m^-3)
            wavelength          -> float, wavelength (nm)
        
        Output 
            rayleigh extintion  -> rayleigh extinction coefficient (km^-1)
    """
    rayleighExtinction = numberDensity*calc_rayleigh_scat_cross(wavelength)*1000
    return rayleighExtinction

def calc_rayleigh_trans(rayleigh_extinction, altitude_profile, kilometers=True):
    """Calculates the Rayleigh Transmission Profile
    """
    if kilometers is True: altitude_profile = altitude_profile / 1000
    int_alpha = [rayleigh_extinction * (altitude_profile[i] - altitude_profile[i-1]) for i in np.arange(1, len(altitude_profile))] 
    # print(int_alpha)
    rayleigh_trans = np.exp(-2 * np.sum(int_alpha))
    return rayleigh_trans

def calc_rayleigh_beta_dot_trans(wavelength, pressure, temperature, altitude, nanometers=True, kilometers=True, celsius=True):
    beta = calc_beta_rayleigh(wavelength, pressure, temperature, nanometers=nanometers)
    numberDensity = calc_number_density(pressure, temperature, celsius=celsius)
    alpha = calc_rayleigh_extinction(wavelength, numberDensity)
    rayleigh_trans = calc_rayleigh_trans(alpha, altitude, kilometers=kilometers)
    beta_dot_trans = beta * rayleigh_trans
    return (beta_dot_trans, beta, numberDensity, alpha, rayleigh_trans)
    

def binned_alts(data_array, altitude, bins=np.arange(0, 15000, 100)):
        data = pd.DataFrame({"data":data_array, "altitude":altitude})
        data["Alt_Bins"] = pd.cut(sonde.HGHT, bins=bins)
        new = data.groupby("Alt_Bins").mean().reset_index()
        return new

        
#%%
if __name__ == "__main__":
    names=["PRES", "HGHT", "TEMP", "DWPT", "RELH", "MIXR", "DRCT", "SKNT", "THTA", "THTE", "THTV"]
    
    sondePath = r"C:/Users/meroo/OneDrive - UMBC/Class/Class 2022/PHYS 650/lidar/data/IAD_20200308_0Z.txt"
    
    sonde = pd.read_csv(sondePath, skiprows=5, nrows=108-5, sep="\s+", names=names)
    
    wavelength = 1064; pressure = sonde["PRES"]; temperature=sonde["TEMP"]; altitude=sonde["HGHT"]
    
    
    beta_dot_trans, beta, numberDensity, alpha, rayleigh_trans = calc_rayleigh_beta_dot_trans(wavelength,
                                                                                              pressure, 
                                                                                              temperature, 
                                                                                              altitude)
    import matplotlib.pyplot as plt
    plt.plot(beta_dot_trans, sonde["HGHT"])
    
    test = binned_alts(beta_dot_trans, sonde["HGHT"])