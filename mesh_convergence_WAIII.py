# -*- coding: mbcs -*-
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from abaqusConstants import *
from odbAccess import *
from sys import argv, exit
import numpy as np

def getMaxForce(odbName, ndsetName):
    """ Print max force location and value given odbName
        and ndset(optional)
    """
    returnValue = None
    ndset = nodeset = None
    region = "over the entire model"
    """ Open the output database """
    odb = openOdb(odbName)
    assembly = odb.rootAssembly

    """ Check to see if the element set exists
        in the assembly
    """
    if ndsetName:
        try:
            nodeset = assembly.nodeSets[ndsetName]
            region = " in the node set : " + ndsetName
        except KeyError:
            print('An assembly level ndset named %s does'
                  'not exist in the output database %s'
                  % (ndsetName, odb))
            odb.close()
            raise KeyError

    """ Initialize maximum values """
    totalForce = -0.1
    maxForce = -0.000001
    maxElemForce = 0
    maxStepForce = "_None_"
    maxFrameForce = -1
    Force = 'RF'

    isForcePresent = False
    for step in odb.steps.values():
        frame = step.frames[-1]
        allFields = frame.fieldOutputs
        if Force in allFields:
            isForcePresent = True
            forceSet = allFields[Force]
            if nodeset:
                forceSet = forceSet.getSubset(region=nodeset)
            for forceValue in forceSet.values:
                totalForce += forceValue.data[1]
                if forceValue.data[1] > maxForce:
                    maxForce = forceValue.data[1]
                    maxElemForce = forceValue.nodeLabel
                    maxStepForce = step.name
                    maxFrameForce = frame.incrementNumber
    # if isForcePresent:
    #    print('Maximum Displacement %s is %f in element %d' % (region, maxForce, maxElemForce))
    #    print('Location: frame # %d  step:  %s ' % (maxFrameForce, maxStepForce))
    #    returnValue = maxForce

    if isForcePresent:
        print('Total RF2 direction is %s' % totalForce)
        print('Maximum RF2 %s is %f in element %d' % (region, maxForce, maxElemForce))
        print('Location: frame # %d  step:  %s ' % (maxFrameForce, maxStepForce))
        returnValue = (maxForce, totalForce)
    else:
        print('Stress output is not available in'
              'the output database : %s\n' % odb.name)
        returnValue = (None, None)

    """ Close the output database before exiting the program """
    odb.close()
    return returnValue



# filename = "Job-Linear_Elastic"
# filename = "Job-Hyperelastic"
# filename = "Job-Viscoelastic"
filename = "Job-RBC-Convergence"
FORCE = True


# Start of program
path = r"C:\Users\Django\Documents\TU Delft\Master\Year 1\Q3\Computational Mechanics of Tissues and Cells - BM41090\Assignment\Workshop Assignment 3"
path += "\\" + filename + ".odb"

meshRange = np.zeros(101)

for i in range(len(meshRange)):
    meshRange[i] = -0.0000225 * i + 0.0024  # this custom formula checks 100 appropriate sizes of the model.
meshRange[-1] = 0.000245

meshNumber = np.zeros(len(meshRange))
maxE33 = np.zeros(len(meshRange))
totalE33 = np.zeros(len(meshRange))
maxForce = np.zeros(len(meshRange))
totalForce = np.zeros(len(meshRange))
previous_part = 0
for i, size in enumerate(meshRange):
    """Generate Mesh"""
    myOdb = session.openOdb(path)

    part = mdb.models['Model-1'].parts['RBC-Healthy']
    part.seedPart(size)
    part.generateMesh()
    myOdb.close()

    """Analyze Mesh"""
    if len(part.elements) <= previous_part:
        continue
    if len(part.nodes) > 1000:
        continue
    else:
        print("Starting analysis with %s elements and %s nodes." % (len(part.elements), len(part.nodes)))

    mdb.jobs[filename].submit()
    mdb.jobs[filename].waitForCompletion()
    meshNumber[i] = len(part.nodes)
    session.viewports['Viewport: 1'].forceRefresh()

    if FORCE:
        maxForce[i], totalForce[i] = getMaxForce(filename + ".odb", " ALL NODES")

    previous_part = len(part.elements)

"""Remove zeros"""
maxE33 = maxE33[maxE33 != 0]
totalE33 = totalE33[totalE33 != 0]
maxForce = maxForce[maxForce != 0]
totalForce = totalForce[totalForce != 0]
meshNumber = meshNumber[meshNumber != 0]

"""Print"""
myOdb = session.openOdb(path)
data1 = []

if FORCE:
    for i, (number, maxForce_) in enumerate(zip(meshNumber, maxForce)):
        data1.append((number, maxForce_))

else:
    for i, (number, maxE33_) in enumerate(zip(meshNumber, maxE33)):
        data1.append((number, maxE33_))

session.XYData(name="Mesh Convergence (Force)", data=data1)
print("Done!")
myOdb.close()