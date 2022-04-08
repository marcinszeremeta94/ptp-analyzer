from enum import Enum
import os
import datetime as d

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

class Logger:
    class LogType(Enum):
        info    = 0
        debug   = 1
        warning = 2
        error   = 3
        newline = 4
    
    LOGS_SEPARATOR = '\n'
    INF_PREAMPULE = 'INF::'
    DBG_PREAMPULE = 'DBG::'
    WRN_PREAMPULE = 'WRN::'
    ERR_PREAMPULE = 'ERR::'
    
    severity = LogsSeverity.Regular
    printOptions = PrintOption.NoPrints
    valErrorRaise = False
    logFileName = 'def.log'

    def __init__(self, logFileName='def', severity=LogsSeverity.Regular, printOptions=PrintOption.PrintToConsole, valErrorRaise=False):
        self.severity = severity
        self.logFileName = logFileName + '.log'
        self.logDirAndName = self._prepare_path()
        self.printOptions = printOptions
        self.valErrorRaise = valErrorRaise
        LOGS_TITLE = f"STARTED::{d.datetime.now()}"
        print(self.logDirAndName)
        with open(self.logDirAndName, 'w') as self.__logFile:
            self._printStrict(LOGS_TITLE)
            self.__logFile.write(LOGS_TITLE + self.LOGS_SEPARATOR)

    def __del__(self):
        self.__logFile.close()
        
    def _writeToLogFile(self, inString):
        with open(self.logDirAndName, 'a') as self.__logFile:
            self.__logFile.write(inString + self.LOGS_SEPARATOR)

    def info(self, inString):
        self._loggerCall(self.LogType.info, inString)
                
    def debug(self, inString):
        self._loggerCall(self.LogType.debug, inString)
            
    def warning(self, inString):
        self._loggerCall(self.LogType.warning, inString)
                
    def error(self, inString):
        self._loggerCall(self.LogType.error, inString)        
        
    def new_line(self):
        self._loggerCall(self.LogType.newline) 
     
    def _loggerCall(self, logType, inString = ''):
        if self._isLogTypeOutOfSeverity(logType) or not self._isStrType(inString):
            return
        preamble = self._getLogTypePreamble(logType)
        logString = preamble + inString
        self._writeToLogFile(logString)
        self._printStrict(logString)
    
    def _getLogTypePreamble(self, logType):
        if logType == self.LogType.info:
            return self.INF_PREAMPULE
        elif logType == self.LogType.debug:
            return self.DBG_PREAMPULE
        elif logType == self.LogType.warning:
            return self.WRN_PREAMPULE
        elif logType == self.LogType.error:
            return self.ERR_PREAMPULE
        else: return ''    
        
    def _isLogTypeOutOfSeverity(self, logType):
        if logType == self.LogType.info:
            if not self._isInfoSeverityScope():
                return True
        elif logType == self.LogType.debug:
            if not self._isDebugSeverityScope():
                return True
        elif logType == self.LogType.warning:
            if not self._isWarningSeverityScope():
                return True
        elif logType == self.LogType.error:
            if not self._isErrorSeverityScope():
                return True
                
               
    def _isInfoSeverityScope(self):
        if self.severity == LogsSeverity.Regular or self.severity == LogsSeverity.Debug or \
            self.severity == LogsSeverity.InfoOnly:
            return True
        else:
            return False
    
    def _isDebugSeverityScope(self):
        if self.severity == LogsSeverity.Debug:
            return True
        else:
            return False   
        
    def _isWarningSeverityScope(self):
        if self.severity != LogsSeverity.NoLogs and self.severity != LogsSeverity.ErrorsOnly and \
            self.severity != LogsSeverity.InfoOnly: 
            return True
        else:
            return False     
        
    def _isErrorSeverityScope(self):
        if self.severity != LogsSeverity and self.severity != LogsSeverity.InfoOnly:
            return True
        else:
            return False     
        
    def _isStrType(self, string):
        if isinstance(string, str):
            return True
        else:
            if self._isErrorSeverityScope():
                self._printStrict(self._LoggerTypeError())
                self._writeToLogFile(self._LoggerTypeError())
            if self.valErrorRaise:
                raise
            return False

    def _prepare_path(self):
        p = os.path.dirname(__file__)
        if os.name == 'nt':
            p = p[:p.rfind('\\')] + '\\reports\\' + self.logFileName
        else:
            p = p[:p.rfind('/')] + '/reports/' + self.logFileName 
        return p
    
    def _printStrict(self, string):
        if self.printOptions == PrintOption.PrintToConsole:
            print(string)

    def _LoggerTypeError(self):
        return "{0}{1}: Passed variable is not a string!".format(self.ERR_PREAMPULE, self._LoggerTypeError.__name__)
