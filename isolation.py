# -*- coding: utf-8
import wx
import wx.lib.colourselect as csel
import threading
import colorsys
import string

GEAR_ICON = 'gear_icon.png'
START_ICON = 'start_icon.png'
DEATH_IMAGE = 'skull.png'

ALPHABET = list(string.lowercase)


## ------------ CLASS FOR INDIVIDUAL GAME CELLS ------------##
class GameCell(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kwargs)
        self.SetBackgroundColour('black')
        self.destroyed = False
        self.parent = parent
        self.size = self.GetSize()
        self.enabled = True

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.base = wx.Panel(self, wx.ID_ANY, style=wx.BORDER_NONE)
        self.base.SetBackgroundColour('white')

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        #self.beeper = wx.Panel(self.base, wx.ID_ANY, size=(self.size[0]/8, self.size[1]/8), style=wx.BORDER_NONE)
        self.beeper = wx.StaticText(self.base, wx.ID_ANY)
        self.beeper.Hide()
        # fallback to ASCII from UTF-8
        try: self.SetLetter('•')
        except: self.SetLetter('*')
        bmp = wx.Image(DEATH_IMAGE).Scale(self.size[0]*0.8, self.size[1]*0.8, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        self.death_bmp = wx.StaticBitmap(self.base, wx.ID_ANY, bmp, size=(50, 50))
        self.death_bmp.Hide()
        vsizer.Add(self.beeper, 0, wx.ALIGN_CENTRE, 0)
        vsizer.Add(self.death_bmp, 0, wx.ALIGN_CENTRE, 0)
        hsizer.Add(vsizer, 1, wx.ALIGN_CENTRE, 0)

        self.base.SetSizer(hsizer)

        sizer.Add(self.base, 1, wx.EXPAND|wx.ALL, 2)
        self.SetSizer(sizer)
        self.Layout()
        # Click Bindings (Redirect EVT_LEFT_DOWN's to the cell object)
        self.base.Bind(wx.EVT_LEFT_DOWN, self.ElementClick)
        self.beeper.Bind(wx.EVT_LEFT_DOWN, self.ElementClick)

    def ElementClick(self, event):
        if self.enabled:
            event = wx.CommandEvent(wx.EVT_LEFT_DOWN.typeId, self.GetId())
            event.SetEventObject(self)
            wx.PostEvent(self, event)

    def SetLetter(self, letter, fontsize=32):
        self.beeper.SetLabel(letter)
        self.beeper.SetFont(wx.Font(fontsize, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD, False, 'Helvetica'))
        self.letter = letter

    def EnableCell(self, enable=True):
        self.enabled = enable

    def DisableCell(self):
        self.enabled = False

    def ShowDeathBitmap(self):
        self.beeper.Hide()
        self.death_bmp.Show()
        self.Layout()

    def HideDeathBitmap(self):
        self.death_bmp.Hide()
        self.Layout()

    def Greyscale(self, event=None):
        bgr = self.base.GetBackgroundColour()
        #gval = (0.21*bgr[0] + 0.71*bgr[1] + 0.07*bgr[2]) # lumosity method (found to be too bright)
        gval = (bgr[0] + bgr[1] + bgr[2]) / 3
        greyscale = (gval, gval, gval)
        if bgr != 'white':
            self.base.SetBackgroundColour(greyscale)
        else:
            self.base.SetBackgroundColour('#EEEEEE')

    def GetLocation(self):
        return tuple([int(x) for x in self.GetName().split('-')])

    def Adjacents(self):
        adj = []
        key = self.GetLocation()
        tests = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for t in tests:
            new_key = (key[0]+t[0], key[1]+t[1])
            if new_key in self.parent.cells:
                cell = self.parent.cells[new_key]
                if not cell.destroyed and cell != self.parent.piece[0] and cell != self.parent.piece[1]:
                    adj.append(new_key)
        return adj

    def IsIsolated(self):
        if self.Adjacents():
            return False
        else:
            return True


## ------------ GAME BOARD CLASS (INCLUDES TOP PANEL) ------------##
class GameBoard(wx.Panel):
    def __init__(self, parent, max_size, conf, border):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.SetFocus()
        self.SetBackgroundColour('black')
        self.conf = conf
        self.parent = parent
        self.player = 0
        self.type = 0
        self.game_over = False
        self.piece = {}
        self.old_piece = {}
        self.cells = {}
        x_offset = 0
        y_offset = 60
        self.timer_value = conf['timer']

        self.InitMath(max_size, x_offset, y_offset, True)

        ## TOP PANEL (GAME INFO AND NEWGAME/CONF BUTTON) ##
        self.toppanel = wx.Panel(self, wx.ID_ANY, (3, 3), (self.size[0]-6, y_offset-5))
        self.toppanel.SetBackgroundColour('white')
        topsizer = wx.BoxSizer(wx.HORIZONTAL)

        font = wx.Font(32, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Helvetica')
        self.turn_text = wx.StaticText(self.toppanel, wx.ID_ANY, 'Player 1')
        self.turn_text.SetFont(font)

        if self.conf['timer'][0]:
            self.timer_text = wx.StaticText(self.toppanel, wx.ID_ANY, )
            self.timer_text.SetFont(font)

            turn_timer_id = wx.ID_ANY
            self.timer = wx.Timer(self, turn_timer_id)
            wx.EVT_TIMER(self, turn_timer_id, self.OnTurnTimer)
            self.SetTimer(str(self.conf['timer'][1]), self.conf['colour'][0])

        bmp = wx.Bitmap(START_ICON, wx.BITMAP_TYPE_ANY)
        self.newgame_button = wx.BitmapButton(self.toppanel, wx.ID_ANY, bmp, size=(40, 40), style=wx.BU_AUTODRAW|wx.NO_BORDER)
        self.newgame_button.Bind(wx.EVT_BUTTON, self.parent.NewGame)

        topsizer.Add(self.turn_text, 0, wx.TOP|wx.LEFT, 8)
        if self.conf['timer'][0]:
            topsizer.AddStretchSpacer(1)
            topsizer.Add(self.timer_text, 0, wx.TOP, 8)
        topsizer.AddStretchSpacer(1)
        topsizer.Add(self.newgame_button, 0, wx.TOP|wx.RIGHT, 8)

        self.toppanel.SetSizer(topsizer)
        self.toppanel.Layout()

        ## GAME BOARD CONTRUCTION (CELL ADDITION LOOP)
        for i in range(self.conf['width']*self.conf['height']):
            if i%self.conf['width'] == 0:
                col = 0
            row = i/self.conf['width']
            x = (self.cell_width*col)+self.x_offset
            y = (self.cell_height*row)+self.y_offset
            self.cells[(row, col)] = cell = GameCell(self, pos=(x, y), size=(self.cell_width, 
                    self.cell_height), style=wx.BORDER_NONE, name='-'.join((str(row), str(col))))
            cell.Bind(wx.EVT_LEFT_DOWN, self.OnCellClick)
            col += 1

            # do alphabet
            if self.conf['width'] <= 5 and self.conf['height'] <= 5:
                letter = ALPHABET[i]
                cell.SetLetter(letter, 22)

        self.old_piece[0] = self.piece[0] = self.cells[(0, conf['width']/2)]
        if self.conf['width']%2==0:
            tup = (conf['height']-1, conf['width']/2-1)
        else: 
            tup = (conf['height']-1, conf['width']/2)
        self.old_piece[1] = self.piece[1] = self.cells[tup]
        
        self.Layout()
        self.GameUpdate()

        if self.conf['width'] <= 5 and self.conf['height'] <= 5:
            self.Bind(wx.EVT_CHAR_HOOK, self.onKey)

    def OnTurnTimer(self, event):
        self.timer_value -= 1
        if self.timer_value < 0:
            self.SwitchTurn()
            self.GameUpdate()
        self.timer_text.SetLabel(str(self.timer_value))

    def SetTimer(self, start, colour):
        self.timer.Stop()
        self.timer_value = int(start)
        self.timer_text.SetLabel(str(start))
        self.timer_text.SetForegroundColour(colour)
        self.timer.Start(1000)


    def onKey(self, event):
        #if evt.GetKeyCode() == wx.WXK_DOWN:
        #    print "Down key pressed"
        if 65 <= event.GetKeyCode() <= 90:
            letter = ALPHABET[event.GetKeyCode()-65]
            self.OnCellLetter(letter)
        else:
            event.Skip()

    def InitMath(self, max_size, x_off=0, y_off=0, resize_parent=False):
        self.x_offset = x_off
        self.y_offset = y_off
        self.size = (max_size[0]+self.x_offset, max_size[1]+self.y_offset)
        self.cell_width = (self.size[0] / float(self.conf['width']))
        self.cell_height = (self.size[1] / float(self.conf['height']))
        if resize_parent:
            size = (self.size[0]+self.x_offset, self.size[1]+self.y_offset+22)
            self.parent.SetSize(size)
            self.parent.SetMinSize(size)

    def SwitchTurn(self):
        self.player = int(not self.player)
        self.type = 0

    def SetTurnText(self, custom=None):
        if custom:
            self.turn_text.SetLabel(custom[0])
            self.turn_text.SetForegroundColour(custom[1])
        else:
            self.turn_text.SetLabel(self.conf['name'][self.player]+"'s Turn")
            self.turn_text.SetForegroundColour(self.conf['colour'][self.player])
        self.toppanel.Layout()

    def ShowBeepers(self, tiles, colour):
        for t in tiles:
            #t.beeper.SetBackgroundColour(colour)
            t.beeper.SetForegroundColour(colour)
            t.beeper.Show()
            t.Layout()

    def HideBeepers(self, tiles):
        for t in tiles:
            t.beeper.Hide()
            t.Layout()

    def AvailableCells(self):
        cells = []
        for c in self.cells.itervalues():
            if not c.destroyed and c != self.piece[0] and c != self.piece[1]:
                cells.append(c)
        return cells

    def GameUpdate(self):
        self.SetTurnText()

        self.old_piece[0].base.SetBackgroundColour('white')
        self.old_piece[1].base.SetBackgroundColour('white')

        if self.type == 0:
            self.HideBeepers(self.cells.itervalues())
            adj_cells = [self.cells[adj] for adj in self.piece[self.player].Adjacents()]
            self.ShowBeepers(adj_cells, self.conf['colour'][self.player])
            if self.conf['timer'][0]:
                self.SetTimer(self.conf['timer'][1], self.conf['colour'][self.player])
        elif self.type == 1:
            self.ShowBeepers(self.AvailableCells(), 'black')

        self.old_piece[0] = self.piece[0]
        self.old_piece[1] = self.piece[1]
        self.piece[0].base.SetBackgroundColour(self.conf['colour'][0])
        self.piece[1].base.SetBackgroundColour(self.conf['colour'][1])

        for p in self.piece:
            if self.player == p and self.piece[p].IsIsolated():
                if not self.game_over:
                    self.FinishGame(int(not p), p)

        self.Refresh()

    def FinishGame(self, wid, lid):
        self.game_over = True
        if self.conf['timer'][0]:
            self.timer.Stop()
            self.timer_text.Hide()

        winner, loser = self.conf['name'][wid], self.conf['name'][lid]
        winner_colour = self.conf['colour'][wid]
                    
        self.SetTurnText(('%s wins!' %winner, winner_colour))

        for cell in self.cells.itervalues():
            cell.beeper.Hide()
            cell.DisableCell()
            if cell == self.piece[wid]:
                pass
            elif cell == self.piece[lid]:
                cell.Greyscale()
                cell.ShowDeathBitmap()
            else:
                cell.Greyscale()
        self.player = lid

    def OnCellClick(self, event):
        cell = event.GetEventObject()
        self.CellLogic(cell)

    def OnCellLetter(self, letter):
        cell = False
        for c in self.cells.itervalues():
            if c.letter == letter:
                cell = c
        if cell:
            self.CellLogic(cell)
        else:
            pass
            # PlaySound(BOOP_SOUND)

    def CellLogic(self, cell):
        if not cell.destroyed:
            if self.type == 0:
                if self.player == 0:
                    if cell.GetLocation() in self.piece[0].Adjacents():
                        self.piece[0] = self.cells[cell.GetLocation()]
                        self.type = int(not self.type)
                    else:
                        pass
                        # PlaySound(BOOP_SOUND)
                elif self.player == 1:
                    if cell.GetLocation() in self.piece[1].Adjacents():
                        self.piece[1] = self.cells[cell.GetLocation()]
                        self.type = int(not self.type)
                    else:
                        pass
                        # PlaySound(BOOP_SOUND)
            elif self.type == 1:
                if cell not in self.piece.itervalues():
                    cell.base.SetBackgroundColour('black')
                    cell.destroyed = True
                    self.SwitchTurn()
        self.GameUpdate()


## ------------ MAIN APP PANEL ------------##
class MainFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title='Isolation', pos=(-1, -1), size=(550, 550), style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__ (self, parent, id, title, pos, size, style)

        self.size = self.GetSize()
        self.default_size = size
        size = (size[0], size[1]+142)
        self.SetMinSize(size)
        self.SetSize(size)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        ## define menubar and menus
        self.menubar = wx.MenuBar(0)
        self.fileMenu = wx.Menu()
        ## add items to file Menu
        self.new_menuitem = wx.MenuItem(self.fileMenu, wx.ID_ANY, "New Game \tCtrl+N")
        self.quit_menuitem = wx.MenuItem(self.fileMenu, wx.ID_ANY, "Quit Isolation \tCtrl+Q")
        self.fileMenu.AppendItem(self.new_menuitem)
        self.fileMenu.AppendSeparator()
        self.fileMenu.AppendItem(self.quit_menuitem)
        # append menus to menubar
        self.menubar.Append(self.fileMenu, "File")
        # menu item bindings
        self.Bind(wx.EVT_MENU, self.NewGame, self.new_menuitem)
        self.Bind(wx.EVT_MENU, self.onClose, self.quit_menuitem)
        ## set menubar
        self.SetMenuBar(self.menubar)

        self.SetBackgroundColour('black')
        self.board = False
        self.startup = False
        self.conf = {
            'timer': [False, 15],
            'width': 5,
            'height': 7,
            'colour': {0: (0, 0, 255), 1: (255, 0, 0)},
            'name': {0: 'Connor', 1: 'Jack'},
        }

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainsizer)
        self.Layout()
        self.Centre(wx.BOTH)

        self.NewGame()
        self.Bind(wx.EVT_WINDOW_MODAL_DIALOG_CLOSED, self.NewGameClose)

    def onClose(self, event):
        self.Destroy()

    def NewGame(self, event=None):
        dialog = NewGameDialog(self, wx.ID_ANY, "New Game", size=(300, 230), style=wx.DEFAULT_DIALOG_STYLE)
        dialog.ShowWindowModal()

    def NewGameClose(self, event):
        """ Called when the NewGame Modal Window is closed
            Creates new board and plays startup sound if confirmed.
            If user canceled the window and self.startup is False, the app will quit. """
        dialog = event.GetDialog()
        return_code = event.GetReturnCode()
        if return_code == wx.ID_OK:
            if not self.startup:
                self.startup = True
            self.RedrawBoard(dialog.conf)
        elif return_code == wx.ID_CANCEL:
            if not self.startup:
                self.Destroy()
        dialog.Destroy()

    def RedrawBoard(self, conf):
        """ Destroys the current board (if exists) and creates a new one """
        if self.board:
            self.board.Destroy()
        # PlaySound(STARTUP_SOUND)
        self.board = GameBoard(self, self.size, conf, 1)
        self.mainsizer.Add(self.board, 1, wx.EXPAND, 0)
        self.Layout()
        self.Centre(wx.BOTH)



## ------------ NEW GAME DIALOG ------------##
class NewGameDialog(wx.Dialog):
    def __init__(self, parent, *args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.conf = self.parent.conf
        self.counter = {}

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.player1_label = wx.StaticText(self, wx.ID_ANY, 'Player 1:')
        self.player1_input = wx.TextCtrl(self, wx.ID_ANY, self.conf['name'][0], size=(110, -1))
        self.player1_input.Bind(wx.EVT_TEXT, lambda event, i=0: self.OnPlayerInput(event, i))
        self.player1_colour = csel.ColourSelect(self, wx.ID_ANY, colour=self.conf['colour'][0], size=(22, 22), style=wx.SIMPLE_BORDER)
        self.player1_colour.Bind(csel.EVT_COLOURSELECT, lambda event, i=0: self.OnPlayerColour(event, i))
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.player1_label, 0, wx.ALL, 5)
        box.Add(self.player1_input, 0, wx.ALL, 5)
        box.Add(self.player1_colour, 0, wx.ALL, 5)
        sizer.Add(box, 0, wx.EXPAND, 0)

        self.player2_label = wx.StaticText(self, wx.ID_ANY, 'Player 2:')
        self.player2_input = wx.TextCtrl(self, wx.ID_ANY, self.conf['name'][1], size=(110, -1))
        self.player2_input.Bind(wx.EVT_TEXT, lambda event, i=1: self.OnPlayerInput(event, i))
        self.player2_colour = csel.ColourSelect(self, wx.ID_ANY, colour=self.conf['colour'][1], size=(22, 22), style=wx.SIMPLE_BORDER)
        self.player2_colour.Bind(csel.EVT_COLOURSELECT, lambda event, i=1: self.OnPlayerColour(event, i))
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.player2_label, 0, wx.ALL, 5)
        box.Add(self.player2_input, 0, wx.ALL, 5)
        box.Add(self.player2_colour, 0, wx.ALL, 5)
        sizer.Add(box, 0, wx.EXPAND, 0)

        self.width_label = wx.StaticText(self, wx.ID_ANY, 'Width of Board')
        self.width_slider = wx.Slider(self, wx.ID_ANY, self.conf['width'], 3, 11)
        self.width_slider.Bind(wx.EVT_SCROLL_THUMBTRACK, lambda event, wh='width': self.OnSlider(event, wh))
        self.counter['width'] = wx.StaticText(self, wx.ID_ANY, str(self.conf['width']))
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.width_label, 0, wx.ALL, 5)
        box.AddStretchSpacer(1)
        box.Add(self.width_slider, 0, wx.ALL, 5)
        box.Add(self.counter['width'], 0, wx.ALL, 5)
        sizer.Add(box, 0, wx.EXPAND, 0)

        self.height_label = wx.StaticText(self, wx.ID_ANY, 'Height of Board')
        self.height_slider = wx.Slider(self, wx.ID_ANY, self.conf['height'], 3, 11)
        self.height_slider.Bind(wx.EVT_SCROLL_THUMBTRACK, lambda event, wh='height': self.OnSlider(event, wh))
        self.counter['height'] = wx.StaticText(self, wx.ID_ANY, str(self.conf['height']))
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.height_label, 0, wx.ALL, 5)
        box.AddStretchSpacer(1)
        box.Add(self.height_slider, 0, wx.ALL, 5)
        box.Add(self.counter['height'], 0, wx.ALL, 5)
        sizer.Add(box, 0, wx.EXPAND, 0)

        self.timer_checkbox = wx.CheckBox(self, wx.ID_ANY, label='Timer:')
        self.timer_checkbox.SetValue(self.conf['timer'][0])
        self.timer_input = wx.SpinCtrl(self, wx.ID_ANY, str(self.conf['timer'][1]), size=(60, -1))
        self.timer_checkbox.Bind(wx.EVT_CHECKBOX, self.OnTimer)
        self.timer_input.Bind(wx.EVT_TEXT, self.OnTimer)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.timer_checkbox, 0, wx.TOP|wx.LEFT, 6)
        box.Add(self.timer_input, 0, wx.BOTTOM|wx.LEFT, 5)
        sizer.Add(box, 0, wx.EXPAND, 0)

        sizer.AddStretchSpacer(1)

        line = wx.StaticLine(self, wx.ID_ANY, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTRE|wx.ALL, 2)

        self.SetSizer(sizer)
        self.Layout()

    def OnTimer(self, event):
        if self.timer_checkbox.IsChecked():
            self.conf['timer'][0] = True
        else:
            self.conf['timer'][0] = False
        self.conf['timer'][1] = self.timer_input.GetValue()

    def OnPlayerColour(self, event, i):
        self.conf['colour'][i] = event.GetValue()

    def OnPlayerInput(self, event, i):
        self.conf['name'][i] = event.GetEventObject().GetValue()

    def OnSlider(self, event, wh):
        val = event.GetEventObject().GetValue()
        self.conf[wh] = val
        self.counter[wh].SetLabel(str(val))
        self.Layout()



if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame(None)
    frame.Show()
    app.MainLoop()