import numpy as np
from forwardPass import *
from Reconstruction import *

detectorLocation = [350, 50]            # Located 5cm away from the end of the phantom, 5cm laterlally
peak = 150                              # mm - our desired peak of the bragg curve


# Creating the 1D depth axis:
# While the 'phantom' will be located in a 1D line, 2D coordinates will be used so each bin will be represented as [x, 0]
phantom, phantomXY = CreatePhantom()


# Now to calculate distances from each of the bins to the detector
distances, distMag = CalculateDistances(phantomXY, detectorLocation)


# Implement the theoretical Bragg peak curve using a Gaussian distribution
dose = CreateBraggCurve(phantom, peak)
dose /= np.max(dose)                        # Normalise the curve


# Now to model the time of flight to each of the bins
# We need the Energy of the proton, which for a range of 150mm, the initial energy must be approx. 145.722222 MeV
# In order to find the the time of flight, we'll integrate over the reciprocal of the velocities between 0 and a certain depth
# And we'll integrate for every z value

velocities = velocities(phantom, 145.722222)                # Retrieving the velocities of the proton at each depth
tp = ProtonTime(velocities, phantom)                        # Time of flight of a proton at each depth



# For simplicity, we will assume that the number of PGs emitted is roughly proportional to the output of the above function

nPrim = 5e13                                # This is the number of protons per burst
Y = 1e-4                                    # This is the yield of gamma photons for every proton
detectorArea = 0.0025                       # m^2 - Area of the detector, will use to find solid angle
mu = 0.06                                   #cm^-1          Attenuation coefficient for...
dTR = 0.5e-9                                # 500 ps - Detector timing resolution
gammaTOF = distMag/3e8                      # Time of flight for gamma photons


pPB = [5e13]
names = ["5e13 photons"]
reconData = []
results = []

for burst in pPB:
    detectorData = SimulateBurst(phantom, distMag, peak, pPB=burst, yiel=Y, dArea=detectorArea, mu=mu, tp= tp, dTRes = dTR)
    reconstruction = Reconstruction(phantom, detectorData, tp, gammaTOF, 0.05e-9, dTR, detectorArea, distMag, (np.exp(-mu*(distMag/10))))
    reconData.append(reconstruction)

    peakPosition = phantom[np.argmax(reconstruction)]
    peakError = abs(peakPosition-150)
    results.append({'protons': pPB, 'error (mm)': str(peakError)})

plt.figure()
plt.plot(phantom, dose, label = "Theoretical dose distribution")

plt.grid()
plt.xlabel("Tissue Depth (mm)")
plt.ylabel("Relative Dose")

for i, array in enumerate(reconData):
    plt.plot(phantom, array/np.max(array), label = names[i])

plt.legend()
plt.show()

print(results)