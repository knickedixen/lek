from dataclasses import dataclass

@dataclass
class Row:
    chars: str = ""
    length: int = 0

class EditorState:
    topLine: int = 0
    windowY: int = 0
    windowX: int = 0
    editorY: int = 0
    cursorX: int = 0
    wishorX: int = 0
    cursorY: int = 0
    command: str = ""
    commandInput: str = ""
    selectMode: bool = False
    selectStartX: int = 0
    selectStartY: int = 0
    info: str = ""
    key: bytes = ''
    filePath: str = ""
    rows: Row = []

