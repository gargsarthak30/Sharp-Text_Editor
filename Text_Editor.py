import wx
import wx.stc as stc
import os
import wx.lib.dialogs
import keyword
from xml.dom.minidom import parse
import xml.dom.minidom

faces = {
    'mono': 'Courier New',
    'helv': 'Helvetica',
    'other': 'Comic Sans MS',
    'size': 11,
    'size2': 8
        }

class MainWindow(wx.Frame):
    def __init__(self,parent,title):
        
        self.theme_number = 1
        self.dirname=''
        self.filename=''
        self.normalStylesFore = dict()
        self.normalStylesBack = dict()
        self.pythonStylesFore = dict()
        self.pythonStylesBack = dict()

        self.leftMarginWidth = 25
        self.lineNumbersEnabled = True
        
        wx.Frame.__init__(self,parent,title=title,size=(800,600))
        self.control = stc.StyledTextCtrl(self,style=wx.TE_MULTILINE | wx.TE_WORDWRAP)

        self.control.CmdKeyAssign(ord('+'),stc.STC_SCMOD_CTRL,stc.STC_CMD_ZOOMIN) #Ctrl + = to Zoom In
        self.control.CmdKeyAssign(ord('-'),stc.STC_SCMOD_CTRL,stc.STC_CMD_ZOOMOUT) #Ctrl - to Zoom Out

        # Python keywords for syntax highlighting
        self.control.SetLexer(stc.STC_LEX_PYTHON)
        self.control.SetKeyWords(0, " ".join(keyword.kwlist))
        
        self.control.SetViewWhiteSpace(False)
        self.control.SetMargins(5,0)
        self.control.SetMarginType(1,stc.STC_MARGIN_NUMBER)
        self.control.SetMarginWidth(1,self.leftMarginWidth)
        self.CreateStatusBar()
        self.StatusBar.SetBackgroundColour((220,220,220))

        filemenu = wx.Menu()
        menuNew = filemenu.Append(wx.ID_NEW, "&New", "Create a new document")
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open", "Open an existing document")
        menuSave = filemenu.Append(wx.ID_SAVE, "&Save", "Save the current document")
        menuSaveAs = filemenu.Append(wx.ID_SAVEAS, "Save &As", "Save a new document")
        filemenu.AppendSeparator()
        menuClose = filemenu.Append(wx.ID_EXIT, "&Close", "Close the Application")

        editmenu = wx.Menu()
        menuUndo = editmenu.Append(wx.ID_UNDO, "&Undo", "Undo last action")
        menuRedo = editmenu.Append(wx.ID_REDO, "&Redo", "Red last Action")
        editmenu.AppendSeparator()
        menuSelectAll = editmenu.Append(wx.ID_SELECTALL, "&Select All", "Select the whole document")
        menuCopy = editmenu.Append(wx.ID_COPY, "&Copy", "Copy Selected Text")
        menuCut = editmenu.Append(wx.ID_CUT, "C&ut", "Cut Selected Text")
        menuPaste = editmenu.Append(wx.ID_PASTE, "&Paste", "Copy Selected Text")

        settingsmenu = wx.Menu()
        themes = settingsmenu.Append(wx.ID_ANY, "&Change Theme", "Change the Theme of Editor.")

        helpmenu = wx.Menu()
        menuHowTo = helpmenu.Append(wx.ID_ANY, "&How To...", "Get help using the editor.")
        helpmenu.AppendSeparator()
        menuAbout = helpmenu.Append(wx.ID_ABOUT, "&About", "Read About the Editor and its making")
        menuCredits = helpmenu.Append(wx.ID_ANY, "&Credits", "Open Source Credits")
        
        #------------Binding Menu Options to their Functions-----------------
        self.Bind(wx.EVT_MENU,self.OnNew,menuNew)
        self.Bind(wx.EVT_MENU,self.OnOpen,menuOpen)
        self.Bind(wx.EVT_MENU,self.OnSave,menuSave)
        self.Bind(wx.EVT_MENU,self.OnSaveAs,menuSaveAs)
        self.Bind(wx.EVT_MENU,self.OnClose,menuClose)

        self.Bind(wx.EVT_MENU,self.OnUndo,menuUndo)
        self.Bind(wx.EVT_MENU,self.OnRedo,menuRedo)
        self.Bind(wx.EVT_MENU,self.OnSelectAll,menuSelectAll)
        self.Bind(wx.EVT_MENU,self.OnCopy,menuCopy)
        self.Bind(wx.EVT_MENU,self.OnCut,menuCut)
        self.Bind(wx.EVT_MENU,self.OnPaste,menuPaste)

        self.Bind(wx.EVT_MENU,self.OnHowTo,menuHowTo)
        self.Bind(wx.EVT_MENU,self.OnAbout,menuAbout)
        self.Bind(wx.EVT_MENU,self.OnCredits,menuCredits)
        #------------Binding Menu Options to their Functions: Ends-----------------
 
        #------------Binding Advanced Functions-----------------
        self.control.Bind(wx.EVT_KEY_UP,self.UpdateLineCol)
        self.control.Bind(wx.EVT_CHAR,self.OnCharEvent)
        self.control.Bind(wx.EVT_LEFT_UP,self.OnLeftUp)
        self.control.Bind(wx.EVT_UPDATE_UI,self.OnUpdateUI)
        self.Bind(wx.EVT_MENU,self.OnThemeChange,themes)
        #------------Binding Advanced Functions-----------------
        
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        menuBar.Append(editmenu, "&Edit")
        menuBar.Append(settingsmenu, "&Settings")
        menuBar.Append(helpmenu, "&Help")
        
        self.SetMenuBar(menuBar)

        #---------------Designing Ends-------------
        self.Show()
        self.UpdateLineCol(self)
        self.control.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
        self.control.StyleClearAll() 
        # global default styles for all languages
        self.control.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
        self.control.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "back:#C0C0C0,face:%(helv)s,size:%(size2)d" % faces)
        self.control.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % faces)
        self.control.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#FFFFFF,back:#0000FF,bold")
        self.control.StyleSetSpec(stc.STC_STYLE_BRACEBAD, "fore:#000000,back:#FF0000,bold")
        self.ParseSettings("styling.xml")
        self.SetStyling()

        #---------------Set Styling Functions---------
    def SetStyling(self):
        # Set the general foreground and background for normal and python styles
        pSFore = self.pythonStylesFore
        pSBack = self.pythonStylesBack
        nSFore = self.normalStylesFore
        nSBack = self.normalStylesBack

            # Python styles
        self.control.StyleSetBackground(stc.STC_STYLE_DEFAULT, nSBack["Main"])
        if self.theme_number==1:
            self.control.SetSelBackground(True, "#dddddd")
        elif self.theme_number==2:
            self.control.SetSelBackground(True, "#666666") 

            # Default
        self.control.StyleSetSpec(stc.STC_P_DEFAULT, "fore:%s,back:%s" % (pSFore["Default"], pSBack["Default"]))
        self.control.StyleSetSpec(stc.STC_P_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)

            # Comments
        self.control.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:%s,back:%s" % (pSFore["Comment"], pSBack["Comment"]))
        self.control.StyleSetSpec(stc.STC_P_COMMENTLINE, "face:%(other)s,size:%(size)d" % faces)

            # Number
        self.control.StyleSetSpec(stc.STC_P_NUMBER, "fore:%s,back:%s" % (pSFore["Number"], pSBack["Number"]))
        self.control.StyleSetSpec(stc.STC_P_NUMBER, "size:%(size)d" % faces)

            # String
        self.control.StyleSetSpec(stc.STC_P_STRING, "fore:%s,back:%s" % (pSFore["String"], pSBack["Number"]))
        self.control.StyleSetSpec(stc.STC_P_STRING, "face:%(helv)s,size:%(size)d" % faces)

            # Single-quoted string
        self.control.StyleSetSpec(stc.STC_P_CHARACTER, "fore:%s,back:%s" % (pSFore["SingleQuoteString"], pSBack["SingleQuoteString"]))
        self.control.StyleSetSpec(stc.STC_P_CHARACTER, "face:%(helv)s,size:%(size)d" % faces)

            # Keyword
        self.control.StyleSetSpec(stc.STC_P_WORD, "fore:%s,back:%s" % (pSFore["Keyword"], pSBack["Keyword"]))
        self.control.StyleSetSpec(stc.STC_P_WORD, "bold,size:%(size)d" % faces)

            # Triple quotes
        self.control.StyleSetSpec(stc.STC_P_TRIPLE, "fore:%s,back:%s" % (pSFore["TripleQuote"], pSBack["TripleQuote"]))
        self.control.StyleSetSpec(stc.STC_P_TRIPLE, "size:%(size)d" % faces)

            # Triple double quotes
        self.control.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:%s,back:%s" % (pSFore["TripleDoubleQuote"], pSBack["TripleDoubleQuote"]))
        self.control.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "size:%(size)d" % faces)

            # Class name definition
        self.control.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:%s,back:%s" % (pSFore["ClassName"], pSBack["ClassName"]))
        self.control.StyleSetSpec(stc.STC_P_CLASSNAME, "bold,underline,size:%(size)d" % faces)

            # Function name definition
        self.control.StyleSetSpec(stc.STC_P_DEFNAME, "fore:%s,back:%s" % (pSFore["FunctionName"], pSBack["FunctionName"]))
        self.control.StyleSetSpec(stc.STC_P_DEFNAME, "bold,size:%(size)d" % faces)

            # Operators
        self.control.StyleSetSpec(stc.STC_P_OPERATOR, "fore:%s,back:%s" % (pSFore["Operator"], pSBack["Operator"]))
        self.control.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)

            # Identifiers
        self.control.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:%s,back:%s" % (pSFore["Identifier"], pSBack["Identifier"]))
        self.control.StyleSetSpec(stc.STC_P_IDENTIFIER, "face:%(helv)s,size:%(size)d" % faces)

            # Comment blocks
        self.control.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:%s,back:%s" % (pSFore["CommentBlock"], pSBack["CommentBlock"]))
        self.control.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "size:%(size)d" % faces)

            # End of line where string is not closed
        self.control.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:%s,back:%s" % (pSFore["StringEOL"], pSBack["StringEOL"]))
        self.control.StyleSetSpec(stc.STC_P_STRINGEOL, "face:%(mono)s,eol,size:%(size)d" % faces)

            # Caret/Insertion Point
        self.control.SetCaretForeground(pSFore["Caret"])
        self.control.SetCaretLineBackground(pSBack["CaretLine"])
        self.control.SetCaretLineVisible(True)

  #---------------Normal Functions--------------
    def OnNew(self,e):
        self.filename=''
        self.control.SetValue("")

    def OnOpen(self,e):
        try:
            dlg = wx.FileDialog(self,"Choose a file", self.dirname, "", "*.*",wx.FD_OPEN)
            if(dlg.ShowModal()==wx.ID_OK):
                self.filename = dlg.GetFilename()
                self.dirname = dlg.GetDirectory()
                f = open(os.path.join(self.dirname,self.filename),'r')
                self.control.SetValue(f.read())
                f.close()
            dlg.Destroy()
        except:
            dlg = wx.MessageDialog(self,"Couldn't open the file",wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def OnSave(self,e):
        try:
            f = open(os.path.join(self.dirname,self.filename),'w')
            f.write(self.control.GetValue())
            f.close()
        except:
            try:
                dlg = wx.FileDialog(self,"Save File As",self.dirname,"Untitled","*.*",wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if(dlg.ShowModal()==wx.ID_OK):
                    self.filename = dlg.GetFilename()
                    self.dirname = dlg.GetDirectory()
                    f = open(os.path.join(self.dirname,self,filename),'w')
                    f.write()
                    f.close()
                dlg.Destroy()
            except:
                pass

    def OnSaveAs(self,e):
        dlg = wx.FileDialog(self,"Save File As",self.dirname,"Untitled","*.*",wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if(dlg.ShowModal()==wx.ID_OK):
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = open(os.path.join(self.dirname,self.filename),'w')
            f.write(self.control.GetValue())
            f.close()
        dlg.Destroy()
        
    def OnClose(self,e):
        self.Close(True)

    def OnUndo(self,e):
        self.control.Undo()

    def OnRedo(self,e):
        self.control.Redo()

    def OnSelectAll(self,e):
        self.control.SelectAll()

    def OnCopy(self,e):
        self.control.Copy()

    def OnCut(self,e):
        self.control.Cut()

    def OnPaste(self,e):
        self.control.Paste()
         
    def OnHowTo(self,e):
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self,"SHARP - Text Editor can be used as a normal Text Editor. However it supports syntax highlighting for Python hence is much more useful for Python Programmers.","How To Use SHARP", size = (400,400))
        dlg.ShowModal()
        dlg.Destroy()

    def OnAbout(self,e):
        dlg = wx.MessageDialog(self, "SHARP Text Editor\n Developer: Sarthak Garg (Gautam Buddha University)\n Email: gargsarthak30@gmail.com\n Github: github.com/gargsarthak30","About SHARP",wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnCredits(self,e):
        dlg = wx.MessageDialog(self, "A lot of help has been taken from various online sources for making this text editor. Thanks to Zach King for publishing tutorials! .","Credits",wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

        #------------------------ Advanced Functions--------------------------

    def UpdateLineCol(self,e):
        line = self.control.GetCurrentLine() + 1
        col = self.control.GetColumn(self.control.GetCurrentPos())
        stat = "Line: %s, Column: %s" %(line,col)
        self.StatusBar.SetStatusText(stat,0)

    def OnCharEvent(self,e):
        keycode = e.GetKeyCode()
        altDown = e.AltDown()

        if(keycode == 14): #Ctrl+ N
            self.OnNew(self)
        elif(keycode == 15): #Ctrl + O
            self.OnOpen(self)
        elif(keycode == 19): #Ctrl + S
            self.OnSave(self)
        elif(altDown and (keycode == 115)): #Alt + S
            self.OnSaveAs(self)
        elif(keycode == 23): #Ctrl + W
            self.OnClose(self)
        elif(keycode == 340): #F1
            self.OnHowTo(self)
        elif(keycode == 341): #F2
            self.OnAbout(self)
        else:
            e.Skip()

    def OnLeftUp(self,e):
        self.UpdateLineCol(self)
        e.Skip()

    def OnUpdateUI(self,e):
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.control.GetCurrentPos()

        if(caretPos>0):
            charBefore = self.control.GetCharAt(caretPos - 1)
            styleBefore = self.control.GetStyleAt(caretPos - 1)

        if(braceAtCaret<0):
            charAfter = self.control.GetCharAt(caretPos)
            styleAfter = self.control.GetStyleAt(caretPos)
            if(charAfter and chr(charAfter) in  "[](){}" and styleAfter == stc.STC_P_OPERATOR):
                braceAtCaret = caretPos
        if(braceAtCaret>=0):
            braceOpposite = self.control.BraceMatch(braceAtCaret)

        if(braceAtCaret!=-1 and braceOpposite==-1):
            self.control.BraceBadLight(braceAtCaret)
        else:
            self.control.BraceHighlight(braceAtCaret,braceOpposite)

    def OnThemeChange(self,e):
        if self.theme_number == 1:
            self.theme_number = 2
            self.ParseSettings("styling_2.xml")
            self.SetStyling()
        elif self.theme_number == 2:
            self.theme_number=1
            self.ParseSettings("styling.xml")
            self.SetStyling()
            
    def ParseSettings(self, settings_file):
    # Open XML document using minidom parser
        DOMTree = xml.dom.minidom.parse(settings_file)
        collection = DOMTree.documentElement # Root element
        
    # Get all the styles in the collection
        styles = collection.getElementsByTagName("style")
        for s in styles:
            item = s.getElementsByTagName("item")[0].childNodes[0].data
            color = s.getElementsByTagName("color")[0].childNodes[0].data
            side = s.getElementsByTagName("side")[0].childNodes[0].data
            sType = s.getAttribute("type")
            if sType == "normal":
                if side == "Back": # background
                    self.normalStylesBack[str(item)] = str(color)
                else:
                    self.normalStylesFore[str(item)] = str(color)
            elif sType == "python":
                if side == "Back":
                    self.pythonStylesBack[str(item)] = str(color)
                else:
                    self.pythonStylesFore[str(item)] = str(color)


            
app = wx.App()
frame = MainWindow(None,"SHARP - Text Editor")
app.MainLoop()
