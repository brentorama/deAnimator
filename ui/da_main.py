#pylint: disable=import-error
import iconLib
import maya.cmds
from Qt import QtWidgets
from Qt import QtCore
from Qt import QtGui
import ui
#pyline: enable=import-error
import deAnimator
from functools import partial

Rigs = {}

class DeAnimator(ui.BaseUI):
    def __init__(self, parent=None):
        super(DeAnimator, self).__init__(parent=parent)
        self.verbose = False
        self.dryrun = False
        self.wh = [600, 300]
        self.mzButton = iconLib.functions.mzButton
        self.name = "DeAnimator"
        self.ver = "0.1.0"
        self.ui = {}

    def build(self):
        if maya.cmds.selectionConnection("deAnimator", q=True, ex=True):
            maya.cmds.deleteUI("deAnimator")

        wndw = maya.cmds.window(self.name, t="%s %s" % (self.name, self.ver), wh=self.wh, menuBar=True)

        main = maya.cmds.formLayout("main", nd=100, p=wndw)
        panl = maya.cmds.paneLayout("panels", configuration ="vertical2", p=main,  h=5, paneSize=([1, 70, 100]))
        hlpl = maya.cmds.helpLine("helpLine", p=main)

        colA = maya.cmds.formLayout("colA", nd=100, p=panl, h=5)
        adds = self.mzButton("mzGoodcon","add object")
        rems = self.mzButton("mzBadcon", "remove object")
        refs = self.mzButton("mzReload", "refresh list")
        
        otpl = maya.cmds.outlinerPanel(mbv=False)
        objs = maya.cmds.outlinerPanel(otpl, query=True, outlinerEditor=True)
        slcn = maya.cmds.selectionConnection("deAnimator")
        maya.cmds.outlinerEditor(objs, edit=True, mainListConnection=slcn, ln=True, nn=False, sn=True, dag=False)


        colB = maya.cmds.formLayout("colB", nd=100, p=panl)
        chka = maya.cmds.checkBox("dryrun", al="center", v=0)
        chkb = maya.cmds.checkBox("verbose", al="center", v=0)
        aide = self.mzButton("mzQ", "Help")
        doit = self.mzButton("mzCheck","Execute")

        maya.cmds.formLayout(main, edit=True, af=[(panl, "top", 5),
                                                 (panl, "bottom", 20),
                                                 (panl, "left", 5),
                                                 (panl, "right", 5),
                                                 (hlpl, "left", 5),
                                                 (hlpl, "bottom", 0)],
                                             ap=[(hlpl, "right", 5, 100)]) 

        maya.cmds.formLayout(colA, edit=True, af=[(adds, "top", 0),
                                                  (adds, "left", 0),
                                                  (otpl, "top", 0),
                                                  (otpl, "right", 0),
                                                  (otpl, "bottom", 0)],
                                              ac=[(rems, "top", 5, adds),
                                                   (refs, "top", 5, rems),
                                                   (otpl, "left", 5, adds)])

        maya.cmds.formLayout(colB, edit=True, af=[(chka, "top", 0),
                                                  (chka, "left", 0),
                                                  (aide, "bottom", 5),
                                                  (doit, "bottom", 5),
                                                  (doit, "right", 5)],
                                              ac=[(chkb, "top", 5, chka),
                                                 (aide, "right", 5, doit)])
        ui = {}
        ui.window = [wndw, "", "window"]
        ui.panel = [panl, "The friendly deAnimator menu for cool dudes and rockin' homeboys", "paneLayout"]
        ui.form =[main, "", ""]
        ui.cola = [colA, "", ""]
        ui.colb =  [colB, "", ""]
        ui.selcon = [slcn, "", ""]
        ui.outliner = [otpl, "", ""]
        ui.add = [adds, "Add selectde to list", "iconTextButton"]
        ui.remove = [rems, "Remove selected from list", "iconTextButton"]
        ui.refresh = [refs, "Refresh the list based on rigs", "iconTextButton"]
        ui.dryrun = [chka, "Dryrun", "checkBox"]
        ui.verbose = [chkb, "Talk to me baby", "checkBox"]
        ui.doit = [doit, "DeAniamte selected", "iconTextButton"]
        ui.help = [aide, "Get help", "iconTextButton"]

        self.ui=ui


    def assignCallBacks(self):

        maya.cmds.iconTextButton(self.ui.add[0], e=True, ebg=True, c=partial(self.add))
        maya.cmds.iconTextButton(self.ui.remove[0], e=True, ebg=True, c=partial(self.remove))
        maya.cmds.iconTextButton(self.ui.refresh[0], e=True, ebg=True,   c=partial(self.refresh))
        maya.cmds.iconTextButton(self.ui.doit[0], e=True, ebg=True,   c=partial(self.execute))
        maya.cmds.iconTextButton(self.ui.help[0], e=True, ebg=True, c=partial(About))
        maya.cmds.checkBox(self.ui.verbose[0],  e=True,  cc=partial(self.toggle))
        maya.cmds.checkBox(self.ui.dryrun[0],  e=True,  cc=partial(self.toggle))
    

    def assignTooltips(self):

        for item in self.ui:
            if self.ui[item][1]:
                try:
                    maya.mel.eval("%s -e -ann \"%s\" %s" % (self.ui[item][2], self.ui[item][1], self.ui[item][0]))
                except:
                    continue


    def postProcess(self):
        self.refresh()
        maya.cmds.showWindow(self.ui.window[0])
        maya.cmds.window(self.ui.window[0], e=True, wh=self.wh)


    def report(self, *ignore):
        Print("report not implemented")
        return


    def add(self, *ignore):
        objects = maya.cmds.selectionConnection(self.ui["selcon"][0], q=True, object=True) or []
        selected = maya.cmds.ls(sl=True) or []
        newList = set(objects).union(set(selected))
        self.refresh(objects = newList)


    def remove(self, *ignore):
        objects = maya.cmds.selectionConnection(self.ui["selcon"][0], q=True, object=True) or []
        selected = maya.cmds.ls(sl=True) or []
        newList = set(objects)-set(selected)
        self.refresh(objects = newList)


    def toggle(self, *ignore):
        self.dryrun = maya.cmds.checkBox(self.ui.dryrun[0], q=True, v=True)
        self.verbose = maya.cmds.checkBox(self.ui.verbose[0], q=True, v=True)


    def refresh(self, objects=None, *ignore):
        global Rigs

        if objects is None:
            da = deAnimator.DeAnimator()
            Rigs = da.getRigs(verbose=self.verbose)
            objects = Rigs.keys()

        outliner = self.ui["outliner"][0]
        selCon = self.ui["selcon"][0]

        maya.cmds.selectionConnection(selCon, e=True, clr=True)

        for one in objects:
            maya.cmds.selectionConnection(selCon, e=True, select=one)

        maya.cmds.outlinerEditor(outliner, edit=True, mainListConnection=selCon, dag=False)


    def execute(self):
        global Rigs

        objects = maya.cmds.selectionConnection(self.ui["selcon"][0], q=True, object=True)
        selected = maya.cmds.ls(sl=True)

        if selected:
            objects = set(objects)&set(selected)
        
        if not objects:
            Print("Nothing selected - either select None or some from the DeAnimator UI")
            return

        rigs = []
        unique = []
        dryrun = self.dryrun
        verbose = self.verbose

        for x in objects:
            if x in Rigs:
                rigs.append(x)
            else:
                unique.append(x)

        rcount = len(rigs)
        ucount = len(unique)

        if rcount:
            Print("Found %s rigs" % rcount, head=True)
            for x in rigs:
                Rigs[x].deleteCurves(dryrun=dryrun, verbose=verbose)

        if ucount:
            Print("Found %s unique" % ucount, head=True)
            for x in unique:
                deAnimator.KillGeneric(x, dryrun=dryrun, verbose=verbose)

        self.refresh()


class About(QtWidgets.QDialog):
    def __init__(self):
        super(About, self).__init__() 

        aboutText = deAnimator.GetAbout()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignHCenter)

        textBox = QtWidgets.QLabel()
        textBox.setWordWrap(True)
        textBox.setText(aboutText)
        textBox.setFont(QtGui.QFont("Monospace", 10, weight=QtGui.QFont.ExtraBold))

        helpBox = QtWidgets.QLabel()
        helpBox.setText(u'<p> For help contact <a href='"'mailto:grtechsupport@marza.com'"'>grtechsupport@marza.com</a>  </p>')
        helpBox.setFont(QtGui.QFont("Monospace", weight=QtGui.QFont.ExtraBold))
        helpBox.setAlignment(QtCore.Qt.AlignHCenter)
        helpBox.setOpenExternalLinks(True)

        layout.addWidget(textBox)
        layout.addWidget(helpBox)
        self.setLayout(layout)

        self.exec_()
