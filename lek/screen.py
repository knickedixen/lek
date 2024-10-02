import termios
import tty
from lek import editorstate
import sys
import atexit
import re
import math

class Const:
    rightBreak = 3
    leftBreak = 5

class VT:
    clear = b'\x1b[J'
    resetPos = b'\x1b[H'

def setup():
    orig_stdout_settings = termios.tcgetattr(sys.stdout)

    # Make sure to always reset settings no matter what
    atexit.register(termios.tcsetattr, sys.stdout, termios.TCSADRAIN, orig_stdout_settings)

    new_settings = termios.tcgetattr(sys.stdout)
    new_settings[0] = new_settings[0] & ~(termios.BRKINT |termios.ICRNL |termios.INPCK | termios.ISTRIP | termios.IXON)
    new_settings[1] = new_settings[1] & ~(termios.OPOST)
    new_settings[2] = new_settings[2] & ~(termios.CS8)
    new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.IEXTEN | termios.ICANON | termios.ISIG)

    termios.tcsetattr(sys.stdout, termios.TCSAFLUSH, new_settings)
    
def reset():
    # Turn on post processing before error message is printed
    settings = termios.tcgetattr(sys.stdout)
    settings[1] = settings[1] | termios.OPOST
    termios.tcsetattr(sys.stdout, termios.TCSAFLUSH, settings)
    
    sys.stdout.buffer.write(VT.resetPos)
    sys.stdout.buffer.write(VT.clear)

def makeCursorPosString(x, y):
    return "\x1b[%s;%sH" % (x, y)

def getCursorPos():
    sys.stdout.write("\x1b[6n")
    sys.stdout.flush()
    
    response = ""
    while not (response := response + sys.stdin.read(1)).endswith('R'):
        True
    match = re.match(r".*\[(?P<y>\d*);(?P<x>\d*)R", response)

    return (match.group("x"), match.group("y"))

def refreshScreen(state):
    sys.stdout.buffer.write(VT.resetPos)
    sys.stdout.buffer.write(VT.clear)
    
    dashLine = "-" * state.windowX + "\n\r"
    
    screenStr = ""
    screenStr += dashLine # first line is untouchable?
    
    offset = 6
    pageSize = state.windowX - offset
    page = math.floor(state.cursorX/pageSize)
    frX = page*pageSize
    if page > 0:
        frX = frX - int(offset/2)
    toX = frX + state.windowX
    
    frY = state.topLine
    toY = frY + state.editorY
    
    for y in range(frY, toY):
        if len(state.rows) > y:
            row = state.rows[y]
            line = row.chars
            line = line[frX:toX]
            if len(line) == 0:
                line = " "

            if state.selectMode:
                line = getSelectFormattedLine(line, y, state)
            screenStr += line 
        else:
            screenStr += "~"
        if y < toY:
            screenStr += "\n\r"
    
    screenStr += dashLine
    
    if state.command:
        commandLine = state.command + ": " + state.commandInput
    else:
        commandLine = state.info
    screenStr += commandLine + "\n\r"

    screenStr += '\033[94m' + "ln: " + str(state.cursorY) + " col: " + str(state.cursorX) + '\033[0m' 
    screenStr += " | " + '\033[96m' + state.filePath + '\033[0m'
    screenStr += " | " + str(state.key)
    #screenStr += " | topLine: " + str(state.topLine)
    
    cursorX = state.cursorX - frX
    cursorY = state.cursorY - state.topLine
    if state.command:
        cursorY = state.editorY + 1
        cursorX = len(commandLine)
    screenStr += makeCursorPosString(cursorY + 1, cursorX + 1)
    
    print(screenStr)

def getSelectFormattedLine(line, y, state):
    bg = '\033[100m' 
    reset = '\033[0m'
    
    selectStartY = min(state.selectStartY, state.cursorY)
    selectStopY = max(state.selectStartY, state.cursorY)
    if state.selectStartY < state.cursorY:
        selectStartX = state.selectStartX
        selectStopX = state.cursorX
    elif state.selectStartY == state.cursorY:
        selectStartX = min(state.selectStartX, state.cursorX)
        selectStopX = max(state.selectStartX, state.cursorX)
        selectStopX += len(bg)
    else:
        selectStartX = state.cursorX
        selectStopX = state.selectStartX

    if selectStartY == y:
        line = line[:selectStartX] + bg + line[selectStartX:]
    if selectStopY == y:
        line = line[:selectStopX] + reset + line[selectStopX:]

    return line
