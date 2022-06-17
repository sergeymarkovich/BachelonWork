import os
import sys
from hxaDefinitions import servoNamesList
from hxaDefinitions import RESOURCE_PATH

InitStateRightLeg  = "-90.0\t600\n0.0\t1500\n90.0\t2400\n"
InitStateLeftLeg = "-90.0\t2400\n0.0\t1500\n90.0\t600\n"

ANGLE_ID = 0
CONTROL_ID = 1

def stringToLut(inputString):
    result = [ ]
    for (k,row) in enumerate(inputString.split('\n')):
        # Working only with none empty lines
        if row.strip():
            values = row.split('\t')
            # If more than two values in row -> bad file
            if len(values) != 2:
                print("stringToLut: Number of values at line differ than two: %s -> %s" % (row,values))
                print("%s" % inputString)
                return None
            # If parsing error -> bad file
            try:
                point = (float(values[0]),float(values[1]))
            except ValueError:
                print("stringToLut: Converting to float error")
                print("%s" % inputString)
                return None
            result.append(point)
    # If result length is zero -> bad file, length of x and y always equal
    if len(result) < 2:
        print("stringToLut: All lines are empty or only one point in LUT")
        print("%s" % inputString)
        return None
    return result

# Check if resulting LUT is monotone acceding.
# If not it can be two values for one coordinate
def isMonotoneLUT(values, key_y):
    if len(values) > 2:
        sign = 1 if values[1][key_y] - values[0][key_y] > 0 else -1
        for (k,v) in enumerate(values[1:]):
            if (v[key_y] - values[k][key_y])*sign < 0:
                print("k = %s, Y Index = %s" % (k,key_y))
                print("(%s - %s)*%s < 0" % (v[key_y],values[k][key_y],sign))
                print("%s" % values)
                return False
    return True

def interp1d(x0,table,key_x,key_y):
    indx = -1

    for (k,row) in enumerate(table):
        if x0 <= row[key_x]:
            indx = k
            break

    if indx == 1:
        indx = len(table)-1

    if indx == 0:
        dy = table[indx+1][key_y] - table[indx][key_y]
        dx = table[indx+1][key_x] - table[indx][key_x]
    else:
        dy = table[indx][key_y] - table[indx-1][key_y]
        dx = table[indx][key_x] - table[indx-1][key_x]

    result = dy/dx*(x0 - table[indx][key_x]) + table[indx][key_y]

    return result

class hxaControlConverter(object):
    def __init__(self, lutDirectory = "servoLUT"):
        # TODO: BUILD NUMPY 1.6.2 AND SCIPY LIBRARIES AND CHANGE THIS CODE!!!

        # Main variable where LUT's for all servo are saved
        # LUT Angle to Control: sort angles in acceding order
        self.lutAngleToControl = { }
        # LUT Control to Angle: sort controls in acceding order
        self.lutControlToAngle = { }

        # Path of LUT's file in disk
        self.lutDirPath = os.path.join(RESOURCE_PATH,lutDirectory)

        # Check if LUT directory exists
        if not os.path.isdir(self.lutDirPath):
            print("LUT directory path not found. Creating ...")
            os.makedirs(self.lutDirPath)

        servoLUT = { }
        # For all known servos creating LUT
        for servo in servoNamesList:
            # Check if file exists
            servoLutPath = os.path.join(self.lutDirPath,servo+".lut")
            if not os.path.isfile(servoLutPath):
                print("LUT file for %s servo not found. Use default values" % servo)
                # Creating new file
                with open(servoLutPath,'w') as servoLutFile:
                    # Choose left or right leg
                    outString = InitStateRightLeg if servo[1] == 'R' and \
                                                     servo[2] != 'C' else InitStateLeftLeg
                    servoLutFile.write(outString)
                servoLUT[servo] = stringToLut(outString)
            else:
                # Reading LUT from disk
                with open(servoLutPath,'r') as servoLutFile:
                    tmp = stringToLut(servoLutFile.read())
                    if tmp is not None:
                        servoLUT[servo] = sorted(tmp, key = lambda x: x[CONTROL_ID])
                        if not isMonotoneLUT(servoLUT[servo],ANGLE_ID):
                            print("Result function not monotone for servo %s. Use default values" % servo)
                            outString = InitStateRightLeg if servo[1] == 'R' and\
                                                             servo[2] != 'C' else InitStateLeftLeg
                            servoLUT[servo] = stringToLut(outString)
                    else:
                        print("LUT file for %s servo can not be read, error "
                              "while parsing. Use default values" % servo)
                        outString = InitStateRightLeg if servo[1] == 'R' and \
                                                         servo[2] != 'C' else InitStateLeftLeg
                        servoLUT[servo] = stringToLut(outString)

        for servo in servoNamesList:
            self.lutAngleToControl[servo] = servoLUT[servo]
            self.lutControlToAngle[servo] = sorted(servoLUT[servo],
                key = lambda x: x[ANGLE_ID])

        print("ControlConverter: Lookup tables loading complete.")

    def toAngle(self,servo,Control):
        return interp1d(Control,self.lutAngleToControl[servo],CONTROL_ID,ANGLE_ID)

    def toControl(self,servo,Angle):
        return interp1d(Angle,self.lutControlToAngle[servo],ANGLE_ID,CONTROL_ID)
