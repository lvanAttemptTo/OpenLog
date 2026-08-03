class Num:
    def __init__(self, val):
        self.val = val

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return str(self.val)

class Log:

    def __init__(self, val):
        self.val = val
        self.URHandler = None


    def createURHandler(self):
        if (self.URHandler == None):
            self.URHandler = Log.UndoRedoHandler(self)

    def setVal(self, val):
        self.createURHandler()
        self.val = val
        self.URHandler.addState()


    def clone(self):
        return Log(self.val)

    def set(self, log):
        self.val = log.val

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return str(self.val)

    class UndoRedoHandler:
        def __init__(self, log):
            self.log = log
            self.editChain = [self.log.clone()]
            self.pointer = 0

        def addState(self):
            self.pointer += 1
            self.editChain = (self.editChain[:self.pointer])
            self.editChain.append(self.log.clone())
            print(self.editChain)

        def undo(self):
            if (self.pointer == 0):
                return

            self.pointer -= 1
            self.log.set(self.editChain[self.pointer])

        def redo(self):
            if (self.pointer < len(self.editChain) - 1):
                self.pointer += 1
                self.log.set(self.editChain[self.pointer])


log = Log(0)
for i in range(10):
    log.setVal(Num(i))

for i in range(5):
    log.URHandler.undo()
    print(log)

log.setVal(Num(1000))
for i in range(5):
    log.URHandler.undo()
    print(log)
for i in range(5):
    log.URHandler.redo()
    print(log)