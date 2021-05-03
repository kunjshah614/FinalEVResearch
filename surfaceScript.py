# set PYTHONPATH=%PYTHONPATH%;C:\Program Files\Dymola 2021\Modelica\Library\python_interface\dymola.egg

import platform
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import time

from dymola.dymola_interface import DymolaInterface

osString = platform.system()
isWindows = osString.startswith("Win")

dymola = None

dymola = DymolaInterface()
dymola.AddModelicaPath('C:/Users/kunjs/Desktop/EVResearch-master')
dymola.ExecuteCommand("Advanced.NumberOfCores = 3")
dymola.cd("C:/Users/kunjs/Desktop/dymDat")

disc = 30
numElements = disc**2
massLowerLimit = 1000#0.1
massUpperLimit = 70000#3
transmissionRatioLowerLimit = 0.1#5
transmissionRatioUpperLimit = 5#50 #update these values

mass = np.linspace(massLowerLimit, massUpperLimit, disc)
transmissionRatio = np.linspace(transmissionRatioLowerLimit, transmissionRatioUpperLimit, disc)

massMesh, transmissionRatioMesh = np.meshgrid(mass, transmissionRatio)

stdEnergy = np.zeros((len(transmissionRatio), len(mass)))
enhEnergy = np.zeros((len(transmissionRatio), len(mass)))

timePerSim = 0.42
inc = 1

print("APPROX " + str(timePerSim*numElements) + " MIN")

for massIndex in range(len(mass)):
    for transmissionRatioIndex in range(len(transmissionRatio)):
        print("Running " + str(inc) + "/" + str(numElements) + ": mass = " + str(mass[massIndex]) + ", transmissionRatio = " + str(transmissionRatio[transmissionRatioIndex]) + "...")

        # standard regen
        print("\tStandard Regen")
        try:
            # Call a function in Dymola and check its return value
            stdResult, stdRegen = dymola.simulateExtendedModel("ElectricVehicle2.Main.stdRegenEV", stopTime = 1200, resultFile = "std", finalNames = ["simplePower.energy.y"], initialNames = ["chassisMass", "transmissionRatio"], initialValues = [mass[massIndex], transmissionRatio[transmissionRatioIndex]])

            if not stdResult:
                print("Simulation failed. Below is the translation log.")
                log = dymola.getLastErrorLog()
                print(log)
            else:
                stdEnergy[transmissionRatioIndex][massIndex] = stdRegen[0] # append the new value to the existing list

        except DymolaException as ex:
            print("Error: " + str(ex))

        # enhanced regen
        print("\tEnhanced Regen")
        try:
            # Call a function in Dymola and check its return value
            enhResult, enhRegen = dymola.simulateExtendedModel("ElectricVehicle2.Main.enhRegenEV", stopTime = 1200, resultFile = "enh", finalNames = ["simplePower.energy.y"], initialNames = ["chassisMass", "transmissionRatio"], initialValues = [mass[massIndex], transmissionRatio[transmissionRatioIndex]])

            if not stdResult:
                print("Simulation failed. Below is the translation log.")
                log = dymola.getLastErrorLog()
                print(log)
            else:
                enhEnergy[transmissionRatioIndex][massIndex] = enhRegen[0] # append the new value to the existing list

        except DymolaException as ex:
            print("Error: " + str(ex))

        inc = inc + 1

if dymola is not None:
    print("\t\tClosing Dymola...")
    dymola.close()
    dymola = None
    assert dymola == None
    time.sleep(5)

energySaved = (stdEnergy - enhEnergy)*25e-7/9

# print(energySaved)

print(transmissionRatioMesh)
print(massMesh)
print(energySaved)

np.save('researchData_energySaved.npy', energySaved)
np.save('researchData_transmissionRatioMesh.npy', transmissionRatioMesh)
np.save('researchData_massMesh.npy', massMesh)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
my_col = cm.jet(energySaved/np.amax(energySaved))
print(my_col)
massMesh = massMesh*0.001
ax.plot_surface(massMesh, transmissionRatioMesh, energySaved, rstride=1, cstride=1, facecolors = my_col, linewidth=0, antialiased=True)

ax.set_xlabel('Chassis Mass ($10^3$ kg)')
ax.set_ylabel('Transmission Ratio (-)')
ax.set_zlabel('Energy Difference (kWh)')
ax.set_title('Energy Difference vs Transmission Ratio and Chassis Mass')

plt.show()
