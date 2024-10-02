import sys
from lek import editorstate
from lek import screen
from lek import file
import os.path
import select

class Command:
    saveAs = "Save As"
    open = "Open"
    
class Chars:
    ctrlQ = b'\x11'
    ctrlS = b'\x13'
    ctrlO = b'\x0f'
    ctrlZ = b'\x1a'
    ctrlY = b'\x19'
    shiftUp = b'\x1b[1;2A'
    shiftDown = b'\x1b[1;2B'
    shiftLeft = b'\x1b[1;2D'
    shiftRight = b'\x1b[1;2C'
    shiftEnd = b'\x1b[1;2F'
    shiftHome = b'\x1b[1;2H'
    arrowUp = b'\x1b[A'
    arrowDown = b'\x1b[B'
    arrowLeft = b'\x1b[D'
    arrowRight = b'\x1b[C'
    carriageReturn = b'\r'
    newLine = b'\n'
    delete = b'\x1b[3~'
    pageUp = b'\x1b[5~'
    pageDown = b'\x1b[6~'
    home = b'\x1b[H'
    end = b'\x1b[F'
    insert = b'\x1b[2~'
    backspace = b'\x7f'

def setup(state):
    setSize(state)
    state.rows.append(editorstate.Row())

def setSize(state):
    terminalSize = os.get_terminal_size()
    editorY = terminalSize.lines - 4
    editorX = terminalSize.columns - 1
    
    state.windowY = terminalSize.lines
    state.windowX = terminalSize.columns
    state.editorY = editorY
    state.editorX = editorX

def readKeyPress(state):
    # 1 secound timeout
    i,o,e = select.select([sys.stdin],[],[],1)
    if not i:
        return False 

    key = bytearray()
    key.extend(readOnce())
    if key[0:1] == b'\x1b':
        key.extend(readOnce())
        if key[1:2] == b'[':
            key.extend(readOnce())
            if 47 < key[2] and key[2] < 58:
                key.extend(readOnce())
                if key[3] == 59:
                    key.extend(readOnce())
                    key.extend(readOnce())
    state.key = key
    return True

def readOnce():
    return sys.stdin.buffer.read(1)

def commitCommandMode(state):
    if state.command == Command.open:
        if os.path.isfile(state.commandInput):
            file.openFile(state.commandInput, state)
        else:
            state.info = "'" + state.commandInput + "' is not a file!"
    elif state.command == Command.saveAs:
        if state.commandInput:
            state.filePath = state.commandInput
            file.saveFile(state)
    state.command = ""
    state.commandInput = ""

def handleCommandMode(state):
    match state.key:
        case Chars.carriageReturn | Chars.newLine:
            commitCommandMode(state)
        case Chars.backspace:
            state.commandInput = "" # TODO
        case Chars.ctrlQ:
            exit(0)
        case _:
            if ord(state.key) < 31:
                # Skip all other control characters
                return
            translatedKey = state.key.decode("utf-8")
            state.commandInput += translatedKey

def enterCommandMode(command, state):
    state.command = command
    state.commandInput = ""

def enterSelectMode(state):
    if not state.selectMode:
        state.selectMode = True
        state.selectStartX = state.cursorX
        state.selectStartY = state.cursorY

def exitSelectMode(state):
    state.selectMode = False
    
def processKeypress(state):
    if not readKeyPress(state):
        return

    if state.command:
        handleCommandMode(state)
        return

    state.info = ""

    match state.key:
        case Chars.arrowUp:
            exitSelectMode(state)
            cursorUp(state)
        case Chars.arrowDown:
            exitSelectMode(state)
            cursorDown(state)
        case Chars.arrowLeft:
            exitSelectMode(state)
            cursorLeft(state)
        case Chars.arrowRight:
            exitSelectMode(state)
            cursorRight(state)
        case Chars.ctrlS:
            if state.filePath:
                file.saveFile(state)
            else:
                enterCommandMode(Command.saveAs, state)
        case Chars.ctrlO:
            enterCommandMode(Command.open, state)
        case Chars.ctrlQ:
            exit(0)
        case Chars.carriageReturn | Chars.newLine:
            newLine(state)
        case Chars.delete:
            delete(state)
        case Chars.backspace:
            backspace(state)
        case Chars.end:
            exitSelectMode(state)
            end(state)
        case Chars.home:
            exitSelectMode(state)
            home(state)
        case Chars.shiftUp:
            enterSelectMode(state)
            cursorUp(state)
        case Chars.shiftDown:
            enterSelectMode(state)
            cursorDown(state)
        case Chars.shiftLeft:
            enterSelectMode(state)
            cursorLeft(state)
        case Chars.shiftRight:
            enterSelectMode(state)
            cursorRight(state)
        case Chars.shiftEnd:
            enterSelectMode(state)
            end(state)
        case Chars.shiftHome:
            enterSelectMode(state)
            home(state)
            return
        case Chars.pageUp | Chars.pageDown | Chars.insert:
            # crash on purpose
            print(state.cursorX[2])
        case _:
            if ord(state.key) < 31:
                # Skip all other control characters
                return
            translatedKey = state.key.decode("utf-8")
            appendAtCursor(translatedKey, state)

