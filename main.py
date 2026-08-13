version = "0.26"

"""
Special Note:
    Make sure to update version
    
    Make sure to update documentation

Things that need to get finished:

    Figure out how to make the check for updates work. Will need to create a website/server for it to request.

    finish implementing importing csv files

Refactoring:

Feature list:

    Add manufacturer, classification, diameter, ect filters to motors tab.
    Maybe through a filter object that stores filter inputs and opens a popup. (can do same thing for log filters)

    add time


Major features !!!:

    add clusters/staging/multi motor

    add multi electronics

    add launch sites

    make it interact with thrustcurve.org for saving rockets

    Read/Import open rocket and rocksim files

    Add opening in new windows (Probably means creating an object for the whole tkinter code and cloning)


Graphics:

    Add dynamic width adjustment based on window width

    Improve Frame formatting and use more labelFrames

    Find better theme pack / tkinter extension


Bug list:

    Changing units while in edit window causes a reference error for finding the item. Due to the __str__() representation changing.
    
    Figure out how to remove flight data files again and have undo/redo work. 
        My best idea is to have it store all the files that need to be removed in a list in the URHandler and then delete those when the program is closed.

"""
# libraries
import datetime
import json
import shutil
import tkinter.filedialog
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Notebook, Combobox
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkcalendar import Calendar
from enum import Enum
import sv_ttk
import os
from matplotlib.figure import Figure
import matplotlib.backends.backend_tkagg as tkagg
from PIL import Image, ImageTk
# other files
from DataReader import DataReader
from MotorReader import MotorReader
import emailer

class DeployMode(Enum):
    MOTOR = 1
    SINGLE = 2
    DUAL = 3

class CheckList(Frame):
    def __init__(self, master, command=None):
        Frame.__init__(self, master)
        self.boxes = []
        self.states = []
        self.command = command

    def addBox(self, name):
        var = IntVar()
        self.boxes.append(Checkbutton(self, text=name, selectcolor="black", variable=var))
        if (self.command != None):
            self.boxes[-1]["command"] = self.command
        self.states.append(var)

    def addBoxes(self, names):
        for name in names:
            self.addBox(name)

    def pack(self, expand=TRUE, fill=BOTH, side=TOP):
        for i in range(len(self.boxes)):
            self.boxes[i].grid(row = i, column = 1)

        Frame.pack(self, expand=expand, fill=fill, side=side)

    def getChecked(self):
        checked = []
        for i in range(len(self.boxes)):
            if (self.states[i].get() == 1):
                checked.append(self.boxes[i]["text"])

        return(checked)

class Popup(Toplevel):
    def __init__(self, master, title = "Popup", disableEscape = False):
        Toplevel.__init__(self, master)
        self.iconbitmap("data/icon.ico")
        self.title(title)
        if (not disableEscape):
            self.bind("<Escape>", lambda event: self.destroy())

