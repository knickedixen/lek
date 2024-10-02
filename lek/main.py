import os
import atexit
import termios
import sys
import screen
import editor
import file
import editorstate

#def run():
screen.setup()

state = editorstate.EditorState()
editor.setup(state)

if len(sys.argv) > 1:
    filePath = sys.argv[1]
    if os.path.isfile(filePath):
        file.openFile(filePath, state)

try:
    while True:
        editor.setSize(state)
        screen.refreshScreen(state)
        editor.processKeypress(state)
finally:
    screen.reset()

#run()

