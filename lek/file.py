from lek import editorstate

def openFile(path, state):
    f = open(path)
    if not f:
        return
    state.rows = []
    state.cursorX = 0
    state.cursorY = 0
    state.wishorX = 0

    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip("\n\r")
        row = editorstate.Row(line, len(line))
        state.rows.append(row)

    if len(state.rows) < 1:
        state.rows.append(editorstate.Row())

    f.close()
    state.filePath = path
    state.info = "Opened '" + state.filePath + "'"

def saveFile(state):
    f = open(state.filePath, "w")
    if not f:
        return
    for row in state.rows:
        f.write(row.chars + "\n")
    state.info = "Saved!"

