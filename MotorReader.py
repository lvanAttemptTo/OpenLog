import glob
# import re
# import requests
import numpy as np
import xml.etree.ElementTree as ET

class MotorReader:
    class Motor:
        classification = ""
        avgThrust = 0
        propType = ""
        totalImpulse = 0
        diameter = 0
        length = 0
        propWeight = 0
        totalWeight = 0
        manufacturer = ""


        def __init__(self, classification, avgThrust, diameter, length, propWeight, totWeight, Manufacturer):
            self.classification = classification.capitalize()
            self.avgThrust = avgThrust
            self.diameter = diameter
            self.length = length
            self.propWeight = propWeight
            self.totalWeight = totWeight
            self.manufacturer = Manufacturer
            self.thrustCurve = [(0,0)]

        def getTimeArray(self):
            arr = []
            for point in self.thrustCurve:
                arr.append(point[0])

            return(np.array(arr))

        def getThrustArray(self):
            arr = []
            for point in self.thrustCurve:
                arr.append(point[1])

            return(np.array(arr))

        def addThrustCurvePoint(self, time, thrust):
            self.thrustCurve.append((time, thrust))

        def calcTotalImpulse(self):
            if (len(self.thrustCurve) > 0):
                for i in range(len(self.thrustCurve) - 1):
                    self.totalImpulse += ((self.thrustCurve[i][1] + self.thrustCurve[i + 1][1])/2) * (self.thrustCurve[i+1][0] - self.thrustCurve[i][0])


        def getDetails(self):
            text = str(self)
            text += "\nManufacturer: " + self.manufacturer
            text += "\nTotal Impulse: " + str(round(self.totalImpulse)) + " Ns"
            text += "\nDiameter: " + str(self.diameter) + " mm"
            text += "\nLength: " + str(self.length) + " mm"
            text += "\nWeight: " + str(round(self.totalWeight,3)) + " kg"
            text += "\nPropellant Mass: " + str(round(self.propWeight,3)) + " kg"


            return (text)

        def getJSON(self):
            JSON = "{\n"
            JSON += "\"name\": \"" + str(self) + "\",\n"
            JSON += "\"propType\": \"" + self.propType + "\"\n"
            JSON += "}"
            return (JSON)

        def __str__(self):
            return (self.classification + str(self.avgThrust) + self.propType)

        def __eq__(self, other):
            if (not isinstance(other, self.__class__)):
                return (False)

            if (self.classification != other.classification):
                return(False)
            if (self.avgThrust != other.avgThrust):
                return(False)
            if (self.totalImpulse != other.totalImpulse):
                return(False)
            if (self.propType != other.propType):
                return(False)
            if (self.diameter != other.diameter):
                return(False)
            if (self.length != other.length):
                return(False)
            if (self.propWeight != other.propWeight):
                return(False)
            if (self.totalWeight != other.totalWeight):
                return(False)
            if (self.manufacturer != other.manufacturer):
                return(False)
            return(True)

        def __ne__(self, other):
            return(not self.__eq__(other))

    @staticmethod
    def readENG(filename):
        motors = []
        with open(filename, "r") as file:
            line = file.readline()
            while(line != ""):
                # checks for comments and whitespaces
                while (line.startswith(";") or len(line) == 0 or not line[0].isalpha()):
                    line = file.readline().strip()
                # splits up RASP header data
                motorInfo = line.split()

                # Cesaroni check
                if (motorInfo[0][0].isdigit()):
                    # Cesaroni parsing
                    inf = motorInfo[0].split("-")
                    classification = inf[1][0]
                    avgThrust = float(int(inf[1][1:]))
                    propType = inf[2]
                else:
                    # Standard motor code parsing
                    classification = motorInfo[0][0]
                    avgThrust = ""
                    # dealing with non integer thrusts
                    for c in motorInfo[0][1:]:
                        if (c.isdigit() or c == "."):
                            avgThrust += c
                        else:
                            break
                    if ("." in avgThrust):
                        avgThrust = float(avgThrust)
                    else:
                        avgThrust = int(avgThrust)

                    # reads propellant type if it exists
                    propType = ""
                    if (not motorInfo[0][-1].isdigit()):

                        for c in motorInfo[0][1:]:
                            if (propType != "" and c == "-"):
                                break
                            if (not c.isdigit()):
                                propType += c

                diameter = int(float(motorInfo[1]))
                length = float(motorInfo[2])
                propWeight = float(motorInfo[4])
                totWeight = float(motorInfo[5])
                Manufacturer = motorInfo[6]
                motor = MotorReader.Motor(classification, avgThrust, diameter, length, propWeight, totWeight, Manufacturer)

                motor.propType = propType

                # reads thrust curve data
                line = file.readline()
                while (len(line) > 0 and (line.startswith(" ") or line[0].isdigit())):
                    line = line.strip()
                    motor.addThrustCurvePoint(float(line.split()[0]), float(line.split()[1]))

                    line = file.readline()

                motor.calcTotalImpulse()

                motors.append(motor)

        return(motors)



    @staticmethod
    def readMotors(directory):
        files =glob.glob(directory+"*.rse")
        motors = []
        for file in files:
            motors.extend(MotorReader.readRSE(file))

        files = glob.glob(directory+"*.eng")
        for file in files:
            motors.extend(MotorReader.readENG(file))
        return(motors)


    @staticmethod
    def readRSE(file):
        tree = ET.parse(file)
        root = tree.getroot()

        motors = []
        for m in root.iter('engine'):
            # CTI BS Handling
            if (m.get("code")[0].isdigit()):
                inf = m.get("code").split("-")
                classification = inf[1][0]
                avgThrust = int(inf[1][1:])
                propType = inf[2]
            else:
                # standard motor code reading
                classification = m.get("code")[0]
                # dealing with non integer thrusts
                avgThrust = ""
                for c in m.get("code")[1:]:
                    if (c.isdigit() or c == "."):
                        avgThrust += c
                    elif (c == ","):
                        continue
                    else:
                        break
                if ("." in avgThrust):
                    avgThrust = float(avgThrust)
                else:
                    avgThrust = int(avgThrust)

                # reads propellant type if it exists
                propType = ""
                if (not m.get("code")[-1].isdigit()):

                    for c in m.get("code")[1:]:
                        if (c == "-" or c == ","):
                            if (propType != ""):
                                break
                            else:
                                continue
                        if (not c.isdigit()):
                            propType += c
            diameter = int(float(m.get("dia")))
            length = int(float(m.get("len")))
            propWeight = float(m.get("propWt")) / 1000
            totWeight = float(m.get("initWt")) / 1000
            Manufacturer = m.get("mfg")
            totImpulse = float(m.get("Itot"))
            motor = MotorReader.Motor(classification, avgThrust, diameter, length, propWeight, totWeight, Manufacturer)
            motor.totalImpulse = totImpulse
            motor.propType = propType

            # reads thrust curve data
            for point in m.iter('eng-data'):
                motor.addThrustCurvePoint(float(point.get("t")), float(point.get("f")))

            motors.append(motor)

        return(motors)
