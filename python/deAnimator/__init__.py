#pylint: disable=import-error
import rigAbstraction
import maya.cmds
import pyf
#pylint: enable=import-error
import timeFilter.functions
import keopsPrint 

pShop = keopsPrint.PrintShop(prefix="[keops][deAnimator]")
Print = pShop._print

    
class DeAnimator(object):
    def __init__(self):
        super(DeAnimator, self).__init__()

    def getRigs(self, allRigs=False, simple=False, verbose=False):
        rigs = {}
        for x in rigAbstraction.List():
            rig = Rig(x, simple=simple)
            if len(rig.curves) > 0 or allRigs:
                rigs[rig.name] = rig
                if verbose:
                    Print("Got %s" % rig.name)
        return rigs


    def getExtras(self, verbose=False):
        legal = set([])
        assemblies = set(maya.cmds.ls(assemblies=True))
        rigs = self.getRigs(allRigs=True, simple=True, verbose=verbose).keys()
        cameras = maya.cmds.ls(cameras=True) or []
        headsUp = maya.cmds.ls(type="mzHeadsupLocator")
        mzCams = maya.cmds.ls("::*mzCam*")
        legal.update(rigs)
        legal.update(mzCams)
        legal.update(maya.cmds.listRelatives(mzCams, p=True) or [])
        legal.update(maya.cmds.listRelatives(rigs, p=True) or [])
        legal.update(maya.cmds.listRelatives(cameras, p=True))
        legal.update(maya.cmds.listRelatives(headsUp, p=True))
        nodes = assemblies - legal
        return(nodes)


    def killExtras(self, nodes, verbose=True, dryrun=True):
        for x in nodes:
            if maya.cmds.reference(x, inr=True, q=True):
                continue
            children = maya.cmds.listRelatives(x, c=True) or []
            readOnly = maya.cmds.ls(children, readOnly=True) or []
            if not readOnly and maya.cmds.objExists(x):
                if dryrun or verbose:
                    Print("Goodbye %s" % x)
                if not dryrun:
                    maya.cmds.delete(x)
            else:
                readNotOnly = set(children)-set(readOnly)
                self.killExtras(readNotOnly)

class Rig(object):
    def __init__(self, rigAbs=None, simple=False):
        super(Rig, self).__init__()
        if not isinstance(rigAbs, rigAbstraction.Rig):
            Print("Requires rigAbstraction.Rig as first arg")
            raise Exception()
        self.name = None
        # self.attrs = set([])
        self.ctls = set([])
        self.groups = set([])
        self.curves = set([])
        self. __initialize__(rigAbs, simple=simple)


    def __initialize__(self, rigAbs, simple=False):
        self.name = maya.cmds.ls(rigAbs.topNode())[0]
        if simple:
            return
        self.groups = rigAbs.listGroups()
        for group in self.groups:
            try:
                self.ctls.update(rigAbs.listControllers(group))
                # self.attrs.update(rigAbs.listAttrs(group))
            except:
                Print("%s not supported as deAnimatable" % self.name)
                continue
            else:
                self.getCurves()


    def report(self, verbose=False):
        if not verbose:
            Print(self.name, head=True)
            Print("ctls : %s" % len(self.ctls))
            Print("animCurves : %s" % len(self.curves))
        else:
            Print(self.__dict__)


    def getCurves(self):
        self.curves = set([])
        for x in self.ctls:
            self.curves.update(GetCurves(x))


    def deleteCurves(self, dryrun=False, verbose=False):
        curves = [x for x in self.curves if maya.cmds.objExists(x)]
        msg = KillCurves(curves, dryrun=dryrun, verbose=verbose)
        Print(self.name, head=True)
        Print(msg)


def GetCurves(node):
    curves = timeFilter.functions.GetAllDGNodes(inNode=node, findNodes = "animCurves")
    return curves


def KillGeneric(node, dryrun=False, verbose=False):
    obs = maya.cmds.listRelatives(node, c=True)
    curves = set([])

    for x in obs:
        curves.update(GetCurves(x))

    msg = KillCurves(curves, dryrun=dryrun, verbose=verbose)
    Print("%s" % node, head=True)
    Print(msg)


def KillCurves(curves, dryrun=False, verbose=False):

    preCount = len(curves)

    if preCount == 0:
        return "No curves"

    killCount = 0

    for x in curves:
        connex = maya.cmds.listConnections(x, d=True, s=False, p=True, c=True)
        if dryrun or verbose:
            Print(connex)

        if not dryrun:
            try:
                maya.cmds.disconnectAttr(connex[0], connex[1])
                maya.cmds.delete(x)
            except:
                if verbose:
                    Print("Fail : %s" % x)
            else:
                killCount += 1

    if preCount == killCount:
        msg = ("Removed all animCurves")
    else:
        msg = ("Removed %s out of %s animCurves" % (killCount, preCount))

    return msg


def GetAbout():
    _about = "Could not find about file"
    helpFile = pyf.path.join(pyf.path.dirname(pyf.path.abspath(__file__)), "about.md")
    if pyf.path.isfile(helpFile):
        f = open(helpFile, "r")
        _about = (f.read()) 
    return _about    

    

                

    