class InputFrame(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        popup = master
        while (not (isinstance(popup, Popup) or isinstance(popup, Toplevel))):
            popup = popup.master
        popup.bind("<Down>", self.moveDown)
        popup.bind("<Right>", self.moveDown)
        popup.bind("<Up>", self.moveUp)
        popup.bind("<Left>", self.moveUp)
        self.inputs = []
        self.labels = []

    def addInput(self, entry, label, swap=False):
        self.inputs.append(entry)
        if (isinstance(label, str)):
            self.labels.append(Label(self, text=label))
        elif (isinstance(label, Label)):
            self.labels.append(label)

        self.swap = swap

    def pack(self, expand=TRUE, fill=BOTH, side=TOP):
        for i in range(len(self.inputs)):
            if (not self.swap):
                self.labels[i].grid(row=i, column=0)
                self.inputs[i].grid(row=i, column=1)
            else:
                self.labels[i].grid(row=i, column=1)
                self.inputs[i].grid(row=i, column=0)

        Frame.pack(self, expand = expand, fill = fill, side=side)

    def moveUp(self, event):
        entry = self.focus_get()

        pointer = -1
        for i in range(len(self.inputs)):
            if (self.inputs[i] == entry):
                pointer = i
                break
        if (pointer == -1):
            self.inputs[-1].focus_set()
            return

        if (pointer > 0):
            pointer -= 1

        self.inputs[pointer].focus_set()
        if (isinstance(self.inputs[pointer], Calendar)):
            self.moveUp("")

    def moveDown(self, event):
        entry = self.focus_get()

        pointer = -1
        for i in range(len(self.inputs)):
            if (self.inputs[i] == entry):
                pointer = i
                break
        if (pointer == -1):
            self.inputs[0].focus_set()
            return

        if (pointer < len(self.inputs) - 1):
            pointer += 1

        self.inputs[pointer].focus_set()
        if (isinstance(self.inputs[pointer], Calendar)):
            self.moveDown("")

    def clear(self):
        for entry in self.inputs:
            if (isinstance(entry, Entry)):
                entry.delete(0, END)
            elif (isinstance(entry, Combobox)):
                entry.set("")

class Rocket:
    name = ""
    diameter = None
    length = None
    MMT = 0
    picture = ""

    def __init__(self, name, diameter, length, MMT):
        self.name = name
        self.diameter = diameter
        self.length = length
        self.MMT = MMT

    def setPicture(self, filename):
        if (filename == ""):
            return

        suffix = filename.split(".")[-1]
        if (self.picture == "" or not self.picture.endswith(suffix)):
            index = 0

            newName = "data/rocketPictures/" + str(index) + "." + suffix
            while (os.path.exists(newName)):
                index += 1
                newName = "data/rocketPictures/" + str(index) + "." + suffix

            self.picture = newName

        shutil.copy(filename, self.picture)

    def getDetails(self):
        text = self.name
        text += "\nDiameter: " + str(self.diameter) + '"'
        text += "\nLength: " + str(self.length) + '"'
        text += "\nMMT: " + str(self.MMT) + " mm"
        return(text)

    def getJSON(self):
        JSON ="{\n"
        JSON += "\"name\": \"" + str(self.name) + "\",\n"
        JSON += "\"diameter\": " + str(self.diameter.value) + ",\n"
        JSON += "\"length\": " + str(self.length.value) + ",\n"
        JSON += "\"MMT\": " + str(self.MMT) + ",\n"
        JSON += "\"Picture\": \"" + str(self.picture) + "\"\n"
        JSON += "}"
        return(JSON)

    def __str__(self):
        return(self.name)

    def __repr__(self):
        return(self.name)

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return(False)

        if (self.name != other.name):
            return(False)
        if (self.diameter != other.diameter):
            return(False)
        if (self.length != other.length):
            return(False)
        if (self.MMT != other.MMT):
            return(False)
        return(True)

    def __ne__(self, other):
        return(not self.__eq__(other))

class Electronic:
    name = ""
    manufacturer = ""
    altSpecific = False
    veloSpecific = False
    accelSpecific = False
    def __init__(self, name, manufacturer, altSpecific, veloSpecific, accelSpecific):
        self.name = name
        self.manufacturer = manufacturer
        self.altSpecific = altSpecific
        self.veloSpecific = veloSpecific
        self.accelSpecific = accelSpecific

    def getDetails(self):
        text = self.name
        text += "\nManufacturer: " + str(self.manufacturer)
        text += "\nAltitude Specific: "
        if (self.altSpecific):
            text += "Yes"
        else:
            text += "No"
        text += "\nVelocity Specific: "
        if (self.veloSpecific):
            text += "Yes"
        else:
            text += "No"
        text += "\nAcceleration Specific: "
        if (self.accelSpecific):
            text += "Yes"
        else:
            text += "No"
        return(text)

    def getJSON(self):
        JSON ="{\n"
        JSON += "\"name\": \"" + self.name + "\",\n"
        JSON += "\"manufacturer\": \"" + str(self.manufacturer) + "\",\n"
        JSON += "\"altSpecific\": " + str(self.altSpecific).lower() + ",\n"
        JSON += "\"veloSpecific\": " + str(self.veloSpecific).lower() + ",\n"
        JSON += "\"accelSpecific\": " + str(self.accelSpecific).lower() + "\n"
        JSON += "}"
        return(JSON)

    def __str__(self):
        return(self.manufacturer + " " + self.name)

    def __repr__(self):
        return(str(self))

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return(False)
        if (self.name != other.name):
            return(False)
        if (self.manufacturer != other.manufacturer):
            return(False)
        if (self.altSpecific != other.altSpecific):
            return(False)
        if (self.veloSpecific != other.veloSpecific):
            return(False)
        if (self.accelSpecific != other.accelSpecific):
            return(False)
        return(True)

    def __ne__(self, other):
        return(not self.__eq__(other))

class Flight:
    motor = None
    rocket = None
    electronics = None
    deployMode = None
    date = datetime.datetime.now()
    alt = None
    velo = None
    accel = None
    success = False
    FDFilename = ""
    # ONLY USED FOR FILTER
    classification = None
    notes = ""
    def __init__(self, motor, rocket, electronics, deployMode, date, FDFilename, alt, velo, accel, success, notes):
        if (motor != None):
            self.motor = motor
            self.classification = motor.classification
        if (rocket != None):
            self.rocket = rocket
        if (electronics != None):
            self.electronics = electronics
        if (deployMode != None):
            self.deployMode = deployMode
        if (date != None):
            self.date = date
        if (FDFilename != None):
            self.FDFilename = FDFilename
        if (alt != None):
            self.alt = alt
        if (velo != None):
            self.velo = velo
        if (accel != None):
            self.accel = accel
        if (success != None):
            self.success = success
        if (notes != None):
            self.notes = notes

    def getDetails(self):
        text = "Rocket: " + self.rocket.name
        text += "\nDate: " + self.date.strftime("%m/%d/%Y")
        text += "\nMotor: " + str(self.motor)
        text += "\nElectronics: " + str(self.electronics)
        text += "\nDeployMode: "
        if (self.deployMode == DeployMode.MOTOR):
            text += "Motor Deploy"
        elif (self.deployMode == DeployMode.SINGLE):
            text += "Single Deploy"
        else:
            text += "Dual Deploy"
        text += "\nAltitude: "
        if (not self.electronics.altSpecific):
            text += "~"
        text += str(self.alt)
        text += "\nVelocity: "
        if(not self.electronics.veloSpecific):
            text += "~"
        text += str(self.velo)
        text += "\nAcceleration: "
        if (not self.electronics.accelSpecific):
            text += "~"
        text += str(self.accel)
        text += "\nSuccess: " + str(self.success)
        text += "\nNotes: " + self.notes
        return(text)

    def getJSON(self):
        JSON ="{\n"
        JSON += "\"motor\": \"" + str(self.motor) + "\",\n"
        JSON += "\"rocket\": \"" + str(self.rocket) + "\",\n"
        JSON += "\"electronics\": \"" + str(self.electronics) + "\",\n"
        JSON += "\"deployMode\": \"" + self.deployMode.name + "\",\n"
        JSON += "\"date\": \"" + str(self.date.strftime("%m/%d/%Y")) + "\",\n"
        JSON += "\"FDFilename\": \"" + self.FDFilename + "\",\n"
        JSON += "\"alt\": " + str(self.alt.value) + ",\n"
        JSON += "\"velo\": " + str(self.velo.value) + ",\n"
        JSON += "\"accel\": " + str(self.accel.value) + ",\n"
        JSON += "\"success\": " + str(self.success).lower() + ",\n"
        JSON += "\"notes\": \"" + str(self.notes).replace("\n", "\\n") + "\"\n"
        JSON += "}"
        return(JSON)

    def getCSV(self):
        csv = self.date.strftime("%m/%d/%y") + ","
        csv += self.rocket.name + ","
        csv += str(self.rocket.diameter.getValue()) + ","
        csv += str(self.motor) + ","
        csv += str(self.motor.totalImpulse) + ","
        csv += str(self.electronics) + ","
        csv += self.deployMode.name + ","
        csv += str(self.alt.getValue()) + ","
        csv += str(self.velo.getValue()) + ","
        csv += str(self.accel.getValue()) + ","
        if (self.success):
            csv += "Y,"
        else:
            csv += "N,"
        csv += "\"" + self.notes + "\"\n"
        return(csv)

    def contains(self, delim):
        if (str(self.motor) == delim or str(self.rocket) == delim or str(self.electronics) == delim):
            return True
        else:
            return False

    def openInWindow(self):
        popup = Popup(window, title="Flight Details")

        details = Text(popup)
        details.pack()
        details.insert(END, self.getDetails())
        details["state"] = DISABLED

    def __str__(self):
        return(str(self.rocket) + " " + self.date.strftime("%m/%d/%Y") + " " + str(self.motor) + " " + str(self.alt))

    def __repr__(self):
        return(str(self))

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return(False)

        if (self.motor != other.motor):
            return(False)
        if (self.rocket != other.rocket):
            return(False)
        if (self.electronics != other.electronics):
            return(False)
        if (self.deployMode != other.deployMode):
            return(False)
        if (self.date != other.date):
            return(False)
        if (self.alt != other.alt):
            return(False)
        if (self.velo != other.velo):
            return(False)
        if (self.accel != other.accel):
            return(False)
        if (self.success != other.success):
            return(False)
        if (self.FDFilename != other.FDFilename):
            return(False)
        if (self.classification != other.classification):
            return(False)
        if (self.notes != other.notes):
            return(False)
        return(True)

    def __ne__(self, other):
        return(not self.__eq__(other))

class Log:
    rockets = []
    electronics = [Electronic("None", "", False, False, False)]
    motors =[]
    flights = []
    tkinterRefresh = False



    '''
    Constructor, establishes log popup window objects
    '''
    def __init__(self, preferences):
        self.preferences = preferences
        self.copiedObj = None
        self.URHandler = Log.UndoRedoHandler(self)
        self.logManagementWindow = Log.LogManagementWindow(self)
        self.rocketManagementWindow = Log.RocketManagementWindow(self)
        self.electronicManagamentWindow = Log.ElectronicManagementWindow(self)
        self.exporter = Log.Exporter(self)

    def __copy__(self):
        newLog = Log(self.preferences)
        newLog.rockets = self.rockets.copy()
        newLog.electronics = self.electronics.copy()
        newLog.motors = self.motors.copy()
        newLog.flights = self.flights.copy()

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return(False)

        # if (self.preferences != other.preferences):
        #     return(False)

        if (len(self.rockets) != len(other.rockets)):
            return(False)
        for i in range(len(self.rockets)):
            if (self.rockets[i] != other.rockets[i]):
                return(False)

        if (len(self.electronics) != len(other.electronics)):
            return(False)
        for i in range(len(self.electronics)):
            if (self.electronics[i] != other.electronics[i]):
                return(False)

        if (len(self.motors) != len(other.motors)):
            return(False)

        if (len(self.flights) != len(other.flights)):
            return(False)
        for i in range(len(self.flights)):
            if (self.flights[i] != other.flights[i]):
                return(False)

        return(True)

    def __ne__(self, other):
        return(not self.__eq__(other))

    def clone(self):
        newLog = Log(self.preferences)
        newLog.rockets = list(self.rockets)
        newLog.electronics = list(self.electronics)
        newLog.motors = self.motors
        newLog.flights = list(self.flights)
        return(newLog)

    class UndoRedoHandler:

        def __init__(self, log):
            self.log = log
            self.editChain = []
            self.pointer = -1
            self.addState()

        def addState(self):
            if (len(self.editChain) == 0):
                self.pointer = 0
                self.editChain.append(self.log.getJSON())
                return
            # if (self.editChain[self.pointer] != self.log):
            self.pointer += 1
            self.editChain = (self.editChain[:self.pointer])
            self.editChain.append(self.log.getJSON())

        def reset(self):
            self.editChain = []
            self.pointer = -1

        def undo(self):
            if (self.pointer <= 0):
                return

            self.pointer -= 1
            self.log.parseJSON(self.editChain[self.pointer])
            if (self.log.preferences.logFile != ""):
                with open(self.log.preferences.logFile, "w") as JSONFile:
                    JSONFile.write(self.log.getJSON())
                self.log.refreshAll()

        def redo(self):
            if (self.pointer < len(self.editChain) - 1 and self.pointer >= 0):
                self.pointer += 1
                self.log.parseJSON(self.editChain[self.pointer])
                if (self.log.preferences.logFile != ""):
                    with open(self.log.preferences.logFile, "w") as JSONFile:
                        JSONFile.write(self.log.getJSON())
                    self.log.refreshAll()

        '''
        Tkinter event handling
        '''

        def handleUndo(self, event):
            self.undo()

        def handleRedo(self, event):
            self.redo()

        def getJSON(self):
            # return(json.dumps({"States": self.editChain}, indent=4))
            JSON = "{\n"
            JSON += "\"Pointer\": " + str(self.pointer) + ",\n"
            JSON += "\"States\": [\n"
            for state in self.editChain[:-1]:
                JSON += state + ",\n"
            JSON += self.editChain[-1] + "\n"
            JSON += "]\n"
            JSON += "}"
            return(JSON)

    '''
    Clears out log data (backend use only)
    '''
    def clear(self):
        self.rockets = []
        self.electronics = [Electronic("None", "", False, False, False)]
        self.motors = []
        self.flights = []
        self.tkinterRefresh = True

    '''
    Get stats based on if the flight contains something matching the name of the delim, if it is "All" it is ignored.
    '''
    def getStats(self, delim):
        confirmedOnly = statsConfidence.get() == "Yes"
        successesOnly = statsSuccessOnly.get() == "Yes"

        maxAlt = Number(0, Number.Type.ALT, self.preferences)
        maxVelo = Number(0, Number.Type.VELO, self.preferences)
        maxAccel = Number(0, Number.Type.ACCEL, self.preferences)
        totalAlt = Number(0, Number.Type.ALT, self.preferences)
        totalImpulse = 0
        totalPropBurned = Number(0, Number.Type.MOTORMASS, self.preferences)
        successes = 0
        totalFlights = 0

        for flight in self.flights:
            if (delim != "All" and not flight.contains(delim)):
                continue
            if (successesOnly and not flight.success):
                totalFlights += 1
                continue

            if (flight.alt * int(not confirmedOnly or flight.electronics.altSpecific) > maxAlt):
                maxAlt = flight.alt
            if (flight.velo * int(not confirmedOnly or flight.electronics.veloSpecific) > maxVelo):
                maxVelo = flight.velo
            if (flight.accel * int(not confirmedOnly or flight.electronics.accelSpecific) > maxAccel):
                maxAccel = flight.accel

            totalAlt += flight.alt * int(not confirmedOnly or flight.electronics.altSpecific)
            totalImpulse += flight.motor.totalImpulse
            totalPropBurned += flight.motor.propWeight
            successes += int(flight.success)
            totalFlights += 1

        text = "Total Flights: " + str(totalFlights)
        text += "\nMax Altitude: " + str(maxAlt)
        text += "\nMax Velocity: " + str(maxVelo)
        text += "\nMax Acceleration: " + str(maxAccel)
        text += "\nTotal Altitude: " + str(totalAlt)
        text += "\nTotal Impulse: " + str(round(totalImpulse)) + " Ns"
        text += "\nTotal Propellant Burned: " + str(totalPropBurned)
        if (totalFlights > 0):
            text += "\nSuccess Rate: %" + str(round((successes / totalFlights) * 100))
        else:
            text += "\nSuccess Rate: NA"

        return (text)


    def getFlights(self):
        matchingFlights = []
        if (tabControl.index("current") == 1):
            # rocket
            if (len(rocketList.curselection()) == 0):
                messagebox.showerror("Error", "Please select a rocket.")
                return
            selectedRocket = self.getRocket(rocketList.selection_get())
            if (selectedRocket == None):
                messagebox.showerror("Error", "Please select a rocket.")
                return

            for flight in self.flights:
                if (flight.rocket == selectedRocket):
                    matchingFlights.append(flight)


        elif (tabControl.index("current") == 2):
            # electronics
            if (len(electronicsList.curselection()) == 0):
                messagebox.showerror("Error", "Please select an electronic.")
                return
            selectedElectronic = self.getElectronic(electronicsList.selection_get())
            if (selectedElectronic == None):
                messagebox.showerror("Error", "Please select an electronic.")
                return

            for flight in self.flights:
                if (flight.electronics == selectedElectronic):
                    matchingFlights.append(flight)
        elif (tabControl.index("current") == 3):
            if (len(motorList.curselection()) == 0):
                messagebox.showerror("Error", "Please select an motor.")
                return
            selectedMotor = self.getMotor(motorList.selection_get())
            if (selectedMotor == None):
                messagebox.showerror("Error", "Please select an motor.")
                return

            for flight in self.flights:
                if (flight.motor == selectedMotor):
                    matchingFlights.append(flight)
        else:
            return

        popup = Popup(window, title="Flight List")

        matchingFlightListBox = Listbox(popup)
        matchingFlightListBox.pack(expand=True, fill="both")
        matchingFlightListBox.bind("<Double-Button-1>", self.handleVFDoubleClick)
        for flight in matchingFlights:
            matchingFlightListBox.insert(END, flight)

    def handleVFDoubleClick(self, event):
        if (len(event.widget.curselection()) == 0):
            return
        flight = self.getFlight(event.widget.selection_get())
        flight.openInWindow()
    '''
    Backend add functions that handle updates to Tkinter
    '''

    def addRocket(self, rocket):
        if (self.getRocket(str(rocket)) != None):
            return(False)
        self.rockets.append(rocket)
        self.updateRocketList()
        self.saveJSON()
        self.tkinterRefresh = True
        return(True)

    def addElectronic(self, electronic):
        if (self.getElectronic(str(electronic)) != None):
            return(False)
        self.electronics.append(electronic)
        self.updateElectronicsList()
        self.saveJSON()
        self.tkinterRefresh = True
        return(True)

    def addFlight(self, flight):
        self.flights.append(flight)
        self.updateLogList()
        self.saveJSON()
        self.updateStats()
        self.tkinterRefresh = True
        return(True)

    '''
    Filter Objects
    '''

    class Filter:
        def __init__(self):
            self.rangeCriteriaDict = {}
            self.boolCriteriaDict = {}
            self.existsCriteriaDict = {}
            self.containedInList = []
            self.attrContainedInCriteriaDict = {}

        def addRangeCriteria(self, name, min, max):
            self.rangeCriteriaDict[name] = (min, max)

        def addBoolCriteria(self, name, state):
            self.boolCriteriaDict[name] = state

        def addExistsCriteria(self, name, exists):
            self.existsCriteriaDict[name] = exists

        def addAttrContainedInCriteria(self, name, list):
            self.attrContainedInCriteriaDict[name] = list

        def setContainedInList(self, list):
            self.containedInList = list

        def check(self, obj):
            if (len(self.containedInList) != 0):
                if (obj not in self.containedInList):
                    return(False)

            for rangeCriteria in self.rangeCriteriaDict.keys():
                val = getattr(obj, rangeCriteria)
                if (val != None):
                    if (self.rangeCriteriaDict[rangeCriteria][0] != None):
                        if (val < self.rangeCriteriaDict[rangeCriteria][0]):
                            return(False)
                    if (self.rangeCriteriaDict[rangeCriteria][1] != None):
                        if (val > self.rangeCriteriaDict[rangeCriteria][1]):
                            return(False)

            for boolCriteria in self.boolCriteriaDict.keys():
                if (self.boolCriteriaDict[boolCriteria] != None and getattr(obj, boolCriteria) != None):
                    if (getattr(obj, boolCriteria) != self.boolCriteriaDict[boolCriteria]):
                        return(False)

            for existsCriteria in self.existsCriteriaDict.keys():
                val = getattr(obj, existsCriteria)
                if (self.existsCriteriaDict[existsCriteria] != None and val != None):
                    if (self.existsCriteriaDict[existsCriteria] == True):
                        if (val == None):
                            return(False)
                        elif (str(val).lower().strip() == "none"):
                            return(False)
                    else:
                        if (val != None and str(val).lower().strip() != "none"):
                            return(False)

            for attrContainedIn in self.attrContainedInCriteriaDict.keys():
                if (self.attrContainedInCriteriaDict[attrContainedIn] != None and getattr(obj, attrContainedIn) != None):
                    if (getattr(obj, attrContainedIn) not in self.attrContainedInCriteriaDict[attrContainedIn]):
                        return(False)

            return(True)

        def filter(self, list):
            output = []
            for obj in list:
                if (self.check(obj)):
                    output.append(obj)

            return output

        def search(self, list, term, inDepth = False):
            filteredList = self.filter(list)
            searchedList = []
            term = term.lower()
            if (term == ""):
                return (filteredList)
            if (inDepth): # I think it works, but might have some bugs
                for obj in filteredList:
                    attributes = obj.__dict__
                    for attr in attributes.keys():
                        if (attr == "thrustCurve"):
                            continue
                        if (term in str(attributes[attr]).lower()):
                            searchedList.append(obj)
                            break
                return(searchedList)

            else:
                for obj in filteredList:
                    if (term in str(obj).lower()):
                        searchedList.append(obj)

                return(searchedList)

    '''
    Update functions for the Tkinter ListBoxes
    '''

    def refreshAll(self):
        self.updateMotorList()
        self.updateRocketList()
        self.updateElectronicsList()
        self.updateLogList()
        self.updateStats()
        self.tkinterRefresh = True


    def dynamicMotorListUpdate(self, event):
        self.updateMotorList()

    def updateMotorList(self):
        self.motors = sorted(self.motors, key=lambda x: str(x).lower())

        filter = Log.Filter()
        if(motorUsedSelection.get() == "Yes"):
            usedMotors = []
            for flight in self.flights:
                usedMotors.append(flight.motor)
            filter.setContainedInList(usedMotors)
        searchTerm = motorSearchBar.get()

        mList = filter.search(self.motors, searchTerm)

        motorList.delete(0, END)
        for m in mList:
            motorList.insert(END, m)

        self.updateLogList()

    def updateRocketList(self):
        self.rockets = sorted(self.rockets, key=lambda x: str(x).lower())
        # rocketOptions['values'] = self.rockets
        rocketList.delete(0, END)
        for r in self.rockets:
            rocketList.insert(END, r)

        self.updateLogList()

    def updateElectronicsList(self):
        self.electronics = sorted(self.electronics, key=lambda x: str(x).lower())
        # electronicsOptions['values'] = self.electronics
        logUsesElectronicsOptions['values'] = ["N/A", "Yes", "No"] + self.electronics[1:]
        electronicsList.delete(0, END)
        for e in self.electronics:
            if (str(e) != " None"):
                electronicsList.insert(END, e)

        self.updateLogList()

    def dynamicLogListUpdate(self, event):
        self.updateLogList()

    def updateLogList(self):

        # create filtered list
        filter = Log.Filter()

        '''
        Filter reading
        '''

        # electronics reading
        if (logUsesElectronicsOptions.get() == "" or logUsesElectronicsOptions.get() == "N/A"):
            filter.addExistsCriteria("electronics", None)
        elif (logUsesElectronicsOptions.get() == "Yes"):
            filter.addExistsCriteria("electronics", True)
        elif (logUsesElectronicsOptions.get() == "No"):
            filter.addExistsCriteria("electronics", False)
        else:
            filter.addBoolCriteria("electronics", self.getElectronic(logUsesElectronicsOptions.get()))

        #success reading
        if (logSuccessOnlyOptions.get() == ""):
            filter.addBoolCriteria("success", None)
        elif (logSuccessOnlyOptions.get() == "Yes"):
            filter.addBoolCriteria("success", True)
        else:
            filter.addBoolCriteria("success", None)

        # reads numbers
        try:
            # alt reading
            if (logMinAltEntry.get() == ""):
                altMin = None
            else :
                altMin = int(logMinAltEntry.get())

            if (logMaxAltEntry.get() == ""):
                altMax = None
            else:
                altMax = int(logMaxAltEntry.get())

            filter.addRangeCriteria("alt", altMin, altMax)

            # velocity reading
            if (logMinVeloEntry.get() == ""):
                veloMin = None
            else:
                veloMin = int(logMinVeloEntry.get())

            if (logMaxVeloEntry.get() == ""):
                veloMax = None
            else:
                veloMax = int(logMaxVeloEntry.get())

            filter.addRangeCriteria("velo", veloMin, veloMax)

            # accel reading
            if (logMinAccelEntry.get() == ""):
                accelMin = None
            else:
                accelMin = float(logMinAccelEntry.get())

            if (logMaxAccelEntry.get() == ""):
                accelMax = None
            else:
                accelMax = float(logMaxAccelEntry.get())

            filter.addRangeCriteria("accel", accelMin, accelMax)
        except:
            messagebox.showerror("Error", "Please enter valid numbers")

        # reading class
        if (logMinClassEntry.get() == ""):
            classificationMin = None
        else:
            classificationMin = logMinClassEntry.get()

        if (logMaxClassEntry.get() == ""):
            classificationMax = None
        else:
            classificationMax = logMaxClassEntry.get()

        filter.addRangeCriteria("classification", classificationMin, classificationMax)

        filteredLogs = filter.search(self.flights, logSearchBar.get(), inDepth=True)


        # sort filtered list
        sortType = logSortingOptions.get()
        sortReverse = logSortingReverse.get() == "Reverse"

        if (sortType == "Chronological"):
            filteredLogs.sort(key=lambda x: x.date, reverse=sortReverse)
        elif (sortType == "Altitude"):
            filteredLogs.sort(key=lambda x: x.alt.getValue(), reverse=not sortReverse)
        elif (sortType == "Velocity"):
            filteredLogs.sort(key=lambda x: x.velo.getValue(), reverse=not sortReverse)
        elif (sortType == "Acceleration"):
            filteredLogs.sort(key=lambda x: x.accel.getValue(), reverse=not sortReverse)
        else:
            messagebox.showerror("Error", "Sort type not recognized")


        # clear logList
        logList.delete(0, END)

        # build log list
        for log in filteredLogs:
            logList.insert(END, log)

        logSortingFrame.pack_forget()
        logFilteringFrame.pack_forget()
        logSortingApplyButton.pack_forget()
        logList.pack_forget()
        logShowSortFilterButton.pack(fill ="both")
        logList.pack(expand = 1, fill ="both")
        self.tkinterRefresh = True


    '''
    Show filtering and sorting
    '''
    def showLogSortingAndFilters(self):
        logShowSortFilterButton.pack_forget()
        logList.pack_forget()
        logSortingFrame.pack(expand = 1, fill ="both")
        logFilteringFrame.pack(expand = 1, fill ="both")
        logSortingApplyButton.pack(expand = 1, fill ="both")
        logList.pack(expand = 1, fill ="both")


    '''
    Get functions for reused objects (rockets, electronics, motors)
    '''

    def getRocket(self, name):
        for i in range (len(self.rockets)):
            if (self.rockets[i].name == name):
                return(self.rockets[i])
        return(None)

    def getMotor(self, name):
        for i in range (len(self.motors)):
            if (str(self.motors[i]) == name):
                return(self.motors[i])
        return(None)

    def getElectronic(self, name):
        for i in range (len(self.electronics)):
            if (str(self.electronics[i]) == name):
                return(self.electronics[i])
        return(None)

    def getFlight(self, name):
        for i in range (len(self.flights)):
            if (str(self.flights[i]) == name):
                return(self.flights[i])
        return(None)


    '''
    Tkinter functions to delete an entry
    '''

    def deleteFlight(self, flight):
        # if (flight.FDFilename != ""):
        #     os.remove(flight.FDFilename)
        self.flights.remove(flight)
        self.updateLogList()
        self.saveJSON()
        self.tkinterRefresh = True

    def deleteRocket(self, rocket):
        self.rockets.remove(rocket)
        self.updateRocketList()
        self.saveJSON()
        self.tkinterRefresh = True

    def deleteElectronic(self, electronic):

        self.electronics.remove(electronic)
        self.updateElectronicsList()
        self.saveJSON()
        self.tkinterRefresh = True


    '''
    Copy/Paste/Cut management
    '''
    def copy(self):
        if(tabControl.index("current") == 0):
            if (len(logList.curselection()) != 0):
                self.copiedObj = self.getFlight(logList.selection_get())
        elif(tabControl.index("current") == 1):
            if (len(rocketList.curselection()) != 0):
                self.copiedObj = self.getRocket(rocketList.selection_get())
        elif(tabControl.index("current") == 2):
            if (len(electronicsList.curselection()) != 0):
                self.copiedObj = self.getElectronic(electronicsList.selection_get())

    def paste(self):
        if (self.copiedObj == None):
            return
        elif (isinstance(self.copiedObj, Flight)):
            self.addFlight(self.copiedObj)
            self.addRocket(self.copiedObj.rocket)
            self.addElectronic(self.copiedObj.electronics)
        elif (isinstance(self.copiedObj, Rocket)):
            self.addRocket(self.copiedObj)
        elif (isinstance(self.copiedObj, Electronic)):
            self.addElectronic(self.copiedObj)

    def delete(self):
        if (tabControl.index("current") == 0):
            if (len(logList.curselection()) != 0):
                self.deleteFlight(self.getFlight(logList.selection_get()))
        elif (tabControl.index("current") == 1):
            if (len(rocketList.curselection()) != 0):
                self.deleteRocket(self.getRocket(rocketList.selection_get()))
        elif (tabControl.index("current") == 2):
            if (len(electronicsList.curselection()) != 0):
                self.deleteElectronic(self.getElectronic(electronicsList.selection_get()))

    def cut(self):
        self.copy()
        self.delete()

    '''
    Update statistics info
    '''
    def updateStats(self):
        statsText['state'] = 'normal'
        statsText.delete("1.0", END)
        statsText.insert(END, log.getStats("All"))
        statsText['state'] = 'disabled'


    '''
    Object class that handles creating and updating log entries
    '''
    class LogManagementWindow:
        def __init__(self, log):
            self.log = log


        def openPopup(self, purpose):
            self.currLog = None
            self.createLogWindow = Popup(window)
            if (purpose == "create"):
                self.createLogWindow.title("Create Log")
                self.createLogWindow.bind("<Return>", lambda event: self.createLog())
            elif (purpose == "update"):
                self.createLogWindow.title("Update Log")
                logSelectFrame = LabelFrame(self.createLogWindow, text="Select Log")
                self.logSelectComboBox = Combobox(logSelectFrame, values=self.log.flights, state="readonly")
                if (len(logList.curselection()) != 0):
                    self.logSelectComboBox.set(str(self.log.getFlight(logList.selection_get())))
                self.logSelectComboBox.pack(fill="x")
                self.logSelectComboBox.bind("<<ComboboxSelected>>", self.fillInOldInfo)
                logSelectFrame.pack(expand = 1, fill ="x")
                self.createLogWindow.bind("<Return>", lambda event: self.updateLog())

            createLogFrame = Frame(self.createLogWindow)

            logAddFrame = InputFrame(createLogFrame)

            self.rocketOptions = Combobox(logAddFrame,values=self.log.rockets, state="readonly")
            logAddFrame.addInput(self.rocketOptions, "Rocket: ")

            self.cal = Calendar(logAddFrame)
            logAddFrame.addInput(self.cal, "Date: ")

            self.motorOptions = Combobox(logAddFrame, values=self.log.motors)
            self.motorOptions.bind('<KeyRelease>', self.motorSearch)
            logAddFrame.addInput(self.motorOptions, "Motor: ")

            self.electronicsOptions = Combobox(logAddFrame, values=self.log.electronics, state="readonly")
            logAddFrame.addInput(self.electronicsOptions, "Electronics: ")

            self.deployModeOptions = Combobox(logAddFrame, values=["Motor", "Single", "Dual"], state="readonly")
            logAddFrame.addInput(self.deployModeOptions, "Deploy Mode: ")

            self.electronicsFileButton = Button(logAddFrame, text="Select Flight Data File", command=self.selectFDFile)
            self.electronicsFilename = Label(logAddFrame, text="Select File")
            logAddFrame.addInput(self.electronicsFileButton, self.electronicsFilename, swap=True)

            self.altitudeEntry = Entry(logAddFrame)
            logAddFrame.addInput(self.altitudeEntry, "Altitude ("+self.log.preferences.altitudeUnit+"): ")

            self.velocityEntry = Entry(logAddFrame)
            logAddFrame.addInput(self.velocityEntry, "Velocity ("+self.log.preferences.velocityUnit+"): ")

            self.accelerationEntry = Entry(logAddFrame)
            logAddFrame.addInput(self.accelerationEntry, "Acceleration ("+self.log.preferences.accelerationUnit+"): ")

            self.successEntry = Combobox(logAddFrame, values=["True", "False"], state="readonly")
            logAddFrame.addInput(self.successEntry, "Success: ")

            self.clearLogButton = Button(logAddFrame, text="Clear", command=self.clear)
            self.logButton = Button(logAddFrame, text="Log", command=self.createLog)
            self.updateButton = Button(logAddFrame, text="Update", command=self.updateLog)


            self.clearLogButton.grid(row=10, column=0)

            if (purpose == "create"):
                self.logButton.grid(row=10, column=1)
            elif (purpose == "update"):
                self.updateButton.grid(row=10, column=1)


            logAddFrame.pack(expand=1, fill=BOTH, side=LEFT)
            logAddFrame.pack_propagate(0)

            logNotesFrame = Frame(createLogFrame)

            notesLabel = Label(logNotesFrame, text="Notes: ")
            self.notesEntry = Text(logNotesFrame, wrap=WORD)

            notesLabel.grid(row=0, column=0)
            self.notesEntry.grid(row=0, column=1)

            logNotesFrame.pack(expand=1, fill=BOTH, side=LEFT)


            createLogFrame.pack(expand=1, fill=BOTH)
            if (purpose == "update"):
                self.fillInOldInfo("")

        def fillInOldInfo(self, event):
            self.currLog = self.log.getFlight(self.logSelectComboBox.get())
            if (self.currLog == None):
                return
            self.rocketOptions.set(str(self.currLog.rocket))
            self.cal.selection_set(self.currLog.date)
            self.motorOptions.set(str(self.currLog.motor))
            self.electronicsOptions.set(str(self.currLog.electronics))
            if (self.currLog.deployMode == DeployMode.MOTOR):
                self.deployModeOptions.set("Motor")
            elif (self.currLog.deployMode == DeployMode.SINGLE):
                self.deployModeOptions.set("Single")
            else:
                self.deployModeOptions.set("Dual")

            self.altitudeEntry.delete(0, END)
            self.velocityEntry.delete(0, END)
            self.accelerationEntry.delete(0, END)

            self.altitudeEntry.insert(END, self.currLog.alt.getValue())
            self.velocityEntry.insert(END, self.currLog.velo.getValue())
            self.accelerationEntry.insert(END, self.currLog.accel.getValue())


            if (self.currLog.success):
                self.successEntry.set("True")
            else:
                self.successEntry.set("False")
            self.notesEntry.delete("1.0", END)
            self.notesEntry.insert(END, self.currLog.notes)

        def openCreatePopup(self):
            self.openPopup("create")

        def openUpdatePopup(self):
            self.openPopup("update")

        def motorSearch(self, event):
            search = self.motorOptions.get()
            motors = []

            for motor in self.log.motors:
                if (search.lower() in str(motor).lower()):
                    motors.append(motor)

            self.motorOptions['values'] = motors

        def addFDFile(self):
            if (len(logList.curselection()) == 0):
                messagebox.showerror("Error", "Please select a log")
                return
            currLog = self.log.getFlight(logList.selection_get())
            if (currLog == None):
                messagebox.showerror("Error", "Please select a log")
                return
            FDFilename = askopenfilename(filetypes=[("Known Filetypes", ".csv .fbb .olfd"), ("OpenLog", ".csv .olfd"), ("Eggtimer (.csv)", ".csv"), ("Fluctus (.fbb)", ".fbb"), ("All Files", ".*")])
            if (FDFilename == ""):
                return

            FDFSuffix = FDFilename.split(".")[-1]
            if (currLog.FDFilename == "" or not currLog.FDFilename.endswith(FDFSuffix)):
                FDFIndex = 0

                newName = "data/flightData/" + str(FDFIndex) + "." + FDFSuffix
                while (os.path.exists(newName)):
                    FDFIndex += 1
                    newName = "data/flightData/" + str(FDFIndex) + "." + FDFSuffix

                currLog.FDFilename = newName

            shutil.copy(FDFilename, currLog.FDFilename)
            data = DataReader.readFile(currLog.FDFilename)
            if (data == None):
                messagebox.showerror("Error", "Error reading file")
                return
            if (data.getApogee() != 0 and currLog.electronics.altSpecific):
                currLog.alt = Number(round(data.getApogee()), Number.Type.ALT, self.log.preferences,
                                      alreadyMetric=True)
            if (data.getMaxVelo() != 0 and currLog.electronics.veloSpecific):
                currLog.velo = Number(round(data.getMaxVelo()), Number.Type.VELO, self.log.preferences,
                                       alreadyMetric=True)
            if (data.getMaxAccel() != 0 and currLog.electronics.accelSpecific):
                currLog.accel = Number(round(data.getMaxAccel(), 1), Number.Type.ACCEL, self.log.preferences,
                                        alreadyMetric=True)

            self.log.updateLogList()

            self.log.saveJSON()
            self.log.tkinterRefresh = True
            messagebox.showinfo("Success", "Flight data file added successfully!")

        def removeFDFile(self):
            if (len(logList.curselection()) == 0):
                messagebox.showerror("Error", "Please select a log")
                return
            currLog = self.log.getFlight(logList.selection_get())
            if (currLog == None):
                messagebox.showerror("Error", "Please select a log")
                return

            if (currLog.FDFilename == ""):
                messagebox.showerror("Error", "Log does not have a flight data file")
                return

            if (messagebox.askokcancel("Remove Flight Data File", "Are you sure you want to remove the flight data file?")):

                currLog.FDFilename = ""

                self.log.saveJSON()



                messagebox.showinfo("Success", "Flight data file removed successfully!")

        def selectFDFile(self):
            FDFilename = askopenfilename(filetypes=[("Known Filetypes", ".csv .fbb .olfd"), ("OpenLog", ".csv .olfd"), ("Eggtimer (.csv)", ".csv"), ("Fluctus (.fbb)", ".fbb"), ("All Files", ".*")])
            if (FDFilename == ""):
                return
            self.electronicsFilename['text'] = FDFilename





            data = DataReader.readFile(self.electronicsFilename['text'])
            if (data == None):
                messagebox.showerror("Error", "Error reading file")
            if (self.electronicsOptions.get() == ""):
                if (data.getApogee() != 0 and self.altitudeEntry.get() == ""):
                    self.altitudeEntry.delete(0, END)
                    self.altitudeEntry.insert(END, Number(data.getApogee(), Number.Type.ALT, self.log.preferences, alreadyMetric=True).getValue())

                if (data.getMaxVelo() != 0 and self.velocityEntry.get() == ""):
                    self.velocityEntry.delete(0, END)
                    self.velocityEntry.insert(END, Number(data.getMaxVelo(), Number.Type.VELO, self.log.preferences, alreadyMetric=True).getValue())

                if (data.getMaxAccel() != 0 and self.accelerationEntry.get() == ""):
                    self.accelerationEntry.delete(0, END)
                    self.accelerationEntry.insert(END, Number(data.getMaxAccel(), Number.Type.ACCEL, self.log.preferences, alreadyMetric=True).getValue())
            else:
                electronic = self.log.getElectronic(self.electronicsOptions.get())
                if (data.getApogee() != 0 and (electronic.altSpecific or self.altitudeEntry.get() == "")):
                    self.altitudeEntry.delete(0, END)
                    self.altitudeEntry.insert(END, Number(data.getApogee(), Number.Type.ALT, self.log.preferences, alreadyMetric=True).getValue())

                if (data.getMaxVelo() != 0) and (electronic.veloSpecific or self.velocityEntry.get() == ""):
                    self.velocityEntry.delete(0, END)
                    self.velocityEntry.insert(END, Number(data.getMaxVelo(), Number.Type.VELO, self.log.preferences, alreadyMetric=True).getValue())

                if (data.getMaxAccel() != 0 and (electronic.accelSpecific or self.accelerationEntry.get() == "")):
                    self.accelerationEntry.delete(0, END)
                    self.accelerationEntry.insert(END, Number(data.getMaxAccel(), Number.Type.ACCEL, self.log.preferences, alreadyMetric=True).getValue())


            self.createLogWindow.focus_set()

        def createLog(self):
            try:

                rocket = self.log.getRocket(self.rocketOptions.get())
                date = datetime.datetime.strptime(self.cal.get_date(), "%m/%d/%y")
                motor = self.log.getMotor(self.motorOptions.get())
                if (motor == None and len(self.motorOptions['values']) == 1):
                    motor = self.log.getMotor(self.motorOptions['values'][0])
                motor.totalImpulse # check if it exists

                electronics = self.log.getElectronic(self.electronicsOptions.get())
                deployMode = self.deployModeOptions.get()
                if (deployMode == "Dual"):
                    deployMode = DeployMode.DUAL
                elif (deployMode == "Single"):
                    deployMode = DeployMode.SINGLE
                else:
                    deployMode = DeployMode.MOTOR

                FDFilename = ""
                if (self.electronicsFilename['text'] != "Select File"):

                    FDFIndex = 0
                    FDFSuffix = self.electronicsFilename['text'].split(".")[-1]
                    FDFilename = "data/flightData/" + str(FDFIndex) + "." + FDFSuffix
                    while (os.path.exists(FDFilename)):
                        FDFIndex += 1
                        FDFilename = "data/flightData/" + str(FDFIndex) + "." + FDFSuffix

                    shutil.copy(self.electronicsFilename['text'], FDFilename)
                    # data = DataReader.readFile(FDFilename)
                    # alt = Number(round(data.getApogee()), Number.Type.ALT, self.log.preferences, alreadyMetric=True)
                    # velo = Number((data.getMaxVelo()), Number.Type.VELO, self.log.preferences, alreadyMetric=True)
                    # accel = Number(round(data.getMaxAccel(), 1), Number.Type.ACCEL, self.log.preferences, alreadyMetric=True)

                if (self.altitudeEntry.get() != ""):
                    alt = Number(int(self.altitudeEntry.get()), Number.Type.ALT, self.log.preferences)
                if (self.velocityEntry.get() != ""):
                    velo = Number(int(self.velocityEntry.get()), Number.Type.VELO, self.log.preferences)
                if (self.accelerationEntry.get() != ""):
                    accel = Number(float(self.accelerationEntry.get()), Number.Type.ACCEL, self.log.preferences)

                success = self.successEntry.get()
                if (success == "True"):
                    success = True
                else:
                    success = False

                notes = self.notesEntry.get("1.0", END)

                flight = Flight(motor, rocket, electronics, deployMode, date, FDFilename, alt, velo, accel, success,
                                notes)

                self.createLogWindow.destroy()
                self.log.tkinterRefresh = True
                messagebox.showinfo("Success", "Log created successfully!")

            except:
                messagebox.showerror("Error!", "Error in log input fields!")
                return

            self.log.addFlight(flight)

        def updateLog(self):
            self.currLog = self.log.getFlight(self.logSelectComboBox.get())

            if (self.currLog == None):
                messagebox.showerror("Error!", "Please select a log to update!")
                return

            try:

                rocket = self.log.getRocket(self.rocketOptions.get())
                if (rocket != None):
                    self.currLog.rocket = rocket
                date = datetime.datetime.strptime(self.cal.get_date(), "%m/%d/%y")
                if (date != None and date.strftime("%m/%d/%y") != datetime.datetime.today().strftime("%m/%d/%y")):
                    self.currLog.date = date
                motor = self.log.getMotor(self.motorOptions.get())
                if (motor == None and len(self.motorOptions['values']) == 1):
                    motor = self.log.getMotor(self.motorOptions['values'][0])
                if (motor != None):
                    self.currLog.motor = motor
                electronics = self.log.getElectronic(self.electronicsOptions.get())
                if (electronics != None):
                    self.currLog.electronics = electronics
                deployMode = self.deployModeOptions.get()
                if (deployMode == "Dual"):
                    deployMode = DeployMode.DUAL
                elif (deployMode == "Single"):
                    deployMode = DeployMode.SINGLE
                elif (deployMode == "Motor"):
                    deployMode = DeployMode.MOTOR
                else:
                    deployMode = None

                if (deployMode != None):
                    self.currLog.deployMode = deployMode

                alt = self.altitudeEntry.get()
                if (alt != "" and alt != str(self.currLog.alt.getValue())):
                    self.currLog.alt.setValue(int(alt))

                velo = self.velocityEntry.get()
                if (velo != "" and velo != str(self.currLog.velo.getValue())):
                    self.currLog.velo.setValue(int(velo))
                accel = self.accelerationEntry.get()
                if (accel != "" and accel != str(self.currLog.accel.getValue())):
                    self.currLog.accel.setValue(float(accel))

                if (self.electronicsFilename['text'] != "Select File"):
                    FDFSuffix = self.electronicsFilename['text'].split(".")[-1]
                    if (self.currLog.FDFilename == "" or not self.currLog.FDFilename.endswith(FDFSuffix)):
                        FDFIndex = 0

                        FDFilename = "data/flightData/" + str(FDFIndex) + "." + FDFSuffix
                        while (os.path.exists(FDFilename)):
                            FDFIndex += 1
                            FDFilename = "data/flightData/" + str(FDFIndex) + "." + FDFSuffix

                        self.currLog.FDFilename = FDFilename

                    shutil.copy(self.electronicsFilename['text'], self.currLog.FDFilename)
                    # data = DataReader.readFile(self.currLog.FDFilename)
                    # if (data.getApogee() != 0):
                    #     self.currLog.alt = Number(round(data.getApogee()), Number.Type.ALT, self.log.preferences, alreadyMetric=True)
                    # if (data.getMaxVelo() != 0):
                    #     self.currLog.velo = Number(round(data.getMaxVelo()), Number.Type.VELO, self.log.preferences, alreadyMetric=True)
                    # if (data.getMaxAccel() != 0):
                    #     self.currLog.accel = Number(round(data.getMaxAccel(), 1), Number.Type.ACCEL, self.log.preferences, alreadyMetric=True)


                success = self.successEntry.get()
                if (success == "True"):
                    success = True
                elif (success == "False"):
                    success = False
                else:
                    success = None
                if (success != None):
                    self.currLog.success = success

                notes = self.notesEntry.get("1.0", END)
                if (notes.strip() != ""):
                    self.currLog.notes = notes

                # clear inputs
                self.createLogWindow.destroy()

                self.log.updateLogList()

                self.log.saveJSON()
                self.log.tkinterRefresh = True
                messagebox.showinfo("Success", "Log updated successfully!")
            except:
                messagebox.showerror("Error!", "Error in log update input fields!")

        def clear(self):
            self.rocketOptions.set("")
            self.motorOptions.set("")
            self.electronicsOptions.set("")
            self.deployModeOptions.set("")
            self.electronicsFilename['text'] = "Select File"
            self.altitudeEntry.delete(0, END)
            self.velocityEntry.delete(0, END)
            self.accelerationEntry.delete(0, END)
            self.successEntry.set("")
            self.notesEntry.delete("1.0", END)


    '''
    Object class that handles creating and updating rocket entries
    '''
    class RocketManagementWindow:
        def __init__(self, log):
            self.log = log

        def openPopup(self, purpose):
            self.rocketWindow = Popup(window)
            if (purpose == "create"):
                self.rocketWindow.title("Create Rocket")
                self.rocketWindow.bind("<Return>", lambda event: self.createRocket())
            elif (purpose == "update"):
                self.rocketWindow.title("Update Rocket")
                rocketSelectFrame = LabelFrame(self.rocketWindow, text="Select Rocket")
                self.rocketSelectComboBox = Combobox(rocketSelectFrame, values=self.log.rockets, state="readonly")
                if (len(rocketList.curselection()) != 0):
                    self.rocketSelectComboBox.set(str(self.log.getRocket(rocketList.selection_get())))
                self.rocketSelectComboBox.pack(fill="x")
                self.rocketSelectComboBox.bind("<<ComboboxSelected>>", self.fillInOldInfo)
                rocketSelectFrame.pack(expand=1, fill="x")
                self.rocketWindow.bind("<Return>", lambda event: self.updateRocket())

            rocketInputsFrame = InputFrame(self.rocketWindow)
            self.rocketNameEntry = Entry(rocketInputsFrame)
            rocketInputsFrame.addInput(self.rocketNameEntry, "Rocket Name: ")

            self.rocketDiameterEntry = Entry(rocketInputsFrame)
            rocketInputsFrame.addInput(self.rocketDiameterEntry, "Diameter ("+self.log.preferences.rocketDimensionUnit+"): ")

            self.rocketLengthEntry = Entry(rocketInputsFrame)
            rocketInputsFrame.addInput(self.rocketLengthEntry, "Length ("+self.log.preferences.rocketDimensionUnit+"): ")

            self.rocketMMTOptions = Combobox(rocketInputsFrame, values=["13mm", "18mm", "24mm", "29mm", "38mm", "54mm", "75mm", "98mm"])
            rocketInputsFrame.addInput(self.rocketMMTOptions, "MMT: ")

            rocketClearButton = Button(rocketInputsFrame, text="Clear", command=rocketInputsFrame.clear)
            rocketCreateButton = Button(rocketInputsFrame, text="Add", command=self.createRocket)
            rocketUpdateButton = Button(rocketInputsFrame, text="Update", command=self.updateRocket)

            rocketClearButton.grid(row=4, column=0)
            if (purpose == "create"):
                rocketCreateButton.grid(row=4, column=1)
            elif (purpose == "update"):
                rocketUpdateButton.grid(row=4, column=1)
                self.fillInOldInfo("")

            rocketInputsFrame.pack(expand=1, fill="both")


        def fillInOldInfo(self, event):
            self.currRocket = self.log.getRocket(self.rocketSelectComboBox.get())
            if (self.currRocket == None):
                return
            self.rocketNameEntry.delete(0, END)
            self.rocketNameEntry.insert(0, self.currRocket.name)
            self.rocketDiameterEntry.delete(0, END)
            self.rocketDiameterEntry.insert(0, self.currRocket.diameter.getValue())
            self.rocketLengthEntry.delete(0, END)
            self.rocketLengthEntry.insert(0, self.currRocket.length.getValue())
            self.rocketMMTOptions.set(str(self.currRocket.MMT) + "mm")


        def openCreatePopup(self):
            self.openPopup("create")

        def openUpdatePopup(self):
            self.openPopup("update")

        def clearRocketEntries(self):
            self.rocketNameEntry.delete(0, END)
            self.rocketDiameterEntry.delete(0, END)
            self.rocketLengthEntry.delete(0, END)
            self.rocketMMTOptions.set("")

        def createRocket(self):
            try:
                name = self.rocketNameEntry.get()
                diameter = Number(float(self.rocketDiameterEntry.get()), Number.Type.RKTDIM, self.log.preferences)
                length = Number(float(self.rocketLengthEntry.get()), Number.Type.RKTDIM, self.log.preferences)

                MMTInputStr = self.rocketMMTOptions.get().replace(" ", "")
                MMT = ""
                for c in MMTInputStr:
                    if (c.isdigit()):
                        MMT += c
                    else:
                        break
                MMT = int(MMT)


                rocket = Rocket(name, diameter, length, MMT)
                if (self.log.addRocket(rocket)):
                    self.rocketWindow.destroy()
                    self.log.tkinterRefresh = True
                    messagebox.showinfo("Success", "Rocket created successfully")
                else:
                    messagebox.showerror("Error!", "Rocket already exists!")
            except:
                messagebox.showerror("Error!", "Error in rocket input fields!")

        def updateRocket(self):
            self.currRocket = self.log.getRocket(self.rocketSelectComboBox.get())
            if (self.currRocket == None):
                messagebox.showerror("Error!", "Please select a rocket to update!")
                return
            try:
                name = self.rocketNameEntry.get()
                if (name != ""):
                    self.currRocket.name = name
                diameter = self.rocketDiameterEntry.get()
                if (diameter != ""):
                    self.currRocket.diameter.setValue(float(diameter))
                length = self.rocketLengthEntry.get()
                if (length != ""):
                    self.currRocket.length.setValue(float(length))
                MMT = self.rocketMMTOptions.get()
                if (MMT != ""):
                    self.currRocket.MMT = int(MMT[:-2])

                self.rocketWindow.destroy()
                self.log.updateRocketList()
                self.log.saveJSON()
                self.log.tkinterRefresh = True
                messagebox.showinfo("Success", "Rocket updated successfully")
            except:
                messagebox.showerror("Error!", "Error in rocket update input fields!")

        def addPicture(self):
            if (len(rocketList.curselection()) == 0):
                return
            rocket = self.log.getRocket(rocketList.selection_get())
            if (rocket != None):
                rocket.setPicture(askopenfilename(filetypes=[("Photos", ".png .jpeg")]))
                self.log.saveJSON()
                self.log.refreshAll()
                if (rocket.picture != ""):
                    messagebox.showinfo("Success", "Photo added successfully")

        def removePicture(self):
            if (len(rocketList.curselection()) == 0):
                return
            if (messagebox.askokcancel("Remove Picure", "Are you sure you want to remove the picture?")):
                self.log.getRocket(rocketList.selection_get()).picture = ""
                self.log.saveJSON()
                self.log.refreshAll()
                messagebox.showinfo("Success", "Picture removed successfully")


    '''
    Object class that handles creating and updating electronics
    '''
    class ElectronicManagementWindow:
        def __init__(self, log):
            self.log = log

        def openPopup(self, purpose):
            self.electronicsWindow = Popup(window)

            if (purpose == "create"):
                self.electronicsWindow.title("Create Electronic")
                self.electronicsWindow.bind("<Return>", lambda event: self.createElectronic())
            elif (purpose == "update"):
                self.electronicsWindow.title("Update Electronic")
                electronicSelectFrame = LabelFrame(self.electronicsWindow, text="Select Electronic")
                self.electronicSelectComboBox = Combobox(electronicSelectFrame, values=self.log.electronics, state="readonly")
                if (len(electronicsList.curselection()) != 0):
                    self.electronicSelectComboBox.set(str(self.log.getElectronic(electronicsList.selection_get())))
                self.electronicSelectComboBox.pack(fill="x")
                self.electronicSelectComboBox.bind("<<ComboboxSelected>>", self.fillInOldInfo)
                electronicSelectFrame.pack(expand=1, fill="x")
                self.electronicsWindow.bind("<Return>", lambda event: self.updateElectronic())

            electronicInfoFrame = InputFrame(self.electronicsWindow)
            self.electronicsNameEntry = Entry(electronicInfoFrame)
            electronicInfoFrame.addInput(self.electronicsNameEntry, "Name: ")

            self.electronicsManufacturerEntry = Entry(electronicInfoFrame)
            electronicInfoFrame.addInput(self.electronicsManufacturerEntry, "Manufacturer: ")

            self.electronicsAltSpecificEntry = Combobox(electronicInfoFrame, values=["Yes", "No"], state="readonly")
            electronicInfoFrame.addInput(self.electronicsAltSpecificEntry, "Is Altitude Specific?: ")

            self.electronicsVeloSpecificEntry = Combobox(electronicInfoFrame, values=["Yes", "No"], state="readonly")
            electronicInfoFrame.addInput(self.electronicsVeloSpecificEntry, "Is Velocity Specific?: ")

            self.electronicsAccelSpecificEntry = Combobox(electronicInfoFrame, values=["Yes", "No"], state="readonly")
            electronicInfoFrame.addInput(self.electronicsAccelSpecificEntry, "Is Acceleration Specific?: ")

            electronicsClearButton = Button(electronicInfoFrame, text="Clear", command=self.clearElectronicEntries)
            if (purpose == "create"):
                createElectronicButton = Button(electronicInfoFrame, text="Create", command=self.createElectronic)
            elif (purpose == "update"):
                updateElectronicButton = Button(electronicInfoFrame, text="Update", command=self.updateElectronic)


            electronicsClearButton.grid(row=5, column=0)
            if (purpose == "create"):
                createElectronicButton.grid(row=5, column=1)
            elif (purpose == "update"):
                updateElectronicButton.grid(row=5, column=1)
                self.fillInOldInfo("")

            electronicInfoFrame.pack(expand=1, fill="both")

        def fillInOldInfo(self, event):
            self.currElectronic = self.log.getElectronic(self.electronicSelectComboBox.get())
            if (self.currElectronic == None):
                return
            self.electronicsNameEntry.delete(0, END)
            self.electronicsNameEntry.insert(0, self.currElectronic.name)
            self.electronicsManufacturerEntry.delete(0, END)
            self.electronicsManufacturerEntry.insert(0, self.currElectronic.manufacturer)
            if (self.currElectronic.altSpecific):
                self.electronicsAltSpecificEntry.set("Yes")
            else:
                self.electronicsAltSpecificEntry.set("No")
            if (self.currElectronic.veloSpecific):
                self.electronicsVeloSpecificEntry.set("Yes")
            else:
                self.electronicsVeloSpecificEntry.set("No")
            if (self.currElectronic.accelSpecific):
                self.electronicsAccelSpecificEntry.set("Yes")
            else:
                self.electronicsAccelSpecificEntry.set("No")

        def openCreatePopup(self):
            self.openPopup("create")

        def openUpdatePopup(self):
            self.openPopup("update")

        def clearElectronicEntries(self):
            self.electronicsNameEntry.delete(0, END)
            self.electronicsManufacturerEntry.delete(0, END)
            self.electronicsAltSpecificEntry.delete(0, END)
            self.electronicsVeloSpecificEntry.delete(0, END)
            self.electronicsAccelSpecificEntry.delete(0, END)

        def createElectronic(self):
            try:
                name = self.electronicsNameEntry.get()
                manufacturer = self.electronicsManufacturerEntry.get()
                altSpecific = (self.electronicsAltSpecificEntry.get() == "Yes")
                veloSpecific = (self.electronicsVeloSpecificEntry.get() == "Yes")
                accelSpecific = (self.electronicsAccelSpecificEntry.get() == "Yes")

                electronic = Electronic(name, manufacturer, altSpecific, veloSpecific, accelSpecific)
                if (self.log.addElectronic(electronic)):
                    self.electronicsWindow.destroy()
                    messagebox.showinfo("Success", "Electronic created successfully!")
                else:
                    messagebox.showerror("Error!", "Electronic already exists!")
                self.log.tkinterRefresh = True
            except:
                messagebox.showerror("Error!", "Error in electronics input fields!")

        def updateElectronic(self):
            self.currElectronic = self.log.getElectronic(self.electronicSelectComboBox.get())
            if (self.currElectronic == None):
                messagebox.showerror("Error!", "Please select electronic to update!")
                return
            try:
                name = self.electronicsNameEntry.get()
                if (name != ""):
                    self.currElectronic.name = name
                manufacturer = self.electronicsManufacturerEntry.get()
                if (manufacturer != ""):
                    self.currElectronic.manufacturer = manufacturer
                altSpecific = self.electronicsAltSpecificEntry.get()
                if (altSpecific != ""):
                    self.currElectronic.altSpecific = (altSpecific == "Yes")
                veloSpecific = self.electronicsVeloSpecificEntry.get()
                if (veloSpecific != ""):
                    self.currElectronic.veloSpecific = (veloSpecific == "Yes")
                accelSpecific = self.electronicsAccelSpecificEntry.get()
                if (accelSpecific != ""):
                    self.currElectronic.accelSpecific = (accelSpecific == "Yes")

                self.electronicsWindow.destroy()
                self.log.updateElectronicsList()
                self.log.saveJSON()
                self.log.tkinterRefresh = True
                messagebox.showinfo("Success", "Electronic updated successfully!")

            except:
                messagebox.showerror("Error!", "Error in electronics update input fields!")

    '''
    Data Viewer
    '''
    def openDataViewer(self):
        global windowClosed
        if (tabControl.index("current") != 0):
            messagebox.showerror("Error!", "Can only view flight data!")
            return
        if (len(logList.curselection()) == 0):
            messagebox.showerror("Error!", "Please select a flight log!")
            return
        currLog = log.getFlight(logList.selection_get())
        if (currLog == None):
            messagebox.showerror("Error!", "Please select a flight log!")
            return
        if (currLog.FDFilename == ""):
            messagebox.showerror("Error!", "Flight log does not have an assigned flight data file!")
            return
        data = DataReader.readFile(currLog.FDFilename)

        dataViewerWindow = Popup(window, title="Data Viewer")

        windowOpen = {"Open": True}
        dataViewerWindow.protocol("WM_DELETE_WINDOW", lambda: [dataViewerWindow.destroy(), windowOpen.update({"Open": False})])
        dataViewerWindow.bind("<Escape>", lambda event: [dataViewerWindow.destroy(), windowOpen.update({"Open": False})])

        checklist = CheckList(dataViewerWindow)
        checklist.addBoxes(data.getDataArrayOptions())
        checklist.pack()



        fig = Figure(figsize=(8, 5), dpi=100)
        canvas = tkagg.FigureCanvasTkAgg(fig, master=dataViewerWindow)
        toolbar = tkagg.NavigationToolbar2Tk(canvas, dataViewerWindow)

        prevSelection = []
        while windowOpen["Open"] and not windowClosed:
            selectedGraphs = checklist.getChecked()
            if (selectedGraphs != prevSelection):

                prevSelection = selectedGraphs
                fig.clear()
                plot = fig.add_subplot()
                index = 0
                for graph in selectedGraphs:
                    if (index == 0):
                        twin = plot
                    else:
                        twin = plot.twinx()
                        if (index > 1):
                            twin.spines.right.set_position(("axes", 1.4*(index-1)))
                    index += 1

                    dataArr = data.getArray(graph)
                    color = "-b"
                    if (graph == "Altitude"):
                        type = Number.Type.ALT
                        twin.set_ylabel(graph + " (" + self.preferences.altitudeUnit + ")")
                        color = "-b"
                    elif (graph == "Velocity"):
                        type = Number.Type.VELO
                        twin.set_ylabel(graph + " (" + self.preferences.velocityUnit + ")")
                        color = "-g"
                    elif (graph == "Acceleration"):
                        type = Number.Type.ACCEL
                        twin.set_ylabel(graph + " (" + self.preferences.accelerationUnit + ")")
                        color = "-r"

                    coef = Number(1, type, self.preferences)

                    for i in range(len(dataArr)):
                        dataArr[i] =  float(dataArr[i])/coef.value


                    # plotting the graph
                    twin.plot(data.getTimeArray(), dataArr, color)
                    twin.set_ylim(1.2*min(dataArr), 1.2*max(dataArr))

                    plot.grid(True)

                plot.set_xlabel("Time (s)")
                fig.legend(selectedGraphs)
                fig.tight_layout()



                # creating the Tkinter canvas
                # containing the Matplotlib figure

                canvas.draw()

                # placing the canvas on the Tkinter window
                canvas.get_tk_widget().pack()

                # creating the Matplotlib toolbar

                toolbar.update()

                # placing the toolbar on the Tkinter window
                canvas.get_tk_widget().pack()

            window.update()

    '''
    JSON file operations
    '''

    def getJSON(self):
        JSON = "{\n"

        JSON += "\"rockets\": [\n"
        for rocket in self.rockets:
            JSON += rocket.getJSON() + ",\n"
        if (len(self.rockets) > 0):
            JSON = JSON[:-2]
        JSON += "\n],\n"

        JSON += "\"electronics\": [\n"
        for electronic in self.electronics:
            if (electronic.name == "None"):
                continue
            JSON += electronic.getJSON() + ",\n"
        if (len(self.electronics) > 1):
            JSON = JSON[:-2]
        JSON += "\n],\n"

        JSON += "\"flights\": [\n"
        for flight in self.flights:
            JSON += flight.getJSON() + ",\n"
        if (len(self.flights) > 0):
            JSON = JSON[:-2]
        JSON += "\n]\n"
        JSON += "}"
        return JSON

    def saveJSON(self):
        self.URHandler.addState()
        if (preferences.logFile != ""):
            with open(preferences.logFile, "w") as JSONFile:
                JSONFile.write(self.getJSON())

    def parseJSON(self, JSON):
        data = json.loads(JSON)

        self.clear()

        self.motors = MotorReader.readMotors("data/motors/")

        # read rockets
        for rocket in data.get("rockets"):
            name = rocket.get("name")
            diameter = Number(rocket.get("diameter"), Number.Type.RKTDIM, self.preferences, alreadyMetric=True)
            length = Number(rocket.get("length"), Number.Type.RKTDIM, self.preferences, alreadyMetric=True)
            MMT = rocket.get("MMT")
            r = Rocket(name, diameter, length, MMT)
            if ("Picture" in rocket.keys()):
                r.picture = rocket.get("Picture")

            self.rockets.append(r)

        # read electronics
        for electronic in data.get("electronics"):
            name = electronic.get("name")
            manufacturer = electronic.get("manufacturer")
            altSpecific = electronic.get("altSpecific")
            veloSpecific = electronic.get("veloSpecific")
            accelSpecific = electronic.get("accelSpecific")

            self.electronics.append(Electronic(name, manufacturer, altSpecific, veloSpecific, accelSpecific))

        # read flights
        for flight in data.get("flights"):
            motor = self.getMotor(flight.get("motor"))
            rocket = self.getRocket(flight.get("rocket"))
            electronic = self.getElectronic(flight.get("electronics"))
            deployMode = flight.get("deployMode")
            if (deployMode == "DUAL"):
                deployMode = DeployMode.DUAL
            elif (deployMode == "SINGLE"):
                deployMode = DeployMode.SINGLE
            else:
                deployMode = DeployMode.MOTOR

            date = datetime.datetime.strptime(flight.get("date"), "%m/%d/%Y")
            FDFilename = flight.get("FDFilename")
            alt = Number(flight.get("alt"), Number.Type.ALT, self.preferences, alreadyMetric=True)
            velo = Number(flight.get("velo"), Number.Type.VELO, self.preferences, alreadyMetric=True)
            accel = Number(flight.get("accel"), Number.Type.ACCEL, self.preferences, alreadyMetric=True)
            success = flight.get("success")
            notes = flight.get("notes")

            self.flights.append(
                Flight(motor, rocket, electronic, deployMode, date, FDFilename, alt, velo, accel, success, notes))

        self.refreshAll()

    def readJSON(self, filename):
        with open(filename, "r") as file:
            self.parseJSON(file.read())

        self.URHandler.addState()

    '''
    File management
    '''
    def new(self):
        filename = tkinter.filedialog.asksaveasfilename(filetypes=[("OpenLog", ".olg")], defaultextension = ".olg")
        if (filename == ""):
            return
        self.preferences.logFile = filename
        self.preferences.saveJSON()
        self.clear()
        self.URHandler.reset()
        self.saveJSON()
        self.refreshAll()
        window.title('OpenLog (' + preferences.logFile.split('/')[-1] + ')')

    def open(self):
        filename = tkinter.filedialog.askopenfilename(filetypes=[("OpenLog", ".olg"), ("JSON", ".json")], defaultextension = ".olg")
        if (filename == ""):
            return
        self.preferences.logFile = filename
        self.URHandler.reset()
        self.readJSON(filename)
        self.preferences.saveJSON()
        self.refreshAll()
        window.title('OpenLog (' + preferences.logFile.split('/')[-1] + ')')

    def saveAs(self):
        filename = tkinter.filedialog.asksaveasfilename(filetypes=[("OpenLog", ".olg"), ("JSON", ".json")], defaultextension = ".olg")
        if (filename == ""):
            return
        self.preferences.logFile = filename
        self.preferences.saveJSON()
        self.saveJSON()
        window.title('OpenLog (' + preferences.logFile.split('/')[-1] + ')')

    def rename(self):
        filename = tkinter.filedialog.asksaveasfilename(filetypes=[("OpenLog", ".olg"), ("JSON", ".json")],
                                                        defaultextension=".olg")
        if (filename == ""):
            return
        os.rename(self.preferences.logFile, filename)
        self.preferences.logFile = filename
        self.preferences.saveJSON()
        self.saveJSON()
        window.title('OpenLog (' + preferences.logFile.split('/')[-1] + ')')

    def importFile(self):
        filename = tkinter.filedialog.askopenfilename(filetypes=[("OpenLog", ".olg"), ("JSON", ".json")], defaultextension = ".olg")
        if (filename == ""):
            return
        if (filename.endswith(".json") or filename.endswith(".olg")):
            self.readJSON(filename)

    def importMotor(self):
        filename = tkinter.filedialog.askopenfilename(filetypes=[("RASP", ".eng"), ("Rocksim", ".rse")])
        motorFileIndex = 0
        motorSuffix = "." +filename.split(".")[-1]
        filenameText = filename.split("/")[-1].removesuffix(motorSuffix)
        motorFilename = "data/motors/" + filenameText + motorSuffix
        while (os.path.exists(motorFilename)):
            motorFileIndex += 1
            motorFilename = "data/motors/" + filenameText + " (" +  str(motorFileIndex) + ")" + motorSuffix

        shutil.copy(filename, motorFilename)

        motors = MotorReader.readMotors("data/motors/")

        self.motors = motors

        self.refreshAll()

    def cleanFlightDataFiles(self):
        warning = messagebox.askokcancel("Warning!", "WARNING! This will damage flight data file references in other logs!")
        if (not warning):
            return

        # find used filenames and their corresponding flight
        usedFiles = []
        flights = []
        for flight in self.flights:
            if (flight.FDFilename != ""):
                usedFiles.append(flight.FDFilename.split("/")[-1])
                flights.append(flight)

        # remove unused files
        for file in os.listdir("data/flightData/"):
            if (file not in usedFiles):
                os.remove("data/flightData/" + file)

        # rename files
        for flight in zip(flights, usedFiles):
            index = 0
            newName = "data/flightData/" + str(index) + "." + flight[1].split(".")[-1]
            while(os.path.exists(newName)):
                if (newName == "data/flightData/" + flight[1]):
                    break
                index += 1
                newName = "data/flightData/" + str(index) + "." + flight[1].split(".")[-1]



            if (newName != "data/flightData/" + flight[1]):
                os.rename("data/flightData/" + flight[1],newName)
                flight[0].FDFilename =  newName

        self.saveJSON()

    def cleanPicturesFiles(self):
        warning = messagebox.askokcancel("Warning!",
                                         "WARNING! This will damage photo references in other logs!")
        if (not warning):
            return

        # find used filenames and their corresponding flight
        usedFiles = []
        rockets = []
        for rocket in self.rockets:
            if (rocket.picture != ""):
                usedFiles.append(rocket.picture.split("/")[-1])
                rockets.append(rocket)

        # remove unused files
        for file in os.listdir("data/rocketPictures/"):
            if (file not in usedFiles):
                os.remove("data/rocketPictures/" + file)

        # rename files
        for rocket in zip(rockets, usedFiles):
            index = 0
            newName = "data/rocketPictures/" + str(index) + "." + rocket[1].split(".")[-1]
            while (os.path.exists(newName)):
                if (newName == "data/rocketPictures/" + rocket[1]):
                    break
                index += 1
                newName = "data/rocketPictures/" + str(index) + "." + rocket[1].split(".")[-1]

            if (newName != "data/rocketPictures/" + rocket[1]):
                os.rename("data/rocketPictures/" + rocket[1], newName)
                rocket[0].picture = newName

        self.saveJSON()
    '''
    Tkinter Keybind Command handling
    '''

    def handleCopy(self, event):
        self.copy()

    def handlePaste(self, event):
        self.paste()

    def handleCut(self, event):
        self.cut()

    def handleDelete(self, event):
        self.delete()

    def handleCreate(self, event):
        if (tabControl.index("current") == 0):
            self.logManagementWindow.openCreatePopup()
        elif (tabControl.index("current") == 1):
            self.rocketManagementWindow.openCreatePopup()
        elif (tabControl.index("current") == 2):
            self.electronicManagamentWindow.openCreatePopup()

    def handleUpdate(self, event):
        if (tabControl.index("current") == 0):
            self.logManagementWindow.openUpdatePopup()
        elif (tabControl.index("current") == 1):
            self.rocketManagementWindow.openUpdatePopup()
        elif (tabControl.index("current") == 2):
            self.electronicManagamentWindow.openUpdatePopup()
    '''
    Export tools 
    '''

    class Exporter:
        def __init__(self, log):
            self.log = log

        def export(self):
            # format = self.formatComboBox.get()
            filename = tkinter.filedialog.asksaveasfilename(filetypes=[("CSV", ".csv"), ("JSON", ".json"), ("OpenLog", ".olg")], defaultextension = ".csv")
            if (filename == ""):
                return

            if (filename.endswith(".csv")):
                self.exportCSV(filename)
            elif (filename.endswith(".json") or filename.endswith(".olg")):
                self.exportJSON(filename)
            else:
                return

            messagebox.showinfo("OpenLog", "Exported successfully")

        def exportCSV(self, filename):
            csv = "Date, Rocket, Diameter (" + self.log.preferences.rocketDimensionUnit + "), Motor, Total Impulse, Electronics, Deployment, Apogee (" + self.log.preferences.altitudeUnit + "), Max Velocity (" + self.log.preferences.velocityUnit + "), Acceleration (" + self.log.preferences.accelerationUnit + "), Success, Notes\n"

            flights = sorted(self.log.flights, key=lambda flight: flight.date)

            for flight in flights:
                csv += flight.getCSV()


            with open(filename, "w") as CSVFile:
                CSVFile.write(csv)

        def exportJSON(self, filename):
            with open(filename, "w") as JSONFile:
                JSONFile.write(self.log.getJSON())

class Preferences():

    theme = "Dark"
    altitudeUnit = "ft"
    velocityUnit = "ft/s"
    accelerationUnit = "G's"
    rocketDimensionUnit = "in"
    motorLengthUnit = "mm"
    motorMassUnit = "kg"
    thrustUnit = "N"
    logFile = ""


    def __init__(self):
        self.readJSON()
        self.updateTheme()


    def readJSON(self):
        with open("data/preferences.json", "r") as file:
            data = json.load(file)


        self.altitudeUnit = data.get("altitudeUnit")
        self.velocityUnit = data.get("velocityUnit")
        self.accelerationUnit = data.get("accelerationUnit")
        self.rocketDimensionUnit = data.get("rocketDimensionUnit")
        self.motorLengthUnit = data.get("motorLengthUnit")
        self.motorMassUnit = data.get("motorMassUnit")
        self.thrustUnit = data.get("thrustUnit")
        self.logFile = data.get("logFile")

    def saveJSON(self):
        with open("data/preferences.json", "w") as file:
            file.write(self.getJSON())

    def openPopup(self):
        preferencesPopup = Popup(window, title="Preferences")

        settingsFrame = Frame(preferencesPopup)

        # visuals settings
        # visualsLabel =  Label(settingsFrame, text="Visuals: ")
        # visualsLabel.pack()
        visualsFrame = LabelFrame(settingsFrame, text="Visuals")
        themeLabel = Label(visualsFrame, text="Theme: ")
        self.themeComboBox = Combobox(visualsFrame, values=["Light", "Dark"], state="readonly")
        self.themeComboBox.set(self.theme)

        themeLabel.grid(column=0, row=0, padx=5, pady=5)
        self.themeComboBox.grid(column=1, row=0, padx=5, pady=5)

        visualsFrame.pack(expand=True, fill="x")

        # unit settings
        # unitsLabel = Label(settingsFrame, text="Units: ")
        # unitsLabel.pack()

        unitsFrame = LabelFrame(settingsFrame, text="Units")

        altitudeLabel = Label(unitsFrame, text="Altitude: ")
        self.altitudeComboBox = Combobox(unitsFrame, values=["ft", "m", "miles", "kilometers"], state="readonly")
        self.altitudeComboBox.set(self.altitudeUnit)

        velocityLabel = Label(unitsFrame, text="Velocity: ")
        self.velocityComboBox = Combobox(unitsFrame, values=["ft/s", "m/s", "mph", "kph", "mach"], state="readonly")
        self.velocityComboBox.set(self.velocityUnit)

        accelerationLabel = Label(unitsFrame, text="Acceleration: ")
        self.accelerationComboBox = Combobox(unitsFrame, values=["G's", "ft/s^2", "m/s^2"], state="readonly")
        self.accelerationComboBox.set(self.accelerationUnit)

        rocketDimensionsLabel = Label(unitsFrame, text="Rocket Dimensions: ")
        self.rocketDiameterComboBox = Combobox(unitsFrame, values=["in", "ft", "m", "cm", "mm"], state="readonly")
        self.rocketDiameterComboBox.set(self.rocketDimensionUnit)

        motorLengthLabel = Label(unitsFrame, text="Motor Length: ")
        self.motorLengthComboBox = Combobox(unitsFrame, values=["in", "ft", "m", "cm", "mm"], state="readonly")
        self.motorLengthComboBox.set(self.motorLengthUnit)

        motorMassLabel = Label(unitsFrame, text="Motor Mass: ")
        self.motorMassComboBox = Combobox(unitsFrame, values=["lbs", "kg", "g"], state="readonly")
        self.motorMassComboBox.set(self.motorMassUnit)

        thrustUnitLabel = Label(unitsFrame, text="Thrust Unit: ")
        self.thrustUnitComboBox = Combobox(unitsFrame, values=["N", "lbf"], state="readonly")
        self.thrustUnitComboBox.set(self.thrustUnit)


        altitudeLabel.grid(column=0, row=0, padx=5, pady=5)
        self.altitudeComboBox.grid(column=1, row=0, padx=5, pady=5)
        velocityLabel.grid(column=0, row=1, padx=5, pady=5)
        self.velocityComboBox.grid(column=1, row=1, padx=5, pady=5)
        accelerationLabel.grid(column=0, row=2, padx=5, pady=5)
        self.accelerationComboBox.grid(column=1, row=2, padx=5, pady=5)
        rocketDimensionsLabel.grid(column=0, row=3, padx=5, pady=5)
        self.rocketDiameterComboBox.grid(column=1, row=3, padx=5, pady=5)
        motorLengthLabel.grid(column=0, row=4, padx=5, pady=5)
        self.motorLengthComboBox.grid(column=1, row=4, padx=5, pady=5)
        motorMassLabel.grid(column=0, row=5, padx=5, pady=5)
        self.motorMassComboBox.grid(column=1, row=5, padx=5, pady=5)
        thrustUnitLabel.grid(column=0, row=6, padx=5, pady=5)
        self.thrustUnitComboBox.grid(column=1, row=6, padx=5, pady=5)

        unitsFrame.pack(expand=True, fill="x")



        settingsFrame.pack()
        applyFrame = Frame(settingsFrame)
        cancelButton = Button(applyFrame, text="Cancel", command=preferencesPopup.destroy)
        applyButton = Button(applyFrame, text="Apply", command=self.update)
        applyAndCloseButton = Button(applyFrame, text="Save and Close", command=lambda: [f() for f in [self.update, preferencesPopup.destroy]])

        cancelButton.grid(row=0, column=0, padx=5, pady=5)
        applyButton.grid(row=0, column=1, padx=5, pady=5)
        applyAndCloseButton.grid(row=0, column=2, padx=5, pady=5)


        applyFrame.pack(expand=True, fill="x")


    def update(self):
        self.theme = self.themeComboBox.get()

        self.updateTheme()

        self.altitudeUnit = self.altitudeComboBox.get()
        self.velocityUnit = self.velocityComboBox.get()
        self.accelerationUnit = self.accelerationComboBox.get()
        self.rocketDimensionUnit = self.rocketDiameterComboBox.get()
        self.motorLengthUnit = self.motorLengthComboBox.get()
        self.motorMassUnit = self.motorMassComboBox.get()
        self.thrustUnit = self.thrustUnitComboBox.get()

        log.refreshAll()
        log.saveJSON()
        self.saveJSON()

    def updateTheme(self):
        # pywinstyles.apply_style(window, "optimised")
        sv_ttk.set_theme(self.theme.lower())


    def getJSON(self):
        JSON = "{\n"
        JSON += "\"theme\": \"" + self.theme + "\",\n"
        JSON += "\"altitudeUnit\": \"" + self.altitudeUnit + "\",\n"
        JSON += "\"velocityUnit\": \"" + self.velocityUnit + "\",\n"
        JSON += "\"accelerationUnit\": \"" + self.accelerationUnit + "\",\n"
        JSON += "\"rocketDimensionUnit\": \"" + self.rocketDimensionUnit + "\",\n"
        JSON += "\"motorLengthUnit\": \"" + self.motorLengthUnit + "\",\n"
        JSON += "\"motorMassUnit\": \"" + self.motorMassUnit + "\",\n"
        JSON += "\"thrustUnit\": \"" + self.thrustUnit + "\",\n"
        JSON += "\"logFile\": \"" + self.logFile + "\"\n"
        JSON += "}\n"

        return(JSON)

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False
        if (self.theme != other.theme):
            return(False)
        if (self.altitudeUnit != other.altitudeUnit):
            return(False)
        if (self.velocityUnit != other.velocityUnit):
            return(False)
        if (self.accelerationUnit != other.accelerationUnit):
            return(False)
        if (self.rocketDimensionUnit != other.rocketDimensionUnit):
            return(False)
        if (self.motorLengthUnit != other.motorLengthUnit):
            return(False)
        if (self.motorMassUnit != other.motorMassUnit):
            return(False)
        if (self.thrustUnit != other.thrustUnit):
            return(False)
        if (self.logFile != other.logFile):
            return(False)
        return(True)

    def __ne__(self, other):
        return(not self.__eq__(other))

'''
A number class that supports units. Stores everything on the backend in standard metric.
'''
class Number():
    class Type(Enum):
        ALT = 0
        VELO = 1
        ACCEL = 2
        RKTDIM = 3
        MOTORLEN = 4
        MOTORMASS = 5
        THRUST = 6


    value = 0
    type = None
    def __init__(self, value, type, preferences, alreadyMetric = False):
        self.type = type
        self.preferences = preferences
        if (alreadyMetric):
            self.value = value
        else:
            self.setValue(value)


    def setValue(self, value):
        if (self.type == Number.Type.ALT):
            if (self.preferences.altitudeUnit == "ft"):
                self.value = value/3.2808
            elif (self.preferences.altitudeUnit == "m"):
                self.value = value
            elif (self.preferences.altitudeUnit == "miles"):
                self.value = value*1609.34
            elif (self.preferences.altitudeUnit == "kilometers"):
                self.value = value*1000
        elif (self.type == Number.Type.VELO):
            if (self.preferences.velocityUnit == "ft/s"):
                self.value = value / 3.2808
            elif (self.preferences.velocityUnit == "m/s"):
                self.value = value
            elif (self.preferences.velocityUnit == "mph"):
                self.value = value*0.447
            elif (self.preferences.velocityUnit == "kph"):
                self.value = value/3.6
            elif (self.preferences.velocityUnit == "mach"):
                self.value = value*340.29
        elif (self.type == Number.Type.ACCEL):
            if (self.preferences.accelerationUnit == "G's"):
                self.value = value * 9.81
            elif (self.preferences.accelerationUnit == "ft/s^2"):
                self.value = value*0.3048
            elif (self.preferences.accelerationUnit == "m/s^2"):
                self.value = value
        elif (self.type == Number.Type.RKTDIM):
            if (self.preferences.rocketDimensionUnit == "in"):
                self.value = value*0.0254
            elif (self.preferences.rocketDimensionUnit == "ft"):
                self.value = value/3.2808
            elif (self.preferences.rocketDimensionUnit == "m"):
                self.value = value
            elif (self.preferences.rocketDimensionUnit == "cm"):
                self.value = value/100
            elif (self.preferences.rocketDimensionUnit == "mm"):
                self.value = value/1000
        elif (self.type == Number.Type.MOTORLEN):
            if (self.preferences.motorLengthUnit == "in"):
                self.value = value*0.0254
            elif (self.preferences.motorLengthUnit == "ft"):
                self.value = value/3.2808
            elif (self.preferences.motorLengthUnit == "m"):
                self.value = value
            elif (self.preferences.motorLengthUnit == "cm"):
                self.value = value/100
            elif (self.preferences.motorLengthUnit == "mm"):
                self.value = value/1000
        elif (self.type == Number.Type.MOTORMASS):
            if (self.preferences.motorMassUnit == "lbs"):
                self.value = value * 0.4536
            elif (self.preferences.motorMassUnit == "kg"):
                self.value = value
            elif (self.preferences.motorMassUnit == "g"):
                self.value = value/1000
        elif (self.type == Number.Type.THRUST):
            if (self.preferences.thrustUnit == "N"):
                self.value = value
            if (self.preferences.thrustUnit == "lbf"):
                self.value = value * 4.4482

    def getValue(self):
        if (self.type == Number.Type.ALT):
            if (self.preferences.altitudeUnit == "ft"):
                return(round(self.value*3.2808))
            elif (self.preferences.altitudeUnit == "m"):
                return(round(self.value))
            elif (self.preferences.altitudeUnit == "miles"):
                return(round(self.value/1609.34, 2))
            elif (self.preferences.altitudeUnit == "kilometers"):
                return(round(self.value/1000, 2))
        elif (self.type == Number.Type.VELO):
            if (self.preferences.velocityUnit == "ft/s"):
                return(round(self.value * 3.2808))
            elif (self.preferences.velocityUnit == "m/s"):
                return(round(self.value,1))
            elif (self.preferences.velocityUnit == "mph"):
                return(round(self.value/0.447))
            elif (self.preferences.velocityUnit == "kph"):
                return(round(self.value*3.6))
            elif (self.preferences.velocityUnit == "mach"):
                return(round(self.value/340.29,2))
        elif (self.type == Number.Type.ACCEL):
            if (self.preferences.accelerationUnit == "G's"):
                return(round(self.value / 9.81,1))
            elif (self.preferences.accelerationUnit == "ft/s^2"):
                return(round(self.value/0.3048))
            elif (self.preferences.accelerationUnit == "m/s^2"):
                return(round(self.value))
        elif (self.type == Number.Type.RKTDIM):
            if (self.preferences.rocketDimensionUnit == "in"):
                return(round(self.value/0.0254,1))
            elif (self.preferences.rocketDimensionUnit == "ft"):
                return(round(self.value*3.2808,3))
            elif (self.preferences.rocketDimensionUnit == "m"):
                return(round(self.value,3))
            elif (self.preferences.rocketDimensionUnit == "cm"):
                return(round(self.value*100,1))
            elif (self.preferences.rocketDimensionUnit == "mm"):
                return(round(self.value*1000))
        elif (self.type == Number.Type.MOTORLEN):
            if (self.preferences.motorLengthUnit == "in"):
                return(round(self.value/0.0254,1))
            elif (self.preferences.motorLengthUnit == "ft"):
                return(round(self.value*3.2808,3))
            elif (self.preferences.motorLengthUnit == "m"):
                return(round(self.value,3))
            elif (self.preferences.motorLengthUnit == "cm"):
                return(round(self.value*100,1))
            elif (self.preferences.motorLengthUnit == "mm"):
                return(round(self.value*1000))
        elif (self.type == Number.Type.MOTORMASS):
            if (self.preferences.motorMassUnit == "lbs"):
                return(round(self.value/0.4536,2))
            elif (self.preferences.motorMassUnit == "kg"):
                return(round(self.value,3))
            elif (self.preferences.motorMassUnit == "g"):
                return(round(self.value*1000))
        elif (self.type == Number.Type.THRUST):
            if (self.preferences.thrustUnit == "N"):
                return(round(self.value))
            if (self.preferences.thrustUnit == "lbf"):
                return(round(self.value * 4.4482))

        return(0)

    def __float__(self):
        return(float(self.getValue()))

    def __int__(self):
        return(int(self.getValue()))

    def __lt__(self, other):
        if (other == None):
            return False
        return (float(self) <= float(other))

    def __gt__(self, other):
        if (other == None):
            return False
        return (float(self) > float(other))

    def __le__(self, other):
        if (other == None):
            return False
        return (float(self) <= float(other))

    def __ge__(self, other):
        if (other == None):
            return False
        return (float(self) >= float(other))

    def __eq__(self, other):
        if (other == None):
            return False
        return (float(self) == float(other))

    def __ne__(self, other):
        return (not self.__eq__(other))

    def __add__(self, other):
        if (not isinstance(other, Number)):
            newNumber = Number(self.value + other, self.type, self.preferences, alreadyMetric=True)
            return newNumber
        if (self.type == other.type):
            newNumber = Number(self.value + other.value, self.type, self.preferences, alreadyMetric=True)
            return newNumber
        raise Exception("Types " + self.type.name + " and " + other.type.name + " do not match")

    def __sub__(self, other):
        return (self.__add__(-other))

    def __mul__(self, other):
        if (not isinstance(other, Number)):
            newNumber = Number(self.value * other, self.type, self.preferences, alreadyMetric=True)
            return newNumber
        if (self.type == other.type):
            newNumber = Number(self.value * other.value, self.type, self.preferences, alreadyMetric=True)
            return newNumber
        raise Exception("Types " + self.type.name + " and " + other.type.name + " do not match")

    def __truediv__(self, other):
        if (not isinstance(other, Number)):
            newNumber = Number(self.value / other, self.type, self.preferences, alreadyMetric=True)
            return newNumber
        if (self.type == other.type):
            newNumber = Number(self.value / other.value, self.type, self.preferences, alreadyMetric=True)
            return newNumber
        raise Exception("Types " + self.type.name + " and " + other.type.name + " do not match")

    def __neg__(self):
        newNumber = Number(-self.value, self.type, self.preferences, alreadyMetric=True)
        return(newNumber)

    def __pos__(self):
        newNumber = Number(self.value, self.type, self.preferences, alreadyMetric=True)
        return (newNumber)

    def __abs__(self):
        newNumber = Number(abs(self.value), self.type, self.preferences, alreadyMetric=True)
        return(newNumber)

    def __str__(self):
        if (self.type == Number.Type.ALT):
            return(str(self.getValue()) + " " + self.preferences.altitudeUnit)
        elif (self.type == Number.Type.VELO):
            return(str(self.getValue()) + " " + self.preferences.velocityUnit)
        elif (self.type == Number.Type.ACCEL):
            return(str(self.getValue()) + " " + self.preferences.accelerationUnit)
        elif (self.type == Number.Type.RKTDIM):
            return(str(self.getValue()) + " " + self.preferences.rocketDimensionUnit)
        elif (self.type == Number.Type.MOTORLEN):
            return(str(self.getValue()) + " " + self.preferences.motorLengthUnit)
        elif (self.type == Number.Type.MOTORMASS):
            return(str(self.getValue()) + " " + self.preferences.motorMassUnit)
        return("")

class SearchableMenubar:
    class Command:
        def __init__(self, master, label, command, description = ""):
            self.master = master
            self.label = label
            self.command = command
            self.description = description

        def __repr__(self):
            return(str(self))

        def __str__(self):
            return(str(self.master) + ">" + self.label)

    def __init__(self, root, name = "", tearoff = False):
        if (isinstance(root, SearchableMenubar)):
            self.menu = Menu(root.menu, tearoff=tearoff)
        else:
            self.menu = Menu(root, tearoff=tearoff)

        self.root = root
        self.name = name
        self.cascades = []
        self.commands = []
        self.popup = None

    '''
    Creating Menubar functions
    '''

    def add_command(self, label = "", command = None, description = ""):
        self.commands.append(SearchableMenubar.Command(self, label, command, description=description))
        self.menu.add_command(label = label, command = command)

    def add_cascade(self, menu, label):
        self.menu.add_cascade(menu = menu.menu, label = label)
        menu.name = label

        self.cascades.append(menu)

    def add_separator(self):
        self.menu.add_separator()

    '''
    Searching the menubar functions
    '''

    def search(self, term):
        term = term.lower()
        matches = []
        for command in self.commands:
            if (term in command.label.lower()):
                matches.append(command)

        for cascade in self.cascades:
            matches.extend(cascade.search(term))

        return(matches)

    def getCommand(self, label, deep = False):
        if (not deep):
            for command in self.commands:
                if (command.label == label):
                    return(command)
        else:
            for cascade in self.cascades:
                command = cascade.getCommand(label, True)
                if (command != None):
                    return(command)

            return(self.getCommand(label))
        return(None)

    def getAllCommands(self):
        commands = self.commands
        for cascade in self.cascades:
            commands.extend(cascade.getAllCommands())

        return(commands)

    def getCascade(self, name):
        for menu in self.cascades:
            if (menu.name == name):
                return (menu)

        return (None)

    def openSearchPopup(self):
        if (isinstance(self.popup, Popup) and self.popup.children != {}):
            return
        self.popup = Popup(self.root, title="Search")

        self.searchBar = Entry(self.popup, width = 50)
        self.searchBar.pack(fill=BOTH, expand=True)
        self.searchBar.focus_set()
        self.searchBar.bind("<KeyRelease>", self.updateSearch)

        self.resultList = Listbox(self.popup, selectmode=SINGLE)
        self.resultList.pack(fill=BOTH, expand=True)
        self.resultList.bind("<Button-3>", self.runAction)
        self.resultList.bind("<Return>", self.runAction)

    def updateSearch(self, event):
        self.resultList.delete(0, END)
        if (self.searchBar.get() == ""):

            return
        results = self.search(self.searchBar.get())

        for result in results:
            self.resultList.insert('end', str(result))

    def runAction(self, event = None):
        selection = self.resultList.get(self.resultList.nearest(event.y)) # A little scuffed, will select the lowest if you click below all of them
        chain = selection.split(">")


        menu = self
        if (len(chain) > 1):
            for item in chain[:-1]:
                menu = menu.getCascade(item)


        command = menu.getCommand(chain[-1])

        if (command != None):
            command.command()
        else:
            raise Exception("Error finding action")

    def __str__(self):
        if (isinstance(self.root, SearchableMenubar)):
            parentStr = str(self.root)
            if (parentStr != ""):
                return(parentStr + ">" + self.name)
        return(self.name)

    def __repr__(self):
        return(str(self))

windowClosed = False
def closeWindow():
    global windowClosed
    if (log.preferences.logFile == ""):
        message = "Do you want to quit? There is no save file set."
        if (messagebox.askokcancel("Quit", message)):
            windowClosed = True
            window.destroy()
    else:
        windowClosed = True
        window.destroy()

class Help:
    def __init__(self, root):
        self.root = root
        pass
    '''
    Help menu and command descriptions
    '''

    def openHelpMenu(self):
        popup = Popup(self.root, title="Help")

        self.helpList = Listbox(popup, selectmode=SINGLE)
        self.helpList.pack(fill=BOTH, expand=True, side=LEFT)
        self.helpList.bind("<<ListboxSelect>>", self.updateHelpText)
        # scuffed using a command for this, but it makes implementation easier
        with open("data/helpDescriptions.json") as descriptionsJSON:
            helpData = json.load(descriptionsJSON).get("Descriptions")

        self.helpContents = []
        for item in helpData:
            self.helpContents.append(item)
            self.helpList.insert('end', item.get("Name"))

        self.helpText = Text(popup, state="disabled", wrap=WORD)
        self.helpText.pack(fill=BOTH, expand=True, side=LEFT)

    def updateHelpText(self, event):
        if (len(self.helpList.curselection()) == 0):
            return
        helpItem = self.helpContents[self.helpList.curselection()[0]]

        if (helpItem == None):
            return
        self.helpText["state"] = "normal"
        self.helpText.delete("1.0", END)
        self.helpText.insert("1.0", helpItem.get("Description"))
        self.helpText["state"] = "disabled"

    '''
    About window
    '''
    def about(self):
        popup = Popup(self.root, title="About")

        aboutText = Text(popup, state="normal", wrap=WORD)
        aboutText.pack(fill=BOTH, expand=True)
        aboutText.insert("1.0", "OpenLog is a logging app for rocketry, and allows for free, easy, and accurate logging of flights. "
                                "OpenLog is currently in Beta and is regularly receiving updates with new features and bug fixes. "
                                "If you do find a bug make sure to report it using the action Help>Report Bug in the menubar. "
                                "Thank you for your support and I hope that OpenLog serves as a useful tool in your rocketry journey. "
                                "Also a special shout out to my mom, Dr. Tammy VanDeGrift for inspiring me to program, and for all the people in OROC that have been so helpful in my rocketry journey.")
        aboutText["state"] = "disabled"

        versionTag = Label(popup, text="OpenLog Version " + version)
        versionTag.pack(side=RIGHT)

    '''
    Get Started Window
    '''
    def getStarted(self):
        popup = Popup(self.root, title="Get Started")

        self.GSPages = Listbox(popup, selectmode=SINGLE)
        self.GSPages.pack(fill=BOTH, expand=True, side=LEFT)
        self.GSPages.bind("<<ListboxSelect>>", self.updateGSText)

        with open("data/getStarted.json") as descriptionsJSON:
            helpData = json.load(descriptionsJSON).get("Pages")

        self.GSContents = []
        for item in helpData:
            self.GSContents.append(item)
            self.GSPages.insert('end', item.get("Name"))

        self.GSText = Text(popup, state="disabled", wrap=WORD)
        self.GSText.pack(fill=BOTH, expand=True, side=LEFT)

    def updateGSText(self, event):
        if (len(self.GSPages.curselection()) == 0):
            return
        page = self.GSContents[self.GSPages.curselection()[0]]

        if (page == None):
            return
        self.GSText["state"] = "normal"
        self.GSText.delete("1.0", END)
        self.GSText.insert("1.0", page.get("Text"))
        self.GSText["state"] = "disabled"

    '''
    Support and bug report
    '''
    def contactSupport(self):
        popup = Popup(self.root, title="Contact Support")

        self.supportText = Text(popup, state="normal", wrap=WORD)
        self.supportText.pack(fill=BOTH, expand=True)

        sendButton = Button(popup, text="Send", command=lambda: [f() for f in [self.sendSupportEmail, popup.destroy]])
        sendButton.pack()

    def sendSupportEmail(self):
        emailer.sendSupportEmail(self.supportText.get("1.0", END))

    def reportBug(self):
        popup = Popup(self.root, title="Report Bug")

        self.bugText = Text(popup, state="normal", wrap=WORD)
        self.bugText.pack(fill=BOTH, expand=True)

        sendButton = Button(popup, text="Send", command=lambda: [f() for f in [self.sendBugReport, popup.destroy]])
        sendButton.pack()

    def sendBugReport(self):
        emailer.sendBugReport(self.bugText.get("1.0", END), log)
'''
Tkinter GUI code
'''

'''
Main application establishment
'''

window = tk.Tk()
window.iconbitmap("data/icon.ico")
window.protocol("WM_DELETE_WINDOW", closeWindow)


# preferences object
preferences = Preferences()
if (preferences.logFile != ""):
    window.title('OpenLog (' + preferences.logFile.split('/')[-1] + ')')
else:
    window.title('OpenLog (No File Selected)')

# log logic object
log = Log(preferences)

'''
Set key binds and commands
'''
window.bind("<Escape>", lambda event: closeWindow())
window.bind("<Control-z>", log.URHandler.handleUndo)
window.bind("<Control-y>", log.URHandler.handleRedo)
window.bind("<Control-c>", log.handleCopy)
window.bind("<Control-v>", log.handlePaste)
window.bind("<Control-x>", log.handleCut)
window.bind("<Delete>", log.handleDelete)
window.bind("<Control-Alt-c>", log.handleCreate)
window.bind("<Control-Alt-u>", log.handleUpdate)
window.bind("<Control-d>", lambda event: log.openDataViewer())
window.bind("<Control-f>", lambda event: log.getFlights())


'''
Menu bar
'''
menubar = SearchableMenubar(window)
window['menu'] = menubar.menu
menuFile = SearchableMenubar(menubar, tearoff=0)
menuEdit = SearchableMenubar(menubar, tearoff=0)
menuCreate = SearchableMenubar(menubar, tearoff=0)
menuView = SearchableMenubar(menubar, tearoff=0)
menuHelp = SearchableMenubar(menubar, tearoff=0)
menubar.add_cascade(menu=menuFile, label='File')
menubar.add_cascade(menu=menuEdit, label='Edit')
menubar.add_cascade(menu=menuCreate, label='Create')
menubar.add_cascade(menu=menuView, label='View')
menubar.add_cascade(menu=menuHelp, label='Help')


# file actions
menuFile.add_command(label="New", command=log.new)
menuFile.add_command(label="Open", command=log.open)
menuFile.add_command(label="Save As", command=log.saveAs)
menuFile.add_command(label="Rename", command=log.rename)

menuFile.add_separator()
menuFile.add_command(label="Export", command=log.exporter.export)
menuFile.add_command(label="Import", command=log.importFile)
menuFile.add_separator()
menuFile.add_command(label="Import Motor", command=log.importMotor)
menuFile.add_command(label="Clean Flight Data Folder", command=log.cleanFlightDataFiles)
menuFile.add_command(label="Clean Rocket Pictures Folder", command=log.cleanPicturesFiles)
menuFile.add_separator()
menuFile.add_command(label="Quit", command=closeWindow)

# Edit Actions
menuUpdate = SearchableMenubar(menuEdit, tearoff=0)
menuUpdate.add_command(label="Update Log", command=log.logManagementWindow.openUpdatePopup)
menuUpdate.add_command(label="Update Rocket", command=log.rocketManagementWindow.openUpdatePopup)
menuUpdate.add_command(label="Update Electronic", command=log.electronicManagamentWindow.openUpdatePopup)
menuEdit.add_cascade(menu=menuUpdate, label="Update")
menuFDF = SearchableMenubar(menuEdit, tearoff=0)
menuFDF.add_command(label="Add Flight Data File", command=log.logManagementWindow.addFDFile)
menuFDF.add_command(label="Remove Flight Data File", command=log.logManagementWindow.removeFDFile)
menuEdit.add_cascade(menu=menuFDF, label="Flight Data File")
menuEdit.add_separator()
menuEdit.add_command(label="Copy", command=log.copy)
menuEdit.add_command(label="Paste", command=log.paste)
menuEdit.add_command(label="Cut", command=log.cut)
menuEdit.add_separator()
menuEdit.add_command(label="Undo", command=log.URHandler.undo)
menuEdit.add_command(label="Redo", command=log.URHandler.redo)
menuEdit.add_separator()
menuEdit.add_command(label="Delete", command=log.delete)

menuEdit.add_separator()
menuEdit.add_command(label="Preferences", command=preferences.openPopup)

# Create actions
menuCreate.add_command(label="Log", command=log.logManagementWindow.openCreatePopup)
menuCreate.add_command(label="Rocket", command=log.rocketManagementWindow.openCreatePopup)
menuCreate.add_command(label="Electronic", command=log.electronicManagamentWindow.openCreatePopup)

# View actions
menuView.add_command(label="Data Window", command=log.openDataViewer)
menuView.add_command(label="View Flights", command=log.getFlights)

# Help actions
helper = Help(window)
menuHelp.add_command(label="Find Action", command=menubar.openSearchPopup)
menuHelp.add_separator()
menuHelp.add_command(label="Help", command=helper.openHelpMenu)
menuHelp.add_command(label="About", command=helper.about)
menuHelp.add_separator()
menuHelp.add_command(label="Getting Started", command=helper.getStarted)
menuHelp.add_separator()
menuHelp.add_command(label="Contact Support", command=helper.contactSupport)
menuHelp.add_command(label="Report Bug", command=helper.reportBug)
menuHelp.add_separator()
menuHelp.add_command(label="Check for Updates")

# tab creation
tabControl = Notebook(window)

logTab = Frame(tabControl)
rocketTab = Frame(tabControl)
electronicsTab = Frame(tabControl)
motorsTab = Frame(tabControl)
statsTab = Frame(tabControl)

tabControl.add(logTab, text='Log')
tabControl.add(rocketTab, text='Rockets')
tabControl.add(electronicsTab, text='Electronics')
tabControl.add(motorsTab, text='Motors')
tabControl.add(statsTab, text='Statistics')
tabControl.pack(expand = 1, fill ="both")

'''
Log tab
'''
# log viewing
logFrame = Frame(logTab)
logListFrame = Frame(logFrame)

logSearchFrame = LabelFrame(logListFrame, text="Search")
logSearchBar = Entry(logSearchFrame)
logSearchBar.pack(fill ="x")
logSearchBar.bind("<KeyRelease>", log.dynamicLogListUpdate)
logSearchFrame.pack(fill ="x")

#sorting
logShowSortFilterButton = Button(logListFrame, text="Show Sort and Filter", command=log.showLogSortingAndFilters)
logShowSortFilterButton.pack(fill = "both")
logSortingFrame = Frame(logListFrame)
logSortingLabel = Label(logSortingFrame, text="Sort by: ")
logSortingOptions = Combobox(logSortingFrame, values=["Chronological", "Altitude", "Velocity", "Acceleration"], state="readonly")
logSortingReverse = Combobox(logSortingFrame, values=["Normal", "Reverse"], state="readonly")
logSortingOptions.current(0)
logSortingReverse.current(0)
logSortingLabel.grid(row=0, column=0)
logSortingOptions.grid(row=0, column=1)
logSortingReverse.grid(row=0, column=2)

#filtering
logFilteringFrame = LabelFrame(logListFrame, text="Filter By: ")
logUsesElectronicsLabel = Label(logFilteringFrame, text="Uses Electronics: ")
logUsesElectronicsOptions = Combobox(logFilteringFrame, values=["N/A", "Yes", "No"], state="readonly")
logUsesElectronicsOptions.current(0)
logSuccessOnlyLabel = Label(logFilteringFrame, text="Successes Only: ")
logSuccessOnlyOptions = Combobox(logFilteringFrame, values=["Yes", "No"], state="readonly")
logSuccessOnlyOptions.current(1)
logMinAltLabel = Label(logFilteringFrame, text="Min Altitude: ")
logMinAltEntry = Entry(logFilteringFrame)
logMaxAltLabel = Label(logFilteringFrame, text="Max Altitude: ")
logMaxAltEntry = Entry(logFilteringFrame)
logMinVeloLabel = Label(logFilteringFrame, text="Min Velocity: ")
logMinVeloEntry = Entry(logFilteringFrame)
logMaxVeloLabel = Label(logFilteringFrame, text="Max Velocity: ")
logMaxVeloEntry = Entry(logFilteringFrame)
logMinAccelLabel = Label(logFilteringFrame, text="Min Acceleration: ")
logMinAccelEntry = Entry(logFilteringFrame)
logMaxAccelLabel = Label(logFilteringFrame, text="Max Acceleration: ")
logMaxAccelEntry = Entry(logFilteringFrame)
logMinClassLabel = Label(logFilteringFrame, text="Min Motor Class: ")
logMinClassEntry = Entry(logFilteringFrame)
logMaxClassLabel = Label(logFilteringFrame, text="Max Motor Class: ")
logMaxClassEntry = Entry(logFilteringFrame)

logUsesElectronicsLabel.grid(row=0, column=0)
logUsesElectronicsOptions.grid(row=0, column=1)
logSuccessOnlyLabel.grid(row=1, column=0)
logSuccessOnlyOptions.grid(row=1, column=1)
logMinAltLabel.grid(row=2, column=0)
logMinAltEntry.grid(row=2, column=1)
logMaxAltLabel.grid(row=3, column=0)
logMaxAltEntry.grid(row=3, column=1)
logMinVeloLabel.grid(row=4, column=0)
logMinVeloEntry.grid(row=4, column=1)
logMaxVeloLabel.grid(row=5, column=0)
logMaxVeloEntry.grid(row=5, column=1)
logMinAccelLabel.grid(row=6, column=0)
logMinAccelEntry.grid(row=6, column=1)
logMaxAccelLabel.grid(row=7, column=0)
logMaxAccelEntry.grid(row=7, column=1)
logMinClassLabel.grid(row=8, column=0)
logMinClassEntry.grid(row=8, column=1)
logMaxClassLabel.grid(row=9, column=0)
logMaxClassEntry.grid(row=9, column=1)

logSortingApplyButton = Button(logListFrame, text="Apply", command=log.updateLogList)

# log list
logList = Listbox(logListFrame, selectmode=SINGLE, width=100)
logList.pack(expand = 1, fill ="both")
logListFrame.pack(expand = 1, fill = BOTH, side=LEFT)
logDetailsFrame = Frame(logFrame)
logDetails = Text(logDetailsFrame, undo=True, state=DISABLED, wrap=WORD)
logDetails.pack(expand = 1, fill ="both")
logUpdateButton = Button(logDetailsFrame, text="Update", command=log.logManagementWindow.openUpdatePopup)
logDataViewerButton = Button(logDetailsFrame, text="View Flight Data", command=log.openDataViewer)
logDeleteButton = Button(logDetailsFrame, text="Delete", command=log.delete)
logDetailsFrame.pack(expand = 1, fill = BOTH, side=LEFT)
logFrame.pack(expand = 0, fill ="both")

# log creation frame and button
logCreateButtonFrame = Frame(logTab)
logCreateButton = Button(logCreateButtonFrame, text="Create Log", command=log.logManagementWindow.openCreatePopup)
logCreateButton.pack(fill=X)
logCreateButtonFrame.pack(expand = 1, fill ="both", side=LEFT)


'''
Rocket tab
'''
# rocket list
rocketFrame = Frame(rocketTab)
rocketListFrame = Frame(rocketFrame)
rocketList = Listbox(rocketListFrame, selectmode=SINGLE)
rocketList.pack(expand = 1, fill ="both")
rocketListFrame.pack(expand = 1, fill ="both", side=LEFT)
rocketRightFrame = Frame(rocketFrame)
rocketDetailsFrame = Frame(rocketFrame)
rocketDetails = Text(rocketDetailsFrame, state="disabled", wrap=WORD)
rocketDetails.pack(expand = 1, fill ="both", side=LEFT)

rocketImageLabel = Label(rocketDetailsFrame)
rocketButtonsFrame = Frame(rocketRightFrame)
rocketUpdateButton = Button(rocketButtonsFrame, text="Update", command=log.rocketManagementWindow.openUpdatePopup)
rocketDeleteButton = Button(rocketButtonsFrame, text="Delete", command=log.delete)
rocketButtonsFrame.pack(expand = 1, fill ="x")
rocketDetailsFrame.pack(expand = 1, fill ="both")
rocketRightFrame.pack(expand = 1, fill ="both", side=LEFT)
rocketFrame.pack(expand = 1, fill = BOTH)

# rocket creation
rocketAddFrame = Frame(rocketTab)

createRocketButton = Button(rocketAddFrame, text="Create Rocket", command=log.rocketManagementWindow.openCreatePopup)
createRocketButton.pack(fill ="x")

rocketAddFrame.pack(expand = 1, fill = BOTH)


'''
Electronics Tab
'''

# electronics list
electronicsFrame = Frame(electronicsTab)
electronicsList = Listbox(electronicsFrame, selectmode=SINGLE)
electronicsList.pack(expand = 1, fill ="both", side=LEFT)
electronicsDetailsFrame = Frame(electronicsFrame)
electronicsDetails = Text(electronicsDetailsFrame, state="disabled", wrap=WORD)
electronicsDetails.pack(expand = 1, fill ="both")
electronicsUpdateButton = Button(electronicsDetailsFrame, text="Update", command=log.electronicManagamentWindow.openUpdatePopup)
electronicsDeleteButton = Button(electronicsDetailsFrame, text="Delete", command=log.delete)
electronicsDetailsFrame.pack(expand = 1, fill ="both", side=LEFT)
electronicsFrame.pack(expand = 1, fill ="both")

# electronics creation
electronicsAddWindow = Frame(electronicsTab)

createElectronicsButton = Button(electronicsAddWindow, text="Create Electronic", command=log.electronicManagamentWindow.openCreatePopup)
createElectronicsButton.pack(fill ="x")

electronicsAddWindow.pack(expand = 1, fill = BOTH)


'''
Motor tab
'''

motorInfoFrame = Frame(motorsTab)

# motor search tools

motorSearchFrame = Frame(motorInfoFrame, relief="raised", borderwidth=5)
motorSearchLabel = Label(motorSearchFrame, text="Search:")
motorSearchBar = Entry(motorSearchFrame)
motorSearchBar.bind("<KeyRelease>", log.dynamicMotorListUpdate)
motorUsedLabel = Label(motorSearchFrame, text="Only Used Motors: ")
motorUsedSelection = Combobox(motorSearchFrame, values=["Yes", "No"], state="readonly")
motorUsedSelection.bind("<<ComboboxSelected>>", log.dynamicMotorListUpdate)
motorUsedSelection.set("No")
motorSearchLabel.grid(row=0, column=0)
motorSearchBar.grid(row=0, column=1)
motorUsedLabel.grid(row=1, column=0)
motorUsedSelection.grid(row=1, column=1)
motorSearchFrame.pack(fill="x")


# motor list
motorList = Listbox(motorInfoFrame, selectmode=SINGLE)
motorList.pack(expand = 1, fill ="both", side=LEFT)

motorDetailsFrame = Frame(motorInfoFrame)
motorDetails = Text(motorDetailsFrame, state="disabled", wrap=WORD)
motorDetails.pack(expand = 1, fill ="both")

thrustCurveFig = Figure(figsize=(5, 2), dpi=100)

TCcanvas = tkagg.FigureCanvasTkAgg(thrustCurveFig, master=motorDetailsFrame)
thrustCurve = thrustCurveFig.add_subplot()

motorDetailsFrame.pack(expand = 1, fill ="both", side=LEFT)
motorInfoFrame.pack(expand = 1, fill ="both")


'''
Stats Tab
'''

statsFrame = Frame(statsTab)

# stats settings
statsSettingsFrame = Frame(statsFrame)
statsConfidenceLabel = Label(statsSettingsFrame, text="Include Confirmed Only? ")
statsConfidence = Combobox(statsSettingsFrame, values=["Yes", "No"], state="readonly")
statsConfidence.current(0)
statsSuccessOnlyLabel = Label(statsSettingsFrame, text="Include Successes Only? ")
statsSuccessOnly = Combobox(statsSettingsFrame, values=["Yes", "No"], state="readonly")
statsSuccessOnly.current(1)

statsConfidenceLabel.grid(row=0, column=0)
statsConfidence.grid(row=0, column=1)
statsSuccessOnlyLabel.grid(row=0, column=2)
statsSuccessOnly.grid(row=0, column=3)
statsSettingsFrame.pack(fill ="both")

# stats output
statsText = Text(statsFrame, state="disabled", wrap=WORD)
statsText.pack(expand = 1, fill ="both")
statsFrame.pack(expand = 1, fill ="both")





# read in previous data
if (preferences.logFile != ""):
    log.readJSON(preferences.logFile)

def doubleClickHandler(event):
    if (event.widget == logList):
        if (len(logList.curselection()) != 0):
            log.getFlight(logList.selection_get()).openInWindow()

    if (event.widget == rocketList):
        if (len(rocketList.curselection()) != 0):
            log.getFlights()

    if (event.widget == electronicsList):
        if (len(electronicsList.curselection()) != 0):
            log.getFlights()




def rightClickHandler(event):
    rightClickMenu = Menu(window, tearoff=0)
    rightClickMenu.add_command(label="Update", command=lambda: log.handleUpdate(""))
    rightClickMenu.add_command(label="Delete", command=log.delete)
    rightClickMenu.add_separator()
    rightClickMenu.add_command(label="Undo", command=log.URHandler.undo)
    rightClickMenu.add_command(label="Redo", command=log.URHandler.redo)
    try:
        if (event.widget == logList):
            logList.selection_clear(0, END)
            logList.select_set(logList.nearest(event.y))

        if (event.widget == rocketList):
            rocketList.selection_clear(0, END)
            rocketList.select_set(rocketList.nearest(event.y))
            rightClickMenu.add_command(label="View Flights", command=log.getFlights)
            rightClickMenu.add_separator()
            rightClickMenu.add_command(label="Add Photo", command=log.rocketManagementWindow.addPicture)
            rightClickMenu.add_command(label="Remove Photo", command=log.rocketManagementWindow.removePicture)

        if (event.widget == electronicsList):
            electronicsList.selection_clear(0, END)
            electronicsList.select_set(electronicsList.nearest(event.y))
            rightClickMenu.add_command(label="View Flights", command=log.getFlights)
        rightClickMenu.tk_popup(event.x_root, event.y_root)

    finally:
        rightClickMenu.grab_release()


window.bind('<Double-Button-1>', doubleClickHandler)
window.bind('<Button-3>', rightClickHandler)


prevLog = ""
logForgot = True
prevRocket = ""
rocketForgot = True
prevElectronic = ""
electronicForgot = True
prevMotor = ""
motorForgot = True
prevStatsConfidence = ""
prevStatsSuccess = ""

while True:

    if (windowClosed):
        break
    # update log details
    if (len(logList.curselection()) != 0):
        currLog = log.getFlight(logList.selection_get())
        if ((currLog != prevLog or log.tkinterRefresh) and currLog != None):
            prevLog = currLog
            logForgot = False
            logDetails['state'] = 'normal'
            logDetails.delete("1.0", END)
            logDetails.insert(END, currLog.getDetails())
            logDetails['state'] = 'disabled'

            logUpdateButton.pack_forget()
            logDataViewerButton.pack_forget()
            logDeleteButton.pack_forget()
            logUpdateButton.pack(expand = 1, fill = BOTH, side = LEFT)
            if (currLog.FDFilename != ""):
                logDataViewerButton.pack(expand = 1, fill = BOTH, side = LEFT)
            else:
                logDataViewerButton.pack_forget()
            logDeleteButton.pack(expand = 1, fill = BOTH, side = LEFT)
    else:
        if (not logForgot or log.tkinterRefresh):
            prevLog = ""
            logForgot = True
            logDetails['state'] = 'normal'
            logDetails.delete("1.0", END)
            logDetails['state'] = 'disabled'
            logUpdateButton.pack_forget()
            logDataViewerButton.pack_forget()
            logDeleteButton.pack_forget()

    # update rockets details
    if (len(rocketList.curselection()) != 0):
        currRocket = log.getRocket(rocketList.selection_get())
        if ((currRocket != prevRocket or log.tkinterRefresh) and currRocket != None):
            prevRocket = currRocket
            rocketForgot = False
            rocketDetails['state'] = 'normal'
            rocketDetails.delete("1.0", END)
            rocketDetails.insert(END, currRocket.getDetails())
            rocketDetails.insert(END, "\n\nStats:\n" + log.getStats(str(currRocket)))
            rocketDetails['state'] = 'disabled'
            rocketUpdateButton.pack(expand = 1, fill = BOTH, side = LEFT)
            rocketDeleteButton.pack(expand = 1, fill = BOTH, side = LEFT)
            if (currRocket.picture != ""):

                rocketImage = Image.open(currRocket.picture)
                rocketImage.thumbnail([int(rocketDetailsFrame.winfo_width()/2), int(rocketDetailsFrame.winfo_height())], Image.Resampling.LANCZOS)
                rocketImage = ImageTk.PhotoImage(rocketImage)
                rocketImageLabel["image"] = rocketImage
                rocketButtonsFrame.pack_forget()
                rocketImageLabel.pack(fill=X, side=LEFT)
                rocketButtonsFrame.pack(expand = 1, fill ="x")
            else:
                rocketImageLabel.pack_forget()
    else:
        if (not rocketForgot or log.tkinterRefresh):
            prevRocket = ""
            rocketForgot = True
            rocketDetails['state'] = 'normal'
            rocketDetails.delete("1.0", END)
            rocketDetails['state'] = 'disabled'
            rocketUpdateButton.pack_forget()
            rocketDeleteButton.pack_forget()
            rocketImageLabel.pack_forget()

    # update electronics details
    if (len(electronicsList.curselection()) != 0):
        currElectronic = log.getElectronic(electronicsList.selection_get())
        if (currElectronic != None and (currElectronic != prevElectronic or log.tkinterRefresh)):
            prevElectronic = currElectronic
            electronicForgot = False
            electronicsDetails['state'] = 'normal'
            electronicsDetails.delete("1.0", END)
            electronicsDetails.insert(END, currElectronic.getDetails())
            electronicsDetails.insert(END, "\n\nStats:\n" + log.getStats(str(currElectronic)))
            electronicsDetails['state'] = 'disabled'
            electronicsUpdateButton.pack(expand = 1, fill = BOTH, side = LEFT)
            electronicsDeleteButton.pack(expand = 1, fill = BOTH, side = LEFT)
    else:
        if (not electronicForgot or log.tkinterRefresh):
            prevElectronic = ""
            electronicForgot = True
            electronicsDetails['state'] = 'normal'
            electronicsDetails.delete("1.0", END)
            electronicsDetails['state'] = 'disabled'
            electronicsUpdateButton.pack_forget()
            electronicsDeleteButton.pack_forget()

    # update motor details

    if(len(motorList.curselection()) != 0):
        motor = log.getMotor(motorList.selection_get())
        if (motor != None and (motor != prevMotor or log.tkinterRefresh)):
            prevMotor = motor
            rocketForgot = False

            motorDetails['state'] = 'normal'
            motorDetails.delete("1.0", END)
            MDStr = str(motor)
            MDStr += "\nManufacturer: " + motor.manufacturer
            MDStr += "\nTotal Impulse: " + str(round(motor.totalImpulse)) + " Ns"
            MDStr += "\nDiameter: " + str(motor.diameter) + " mm"
            MDStr += "\nLength: " + str(Number(motor.length/1000, Number.Type.MOTORLEN, preferences, alreadyMetric=True))
            MDStr += "\nWeight: " + str(Number(motor.totalWeight, Number.Type.MOTORMASS, preferences, alreadyMetric=True))
            MDStr += "\nPropellant Mass: " + str(Number(motor.propWeight, Number.Type.MOTORMASS, preferences, alreadyMetric=True))


            motorDetails.insert(END, MDStr)
            motorDetails.insert(END, "\n\nStats:\n" + log.getStats(str(motor)))
            motorDetails['state'] = 'disabled'



            thrustCurve.clear()
            thrust = motor.getThrustArray()
            if (preferences.thrustUnit == "lbf"):
                for i in range(len(thrust)):
                    thrust[i] = thrust[i]/4.4482
                thrustCurve.set_ylabel("Thrust(lbf)")
            else:
                thrustCurve.set_ylabel("Thrust(N)")

            thrustCurve.plot(motor.getTimeArray(), thrust)

            thrustCurve.set_xlabel("Time(s)")

            thrustCurve.set_title("Thrust Curve")

            thrustCurve.grid(True)

            thrustCurveFig.tight_layout()


            TCcanvas.draw()

            # placing the canvas on the Tkinter window
            TCcanvas.get_tk_widget().pack()
    else:
        if (not rocketForgot or log.tkinterRefresh):
            prevMotor = ""
            rocketForgot = True
            motorDetails['state'] = 'normal'
            motorDetails.delete("1.0", END)
            motorDetails['state'] = 'disabled'
            thrustCurve.clear()
            TCcanvas.draw()

            # placing the canvas on the Tkinter window
            TCcanvas.get_tk_widget().pack()


    # update stats

    if (statsConfidence.get() != prevStatsConfidence or log.tkinterRefresh):
        prevStatsConfidence = statsConfidence.get()
        log.updateStats()
    elif (statsSuccessOnly.get() != prevStatsSuccess or log.tkinterRefresh):
        prevStatsSuccess = statsSuccessOnly.get()
        log.updateStats()

    if (log.tkinterRefresh):
        log.tkinterRefresh = False


    window.update()

