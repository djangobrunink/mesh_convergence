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


def getMaxMises(odbName, elsetName):
    """ Print max mises location and value given odbName
        and elset(optional)
    """
    returnValue = None
    elset = elemset = None
    region = "over the entire model"
    """ Open the output database """
    odb = openOdb(odbName)
    assembly = odb.rootAssembly

    """ Check to see if the element set exists
        in the assembly
    """
    if elsetName:
        try:
            elemset = assembly.elementSets[elsetName]
            region = " in the element set : " + elsetName
        except KeyError:
            print('An assembly level elset named %s does'
                  'not exist in the output database %s'
                  % (elsetName, odb))
            odb.close()

    """ Initialize maximum values """
    totals33 = -0.1
    maxE33 = -0.1
    maxElemMises = 0
    maxStepMises = "_None_"
    maxFrameMises = -1
    Stress = 'S'

    isStressPresent = False
    for step in odb.steps.values():
        frame = step.frames[-1]
        allFields = frame.fieldOutputs
        if Stress in allFields:
            isStressPresent = True
            stressSet = allFields[Stress]
            if elemset:
                stressSet = stressSet.getSubset(region=elemset)
            for stressValue in stressSet.values:
                totals33 += stressValue.data[2]

                if stressValue.mises > totals33:
                    maxE33 = stressValue.data[2]
                    maxElemMises = stressValue.elementLabel
                    maxStepMises = step.name
                    maxFrameMises = frame.incrementNumber
    # if isForcePresent:
    #    print('Maximum Displacement %s is %f in element %d' % (region, maxForce, maxElemForce))
    #    print('Location: frame # %d  step:  %s ' % (maxFrameForce, maxStepForce))
    #    returnValue = maxForce

    if isStressPresent:
        print('Total stress 33 direction is %s' % totals33)
        print('Maximum e33 stress %s is %f in element %d' % (region, maxE33, maxElemMises))
        print('Location: frame # %d  step:  %s ' % (maxFrameMises, maxStepMises))
        returnValue = (maxE33, totals33)
    else:
        print('Stress output is not available in'
              'the output database : %s\n' % odb.name)
        returnValue = (None, None)

    """ Close the output database before exiting the program """
    odb.close()
    return returnValue


# filename = "Job-Linear_Elastic"
filename = "Job-Hyperelastic"
# filename = "Job-Viscoelastic"

# Start of program
path = r"C:\Users\Django\Documents\TU Delft\Master\Year 1\Q3\Computational Mechanics of Tissues and Cells - BM41090\Assignment\Workshop Assignment 2\New Geom"
path += "\\" + filename + ".odb"

meshRange = np.zeros(100)
for i in range(len(meshRange)):
    meshRange[i] = exp(-i / 12 + 250 / 60) + 3  # this custom formula checks 100 appropriate sizes of the model.

meshNumber = np.zeros(len(meshRange))
maxE33 = np.zeros(len(meshRange))
totalE33 = np.zeros(len(meshRange))
previous_part = 0
for i, size in enumerate(meshRange):
    """Generate Mesh"""
    myOdb = session.openOdb(path)

    part = mdb.models['Model-1'].parts['disc']
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

    maxE33[i], totalE33[i] = getMaxMises(filename + ".odb", "SURFACE")
    previous_part = len(part.elements)

"""Remove zeros"""
maxE33 = maxE33[maxE33 != 0]
totalE33 = totalE33[totalE33 != 0]
meshNumber = meshNumber[meshNumber != 0]

"""Print"""
myOdb = session.openOdb(path)
data1 = []
for i, (number, maxE33_) in enumerate(zip(meshNumber, maxE33)):
    data1.append((number, maxE33_))

session.XYData(name="Mesh Convergence (Max)", data=data1)
print("Done!")
myOdb.close()
