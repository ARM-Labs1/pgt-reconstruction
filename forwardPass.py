import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid as cumtrapz

def loadEnergyDict(file = "EnergyRanges.csv"):
    '''
    Function in order to extract range and energy values from the attached CSV file

    ARGUMENTS
    file - csv file of interpolated values for the energy in MeV a proton must have for depths between 0 and 300mm in 1mm increments

    RETURNS
    - A dictionary where the range is the key and the energy is the value
    '''
    df = pd.read_csv(file)
    return dict(zip(df['Range_mm'], df['Energy_MeV']))

energies = loadEnergyDict()

def CreatePhantom():
    '''
    Function in order to create the phantom, A 1D model of water with length 300mm

    RETURNS
    phantom - array of x locations for each 'bin' in the phantom
    phantomXY - array of x-y locations for each 'bin' in the phantom, all y values are 0
    '''
    phantom = np.linspace(0, 300, 301)
    phantomXY = np.column_stack((phantom, np.zeros_like(phantom)))

    return phantom, phantomXY


def CalculateDistances(phantomXY, detectorLocation):
    '''
    Function to calculate the distances between the 'bins' of the phantom, and the location of the detector

    ARGUMENTS
    PhantomXY - [[a1, b1], [a2, b2], ... , [an, bn]] Array of coordinates of each 'bin' in the phantom
    detectorLocation - [c, d] Array holding the x and y position of the detector

    RETURNS
    distances - array of vectors representing distances between bins and detector
    distMag - magnitude of the distances
    '''

    distances = []

    for bin in phantomXY:                           # Loops over the bins, calculates the distances, and appends to 'distances' array
        distance = detectorLocation-bin
        distances.append(distance)

    distMag = []
    
    for distance in distances:                      # Loops over the distances, finds their magnitudes, and appends them to 'distMag' array
        distMag.append(np.sqrt((distance[0])**2 + (distance[1])**2))

    return np.array(distances), np.array(distMag)


def CreateBraggCurve (depths, braggPosition, peakHeight = 1.0, entranceDose = 0.3, peakWidth = 8, falloffSteepness = 5):
    '''
    Function to create the Bragg curve using a gaussian distribution

    This function combines three components in order to create an approximation of the Bragg curve
    1. A Constant plateu for the enterence region - constant low dose of 0.3
    2. A Gaussian distribution centrered at the peak height for the peak
    3. An exponential falloff past the Bragg peak

    ARGUMENTS:
    depths - array of depths from x=0, represents the bins in the phantom model
    braggPosition - (mm) position of bragg peak
    peakHeight - The height of the peak
    entranceDose = the dose before the beak
    peakWidth - (mm) width of the peak
    falloffSteepness - measure of how steep the falloff after the peak is

    RETURNS:
    dose - array of values corresponding to the 'dose' of radiation deposited at each bin
    '''
    
    # Entrance region (constant)
    entrance = entranceDose*np.ones_like(depths)

    # Bragg peak (gaussian)
    peak = peakHeight * np.exp(-(depths-braggPosition)**2 / (2*peakWidth**2))

    # Apply rapid fall-off after peak
    falloffMask = depths > braggPosition            # Falloff mask only selects depths past the Bragg peak                                              
    falloff = np.exp(-(depths[falloffMask] - braggPosition)/(falloffSteepness))

    # Combine all regions
    dose = entrance + peak
    dose[falloffMask] = (entrance[falloffMask] + peak[falloffMask]) * falloff        # Drop off values past the peak

    return dose


def velocities(phantom, initialE):
    '''
    Function to calculate the velocities of the proton at each depth

    ARGUMENTS
    phantom - array of depth values within the phantom
    initialE - initial energy of the proton

    RETURNS
    - Array of velocities at each depth
    '''

    vel = np.array([])

    
    for z in phantom:                                       # Iterates over all depths
        energy = energies[z]                                # MeV - Finds the associated proton energy needed to reach that depth in water 
        energy = initialE - energy                          # MeV - finds the energy at that depth, given the initial energy

        if energy <= 0:                                     # Ensures energies after the bragg peak are equal to zero
            energy = 0

        # Calculates the velocity given the energy using the relativistic formula
        beta = np.sqrt(1-((938.3)/(energy + 938.3))**2)
        velocity = beta * 3e8
        vel = np.append(vel, velocity)

    # Sets the initial velocities at 0mm and 1mm depth to the initial velocity
    vel[0] = 0.662 * 3e8
    vel[1] = 0.662 * 3e8

    return vel


def ProtonTime(velocities, phantom):
    '''
    Function to calculate the proton travel time at each depth

    ARGUMENTS
    velocities - array of velocities at each depth
    phantom - array of depths

    RETURNS
    tp - array of time needed to each each depth in the phantom
    '''

    integrand = np.array([])

    # Finds the reciprocal of the velocity, sets it to zero if velocity is zero
    for velocity in velocities:
        if velocity == 0:
            integrand = np.append(integrand, 0)
        else:
            integrand = np.append(integrand, 1/velocity)


    # Uses Scipy's 'cumulative_trapezoid' function in order to calculate the integrals
    tp = cumtrapz(integrand, phantom, initial=0)

    return tp


def SimulateBurst(phantom, distMag, peak, pPB, yiel, dArea, mu, tp, dTRes):
    '''
    Function to simulate a burst of protons, given the number of protons per burst. Takes into account attenuation effects and 
    timing jitter of the detector

    ARGUMENTS
    phantom - the model in question
    distMag - magnitudes of distances from the depths of the phantom to the detector
    peak    - location of the Bragg peak
    pPB     - number of protons fired per burst
    yiel    - yield of gamma photons per proton
    dArea   - area of the detector
    mu      - The attentuation coefficient
    tp      - time of flight of the proton at each depth
    dTRres  - Timing resolution of the detector in seconds

    RETURNS
    An array of timing measurements, each measurement is repeated based on the number of photons emitted at each bin
    '''

    # Finds the normalised percentage of dose at each depth
    dose = CreateBraggCurve(phantom, peak)
    dose /= np.max(dose)

    
    nEmit = pPB * yiel * dose                                                   # Calculates the number of gamma rays emitted at each depth
    attenuationFactor = np.exp(-mu*(distMag/10))                                # Calculates the attenuation factor

    # Calculates the mean photons recieved by the detector at each depth, given the solid angle of the detector
    mean = nEmit * ((dArea)/(4 * np.pi * (distMag/1000)**2)) * attenuationFactor    

    # Takes a poisson distribution of the mean and adds background radiation
    k = np.random.poisson(lam=mean)
    k += np.random.poisson(2, size=k.shape)

    # Calculates the time of flight and adds with the proton time of flight to get the total measured time
    yTOF = distMag/3e8
    baseTime = yTOF + tp
    measuredTime=np.repeat(baseTime, k)
    #measuredTime = yTOF + tp

    # Adds timing jitter to the measured time, simulating as a normal distribution
    timingJitter = np.random.normal(0, dTRes, size=measuredTime.shape)
    measuredTime += timingJitter

    return measuredTime