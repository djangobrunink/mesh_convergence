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
    maxMises = -0.1
    maxElemMises = 0
    maxStepMises = "_None_"
    maxFrameMises = -1
    Stress = 'S'

    maxDisp = -0.1
    maxElemDisp = 0
    maxStepDisp = "_None_"
    maxFrameDisp = -1
    Disp = 'E'

    isStressPresent = False
    isDispPresent = False
    for step in odb.steps.values():
        frame = step.frames[-1]
        allFields = frame.fieldOutputs
        disp = frame.fieldOutputs['U'].getSubset(region=elemset).values
        print(disp)
        print(allFields)
        if Disp in allFields:
            isDispPresent = True
            dispSet = allFields[Disp]
            if elemset:
                dispSet = dispSet.getSubset(region=elemset)
                print(dispSet)
                print(dispSet.values)
            for dispValue in dispSet.values:
                print("test")
                print(dispValue)
                if dispValue.maxPrincipal > maxDisp:
                    maxDisp = dispValue.maxPrincipal
                    maxElemDisp = dispValue.elementLabel
                    maxStepDisp = step.name
                    maxFrameDisp = frame.incrementNumber

        if Stress in allFields:
            isStressPresent = True
            stressSet = allFields[Stress]
            if elemset:
                stressSet = stressSet.getSubset(region=elemset)
                print(stressSet)
            for stressValue in stressSet.values:
                if stressValue.mises > maxMises:
                    maxMises = stressValue.mises
                    maxElemMises = stressValue.elementLabel
                    maxStepMises = step.name
                    maxFrameMises = frame.incrementNumber
    if isDispPresent:
        print('Maximum Displacement %s is %f in element %d' % (region, maxDisp, maxElemDisp))
        print('Location: frame # %d  step:  %s ' % (maxFrameDisp, maxStepDisp))
        returnValue = maxDisp
    else:
        print('Displacement output is not available in'
              'the output database : %s\n' % odb.name)
        returnValue = None

    if isStressPresent:
        print('Maximum von Mises stress %s is %f in element %d' % (region, maxMises, maxElemMises))
        print('Location: frame # %d  step:  %s ' % (maxFrameMises, maxStepMises))
        returnValue = (returnValue, maxMises)
    else:
        print('Stress output is not available in'
              'the output database : %s\n' % odb.name)
        returnValue = (returnValue, None)

    """ Close the output database before exiting the program """
    odb.close()
    return returnValue

# , 9, 11, 13, 15, 17, 19, 21, 23, 25)
for i in range(100):
    meshRange[i] = exp(-i / 12 + 250 / 60) + 7

meshNumber = np.zeros(len(meshRange))
maxMises = np.zeros(len(meshRange))
maxDisp = np.zeros(len(meshRange))
path = r"C:\Users\Django\Documents\TU Delft\Master\Year 1\Q3\Computational Mechanics of Tissues and Cells - BM41090\Assignment\Workshop Assignment 2\Job-2.odb"
previous_part = 0
for i, size in enumerate(meshRange):
    """Generate Mesh"""
    myOdb = session.openOdb(path)
    # session.viewports['Viewport: 1'].setValues(displayedObject=myOdb)

    part = mdb.models['Model-1'].parts['Part-1']
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

    mdb.jobs['Job-2'].submit()
    mdb.jobs['Job-2'].waitForCompletion()
    meshNumber[i] = len(part.nodes)
    session.viewports['Viewport: 1'].forceRefresh()

    maxMises[i], maxDisp[i] = getMaxMises("Job-2.odb", " ALL ELEMENTS")
    previous_part = len(part.elements)

"""Remove zeros"""
maxMises = maxMises[maxMises != 0]
maxDisp = maxDisp[maxDisp != 0]
meshNumber = meshNumber[meshNumber != 0]

"""Print"""
myOdb = session.openOdb(path)
data = []
for i, (number, mises) in enumerate(zip(meshNumber, maxMises)):
    data.append((number, mises))

session.XYData(name="Mesh Convergence", data=data)
print("Done!")
myOdb.close()