def newLine(state):
    line = state.rows[state.cursorY].chars
    oldLine = line[:state.cursorX]
    state.rows[state.cursorY].chars = oldLine
    state.rows[state.cursorY].length = len(oldLine)
    newLine = line[state.cursorX:]
    state.rows.insert(state.cursorY + 1, editorstate.Row(newLine, len(newLine)))
    state.cursorX = 0
    state.wishorX = 0
    cursorDown(state)

def delete(state):
    if state.cursorX == state.rows[state.cursorY].length and state.cursorY < len(state.rows) - 1:
        nextRow = state.rows.pop(state.cursorY + 1)
        state.rows[state.cursorY].chars += nextRow.chars
        state.rows[state.cursorY].length = len(state.rows[state.cursorY].chars)
    elif state.cursorX < state.rows[state.cursorY].length:
        line = state.rows[state.cursorY].chars
        newLine = line[:state.cursorX] + line[state.cursorX + 1:]
        state.rows[state.cursorY].chars = newLine
        state.rows[state.cursorY].length = len(newLine)

def deleteSelected(state):
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

    if selectStartY == selectStopY:
        line = state.rows[selectStartY].chars
        newLine = line[:selectStartX] + line[selectStopX:]
        state.rows[selectStartY].chars = newLine
        state.rows[selectStartY].length = len(newLine)
    else:
        startLine = state.rows[selectStartY].chars
        stopLine = state.rows[selectStopY].chars
        newStartLine = startLine[:selectStartX] + stopLine[selectStopX:]
        state.rows = state.rows[:selectStartY] + state.rows[selectStopY:]
        state.rows[selectStartY].chars = newStartLine
        state.rows[selectStartY].length = len(newStartLine)
    state.cursorX = selectStartX
    state.cursorY = selectStartY
    exitSelectMode(state)

def backspace(state):
    if state.selectMode:
        deleteSelected(state)
        return
    if state.cursorX == 0:
        if state.cursorY > 0:
            upperLineLength = state.rows[state.cursorY -1].length
            row = state.rows.pop(state.cursorY)
            state.rows[state.cursorY -1].chars += row.chars
            state.rows[state.cursorY -1].length = len(state.rows[state.cursorY -1].chars)
            state.wishorX = upperLineLength
            cursorUp(state)
    else:
        line = state.rows[state.cursorY].chars
        newLine = line[:state.cursorX -1] + line[state.cursorX:]
        state.rows[state.cursorY].chars = newLine
        state.rows[state.cursorY].length = len(newLine)
        cursorLeft(state)

def appendAtCursor(key, state):
    line = state.rows[state.cursorY].chars
    newLine = line[:state.cursorX] + key + line[state.cursorX:]
    state.rows[state.cursorY].chars = newLine
    state.rows[state.cursorY].length = len(newLine)
    cursorRight(state)

def cursorRight(state):
    if state.cursorX < state.rows[state.cursorY].length:
        state.cursorX += 1
        state.wishorX = state.cursorX
    elif isCursorAtLastLine(state):
        cursorDown(state)
        cursorStartOfLine(state)

def cursorLeft(state):
    if state.cursorX > 0:
        state.cursorX -= 1
        state.wishorX = state.cursorX
    elif state.cursorY > 0:
        cursorUp(state)
        cursorEndOfLine(state)

def cursorEndOfLine(state):
    state.cursorX = state.rows[state.cursorY].length

def cursorStartOfLine(state):
    state.cursorX = 0

def cursorUp(state):
    if state.cursorY > 0:
        state.cursorY -= 1
        lineChanged(state)
    else:
        cursorStartOfLine(state)

    if state.cursorY < state.topLine:
        state.topLine = state.cursorY

def isCursorAtLastLine(state):
    return state.cursorY < (len(state.rows) - 1)

def cursorDown(state):
    if isCursorAtLastLine(state):
        state.cursorY += 1
        lineChanged(state)
    else:
        cursorEndOfLine(state)
    
    if state.cursorY >= state.editorY:
        state.topLine = (state.cursorY - state.editorY) + 1

def lineChanged(state):
    lineLength = state.rows[state.cursorY].length
    if state.cursorX > lineLength or state.wishorX > lineLength:
        state.cursorX = lineLength
    else:
        state.cursorX = state.wishorX


def end(state):
    state.cursorX = state.rows[state.cursorY].length

def home(state):
    state.cursorX = 0

