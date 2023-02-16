#pylint: disable=import-error
import maya.cmds
import os
#pylint: enable=import-error

    
class DeAnimator(object):
    def __init__(self):
        super(DeAnimator, self).__init__()

    def getRigs(self, allRigs=False, simple=False, verbose=False):
        pass
        # rigs = {}
        # for x in XXXXXX.List():
        #     rig = Rig(x, simple=simple)
        #     if len(rig.curves) > 0 or allRigs:
        #         rigs[rig.name] = rig
        #         if verbose:
        #             print("Got %s" % rig.name)
        # return rigs


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
                    print("Goodbye %s" % x)
                if not dryrun:
                    maya.cmds.delete(x)
            else:
                readNotOnly = set(children)-set(readOnly)
                self.killExtras(readNotOnly)

class Rig(object):
    def __init__(self, rigAbs=None, simple=False):
        super(Rig, self).__init__()
        if not isinstance(rigAbs, rigAbstraction.Rig):
            print("Requires rigAbstraction.Rig as first arg")
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
                print("%s not supported as deAnimatable" % self.name)
                continue
            else:
                self.getCurves()


    def report(self, verbose=False):
        if not verbose:
            print(self.name, head=True)
            print("ctls : %s" % len(self.ctls))
            print("animCurves : %s" % len(self.curves))
        else:
            print(self.__dict__)


    def getCurves(self):
        self.curves = set([])
        for x in self.ctls:
            self.curves.update(GetCurves(x))


    def deleteCurves(self, dryrun=False, verbose=False):
        curves = [x for x in self.curves if maya.cmds.objExists(x)]
        msg = KillCurves(curves, dryrun=dryrun, verbose=verbose)
        print(self.name, head=True)
        print(msg)


def GetCurves(node):
    curves = GetAllDGNodes(inNode=node, findNodes = "animCurves")
    return curves


def GetAllDGNodes(inNode=None, where="up", findNodes=None):
    # Search the DGraph for animCurves connected to a given nodes
    direction = None

    if type(findNodes) not in (list, set):
        findNodes = [findNodes]

    canFind = {"animCurves" :  maya.OpenMaya.MFn.kAnimCurve,
               "transforms" :  maya.OpenMaya.MFn.kTransform,
               "constraints":  maya.OpenMaya.MFn.kConstraint,
               "caches":       maya.OpenMaya.MFn.kCacheFile,
               "pluginDefs":   maya.OpenMaya.MFn.kPluginDeformerNode,
               "time":         maya.OpenMaya.MFn.kTime} 

    nodeMfnTypes = set([])

    for x in findNodes:
        mfnType = canFind.get(x, None)
        if not mfnType:
            print("Bad nodeType key: %s, valid are %s" % (x, ", ".join(canFind.keys())))
            raise Exception()
        nodeMfnTypes.add(mfnType)

    graphDirection = {"up"   : maya.OpenMaya.MItDependencyGraph.kUpstream,
                      "down" : maya.OpenMaya.MItDependencyGraph.kDownstream}

    direction = graphDirection.get(where, None)

    # Create a MSelectionList with our selected items:
    selList = maya.OpenMaya.MSelectionList()
    selList.add(inNode)
    mObject = maya.OpenMaya.MObject()  # The current object
    selList.getDependNode( 0, mObject )

    # Create a dependency graph iterator for our current object:
    nodes = set([])

    for nodeMfnType in nodeMfnTypes:
        depIt = maya.OpenMaya.MItDependencyGraph(mObject, nodeMfnType, direction, maya.OpenMaya.MItDependencyGraph.kDepthFirst, maya.OpenMaya.MItDependencyGraph.kNodeLevel)

        # Loop through the iterator and find all nodes of specified type
        while not depIt.isDone():
            nodes.add(maya.OpenMaya.MFnDependencyNode(depIt.currentItem()).name())
            depIt.next()

    nodes = list(nodes)

    return nodes


def KillGeneric(node, dryrun=False, verbose=False):
    obs = maya.cmds.listRelatives(node, c=True)
    curves = set([])

    for x in obs:
        curves.update(GetCurves(x))

    msg = KillCurves(curves, dryrun=dryrun, verbose=verbose)
    print("%s" % node, head=True)
    print(msg)


def KillCurves(curves, dryrun=False, verbose=False):

    preCount = len(curves)

    if preCount == 0:
        return "No curves"

    killCount = 0

    for x in curves:
        connex = maya.cmds.listConnections(x, d=True, s=False, p=True, c=True)
        if dryrun or verbose:
            print(connex)

        if not dryrun:
            try:
                maya.cmds.disconnectAttr(connex[0], connex[1])
                maya.cmds.delete(x)
            except:
                if verbose:
                    print("Fail : %s" % x)
            else:
                killCount += 1

    if preCount == killCount:
        msg = ("Removed all animCurves")
    else:
        msg = ("Removed %s out of %s animCurves" % (killCount, preCount))

    return msg


def GetAbout():
    _about = "Could not find about file"
    helpFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "about.md")
    if os.path.isfile(helpFile):
        f = open(helpFile, "r")
        _about = (f.read()) 
    return _about    

    

                

    


