#pylint: disable=import-error
import maya.cmds
import inspect
import pyf
import imp
import iconLib.functions
# from abc import ABCMeta
#pylint: enable=import-error
import traceback
import sys
from keopsPrint import PrintShop

pShop = PrintShop(prefix="[keops][keopsUI]")
Print = pShop._print
class Factory(object):
    __Instance = None
    def __new__(klass, *args, **kwargs):
        if Factory.__Instance is None:
            Factory.__Instance = super(Factory, klass).__new__(klass)
            Factory.__Instance.__initialize()
        return Factory.__Instance


    def __init__(self):
        super(Factory, self).__init__()


    def __initialize(self):
        self.uis = {}
        path = pyf.path.dirname(__file__)

        for f in pyf.glob("%s/[!__]*.py" % path):
            filename = pyf.path.splitext(pyf.path.split(f)[1])[0]
            module = imp.load_source(filename, f)
            inspector = inspect.getmembers(module, inspect.isclass)
            for name, obj in inspector:
                # This collector doesnt care what the name of the python file is, only the name of the Class
                if issubclass(obj, BaseUI):
                    self.uis[name] = obj


    def report(self):
        Print("Available UIs:", head=True)
        Print(sorted(self.uis))


    @staticmethod
    def Construct(name, *args, **kwargs):
        factory = Factory()
        if not factory.uis.get(name, None):
            raise Exception("No ui of name: %s" % name)
        ui = factory.uis[name](*args) # init the UI
        if name == "Alert":
            return ui.construct(**kwargs) # This means we're waiting on the return of a prompt dialog
        ui.construct(**kwargs)
        return ui


class BaseUI(object):
    # __metaclass__ = ABCMeta
    def __init__(self, **kwargs):
        super(BaseUI, self).__init__()
        self.ui = {}
        self.wh = [320, 240]
        self.mzButton = iconLib.functions.mzButton
        self.name = "default window"
        self.ver = "1.0.0"

    def build(self):
        Print("Build Not implemented")

    def construct(self, **kwargs):
        self.kill(**kwargs)
        self.build()
        self.assignCallBacks()
        self.assignTooltips()
        self.postProcess()

    def assignCallBacks(self):
        Print("Ass backs Not implemented")
        return

    def assignTooltips(self):
        Print("Ass tips Not implemented")
        return

    def postProcess(self):
        Print("PostProc Not implemented")
        return

    def buildKwargs(self, elements):
        Print("BuildKwargs not implemented")
        return

    def report(self):
        Print("report not implemented")
        return

    def kill(self, **kwargs):
        verbose = kwargs.get("verbose", False)
        realName = self.name.replace(" ", "_")
        if maya.cmds.window(self.name, ex=True):
            maya.cmds.deleteUI(self.name)
        elif maya.cmds.window(realName, ex=True):
            maya.cmds.deleteUI(realName)
        else:
            if verbose:
                Print("not found : %s" % self.name)


