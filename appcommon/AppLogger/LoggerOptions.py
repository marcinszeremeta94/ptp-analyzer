from enum import Enum

class LogsSeverity(Enum):
    Debug = 1
    Regular = 0
    WaningsAndErrors = 2
    ErrorsOnly = 3
    NoLogs = 4
    InfoOnly = 5


class PrintOption(Enum):
    NoPrints = 0
    PrintToConsole = 1