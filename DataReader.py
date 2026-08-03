import csv
import numpy as np

class DataReader:
    class Packet:
        containsAccel = False
        def __init__(self, time = 0, alt = 0, velocity = 0, accel = 0):
            self.data = {}
            self.data['time'] = time
            if (alt != ""):
                self.data['alt'] = float(alt)
            else:
                self.data['alt'] = 0
            if (velocity != ""):
                self.data['velocity'] = float(velocity)
            else:
                self.data['velocity'] = 0
            if (accel != ""):
                self.data['accel'] = float(accel)
            else:
                self.data['accel'] = 0

        def getTime(self):
            return(self.data['time'])

        def getAlt(self):
            return(self.data['alt'])

        def getVelo(self):
            return(self.data['velocity'])

        def getAccel(self):
            return(self.data['accel'])

    class FBBPacket(Packet):
        containsAccel = True
        def __init__(self, data):
            super().__init__()
            if (data[0][0] == "#"):
                fs = data[0].split("#")
                self.data['flag'] = fs[1]
                self.data['time'] = int(fs[2]) / 1000
            else:
                self.data['time'] = int(data[0]) / 1000

            if (data[1] != ""):
                self.data['deltaTime'] = int(data[1]) / 1000
            if (data[2] != ""):
                self.data['status'] = int(data[2])
            if (data[3] != ""):
                self.data['baroAlt'] = int(data[3])
            if (data[4] != ""):
                self.data['deadreckSpeed'] = int(data[4])
            if (data[5] != ""):
                self.data['angle'] = float(data[5])
            if (data[6] != ""):
                self.data['rollRate'] = int(data[6])
            if (data[7] != ""):
                self.data['vertAccel'] = float(data[7])
            if (data[8] != ""):
                self.data['accel'] = float(data[8])
            if (data[9] != ""):
                self.data['deadreckAlt'] = int(data[9])
            if (data[10] != ""):
                self.data['baroSpeed'] = float(data[10])
            if (data[11] != ""):
                self.data['temp'] = int(data[11])
            if (data[12] != ""):
                self.data['battVoltage'] = int(data[12]) / 1000
            if (data[13] != ""):
                self.data['channel1State'] = int(data[13])
            if (data[14] != ""):
                self.data['channel2State'] = int(data[14])
            if (data[15] != ""):
                self.data['channel3State'] = int(data[15])
            if (data[16] != ""):
                self.data['analog1'] = int(data[16]) / 1000
            if (data[17] != ""):
                self.data['analog2'] = int(data[17]) / 1000
            if (data[18] != ""):
                self.data['inFreefall'] = (data[18] == "1")
            if (data[19] != ""):
                self.data['latitude'] = float(data[19])
            if (data[20] != ""):
                self.data['Longitude'] = float(data[20])
            if (data[21] != ""):
                self.data['gpsAlt'] = int(data[21])
            if (data[22] != ""):
                self.data['gpsState'] = int(data[22])
            if (data[23] != ""):
                self.data['gpsSats'] = int(data[23])

        def getTime(self):
            return(self.data['time'])

        def getAlt(self):
            return(self.data['baroAlt'])

        def getVelo(self):
            if (self.data['deadreckSpeed'] == 0):
                return(self.data['baroSpeed'])
            return(self.data['deadreckSpeed'])

        def getAccel(self):
            return(self.data['accel'])

    class EggtimerPacket(Packet):
        containsAccel = False
        def __init__(self, data):
            super().__init__()

            self.data['time'] = float(data['T'])

            self.data['alt'] = float(data['Alt']) / 3.2808

            self.data['Falt'] = float(data['FAlt']) / 3.2808

            self.data['velo'] = float(data['FVeloc']) / 3.2808

        def getTime(self):
            return(self.data['time'])

        def getAlt(self):
            return(self.data['alt'])

        def getVelo(self):
            return(self.data['velo'])

        def getAccel(self):
            return(0)

    class Data:

        def __init__(self):
            self.packets = []
            pass

        def addPacket(self, packet):
            self.packets.append(packet)

        def getApogee(self):
            max = 0
            for packet in self.packets:
                if (packet.getAlt() > max):
                    max = packet.getAlt()
            return(max)

        def getMaxVelo(self):
            max = 0
            for packet in self.packets:
                if (packet.getVelo() > max):
                    max = packet.getVelo()
            return (max)

        def getMaxAccel(self):
            if (self.packets[0].containsAccel):
                max = 0
                for packet in self.packets:

                    if (packet.getAccel() > max):
                        max = packet.getAccel()
                    elif (packet.getAccel() < 5): # Check if burn is finished, doesn't work w/ 2-stage. Would like to do state based
                        break
                return (max)
            else:
                return 0
                # too inaccurate
                max = 0
                for i in range(len(self.packets)-1):
                    accel = (self.packets[i+1].getVelo() - self.packets[i].getVelo())/(self.packets[i+1].getTime() - self.packets[i].getTime())
                    accel = accel*0.03108
                    if (accel > max):
                        max = accel

                return (max)


        def getDataArrayOptions(self):
            options = ["Altitude", "Velocity"]
            if (self.packets[0].containsAccel):
                options.append("Acceleration")

            return(options)

        def getArray(self, str):
            if (str == "Altitude"):
                return(self.getAltArray())
            if (str == "Velocity"):
                return(self.getVeloArray())
            if (str == "Acceleration"):
                return(self.getAccelArray())

        def getTimeArray(self):
            arr = []
            for packet in self.packets:
                arr.append(float(packet.getTime()))

            return(np.array(arr))

        def getAltArray(self):
            arr = []
            for packet in self.packets:
                arr.append(float(packet.getAlt()))

            return(np.array(arr))

        def getVeloArray(self):
            arr = []
            for packet in self.packets:
                arr.append(float(packet.getVelo()))

            return(np.array(arr))

        def getAccelArray(self):
            arr = []
            for packet in self.packets:
                arr.append(float(packet.getAccel()))

            return(np.array(arr))




    @staticmethod
    def readFile(filename):
        if (filename.endswith(".csv")):
            with open(filename, "r") as CSVFile:
                file = csv.DictReader(CSVFile)
                if ("T" in file.fieldnames):
                    return(DataReader.readEggTimer(filename))
                elif ("Time" in file.fieldnames):
                    return(DataReader.readGeneral(filename))
        if (filename.endswith(".fbb")):
            return(DataReader.readFBB(filename))
        if (filename.endswith(".olfd")):
            return(DataReader.readGeneral(filename))
        return(False)


    @staticmethod
    def readFBB(filename):
        fbbData = DataReader.Data()
        with open(filename, "r") as FBBFile:
            text = FBBFile.read()
            lines = text.split("!")
            for line in lines:
                data = line.split(":")
                if (len(data) == 25):
                    packet = DataReader.FBBPacket(data)
                    fbbData.addPacket(packet)
        return(fbbData)


    @staticmethod
    def readEggTimer(filename):
        data = DataReader.Data()
        with open(filename, "r") as EggTimerFile:
            file = csv.DictReader(EggTimerFile)

            for row in file:
                data.addPacket(DataReader.EggtimerPacket(row))
        return(data)

    @staticmethod
    def readGeneral(filename):
        data = DataReader.Data()
        with open(filename, "r") as GeneralFile:
            file = csv.DictReader(GeneralFile)
            for row in file:
                data.addPacket(DataReader.Packet(time=row["Time"], alt=row["Altitude"], velocity=row["Velocity"], accel=row["Acceleration"]))

        return(data)
