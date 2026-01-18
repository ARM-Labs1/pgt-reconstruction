import numpy as np
import matplotlib.pyplot as plt

def Reconstruction(phantom, detectorData, tp, gammaTOF, tBinWidth, sigma, dArea, distMag, aFactor=1):
    '''
    Function to reconstruct the data given the measurement recieved by the detector

    ARGUMENTS
    phantom         - array of depths within the phantom
    detectorData    - array of measurements of time
    tp              - array of time taken for proton to reach certain depths
    gammaTOF        - array of gamma flight times from each mm in the phantom
    tBinWidth       - Width of the bins when binning the time data
    sigma           - Timing resolution of the detector system
    dArea           - Area of the detector
    distMag         - array of distances from each point in the phantom to the detector
    aFactor         - Attenuation factor - default value = 1 representing no attenuation

    RETURNS
    correctedRecon  - An array holding the corrected reconstruction data, each element is ordered based on the depth of the phantom 
    '''

    tExpected = tp + gammaTOF                       # Calculating the expected times, since we know the gamma and proton time-of-flight  

    # Grouping values in detectorData that fall into specific ranges which are the bins, where the bins are defined by tBinWidth
    # tCounts - how many photons fell into each bin
    tCounts, tBinEdges = np.histogram(detectorData, bins=np.arange(detectorData.min(), detectorData.max() + tBinWidth, tBinWidth))
    tBinCentres = (tBinEdges[:-1] + tBinEdges[1:])/2    #Specific time value representing each bin

    # Initialise a variable to hold the reconstructed data with the same size as the phantom array
    reconstructed = np.zeros_like(phantom, dtype=float)


    for i, (tBin, count) in enumerate(zip(tBinCentres, tCounts)):               # Loops over all the bins
        if count == 0:                                                          # If there is no data in the bin, it is passed
            continue

        tDiffs = np.abs(tExpected-tBin)                 # The difference between the bin's centre and each expected time value is calculated

        # Gaussian weighting function calculates weight for each spacial bin - bins who are close to the matched time have higher weighting
 
        weights = np.exp(-tDiffs**2 / (2*sigma**2))         
        weights = weights/np.sum(weights)               # Normalising the weights

        reconstructed += count*weights                  # adding the contributions of those weights, scaling them based on the number of counts


    # Sensitivity correction accounts for geometric detection bias - bins closer to the detector naturally contribute more counts due to
    # their proximity. Corrected data also factors in the attenuation of the gamma photons
    sensitivity = (dArea) / (4 * np.pi * (distMag/1000)**2)
    correctedRecon = reconstructed / (sensitivity*aFactor)

    return correctedRecon


def Plot(phantom, reconstruction, dose):
    '''
    Function to plot the theoretical and reconstructed data

    ARGUMENTS
    phantom - depth profile of the phantom
    reconstruction - normalised reconstruction data
    dose - normalised dose data
    '''
    dose /= np.max(dose)

    plt.figure()
    plt.plot(phantom, reconstruction/np.max(reconstruction), label="Reconstructed data")
    plt.plot(phantom, dose, label = "Theoretical dose distribution")
    plt.legend()
    plt.grid()
    plt.xlabel("Tissue Depth (mm)")
    plt.ylabel("Relative Dose")
    plt.show()

