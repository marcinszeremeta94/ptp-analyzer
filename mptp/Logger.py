from enum import Enum
import os
import time
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
        info = 0
        debug = 1
        warning = 2
        error = 3
        newline = 4
        msg_timing = 5
        banner_small = 6
        banner_large = 7

    _log_type_allowed_in_no_logs = ()
    _log_type_common = (LogType.banner_large, LogType.banner_small,
                        LogType.msg_timing, LogType.newline)

    _log_type_allowed_in_error_only = _log_type_common + (LogType.error,)
    _log_type_allowed_in_info_only = _log_type_common + \
        (LogType.error, LogType.info)
    _log_type_allowed_in_waring_and_errors = _log_type_common + \
        (LogType.error, LogType.warning,)
    _log_type_allowed_in_regular = _log_type_common + \
        (LogType.error, LogType.warning, LogType.info)
    _log_type_allowed_in_debug = _log_type_common + \
        (LogType.error, LogType.warning, LogType.info, LogType.debug)

    LOGS_SEPARATOR = '\n'
    INF_PREAMPULE = '[INF] '
    DBG_PREAMPULE = '[DBG] '
    WRN_PREAMPULE = '[WRN] '
    ERR_PREAMPULE = '[ERR] '
    TIME_PREAMPULE = '[TIME] '

    def __init__(self, log_file_name='def', severity=LogsSeverity.Regular, print_options=PrintOption.PrintToConsole, val_error_raise=False):
        self.severity = severity
        self.print_options = print_options
        self.val_error_raise = val_error_raise
        self._log_file_name = log_file_name + '.log'
        self._log_dir_and_name = self._prepare_path()
        LOGS_TITLE = f'Started at: {d.datetime.now()}'
        print(f'Log file location: {self._log_dir_and_name}')
        with open(self._log_dir_and_name, 'w') as self._logFile:
            self._print_strict(LOGS_TITLE + self.LOGS_SEPARATOR)
            self._logFile.write(LOGS_TITLE + self.LOGS_SEPARATOR)

    def _write_to_log_file(self, in_string):
        with open(self._log_dir_and_name, 'a') as self._logFile:
            self._logFile.write(in_string + self.LOGS_SEPARATOR)

    def info(self, in_string):
        self._loggerCall(self.LogType.info, in_string)

    def debug(self, in_string):
        self._loggerCall(self.LogType.debug, in_string)

    def warning(self, in_string):
        self._loggerCall(self.LogType.warning, in_string)

    def error(self, in_string):
        self._loggerCall(self.LogType.error, in_string)

    def msg_timing(self, msg, time_offset):
        self._loggerCall(self.LogType.msg_timing,
                         self._get_str_for_timing_log(msg, time_offset))
    
    def banner_small(self, in_string):
        pass
    
    def banner_large(self, in_string):
        pass
        
    def new_line(self):
        self._loggerCall(self.LogType.newline)

    def _loggerCall(self, log_type, in_string=''):
        if self._is_in_severity(log_type) and self._is_str(in_string):
            preamble = self._get_log_preamble(log_type)
            log_str = preamble + in_string
            self._write_to_log_file(log_str)
            self._print_strict(log_str)

    def _get_log_preamble(self, logType):
        if logType == self.LogType.info:
            return self.INF_PREAMPULE
        elif logType == self.LogType.debug:
            return self.DBG_PREAMPULE
        elif logType == self.LogType.warning:
            return self.WRN_PREAMPULE
        elif logType == self.LogType.error:
            return self.ERR_PREAMPULE
        elif logType == self.LogType.msg_timing:
            return self.TIME_PREAMPULE
        else:
            return ''

    def _is_in_severity(self, log_type):
        if self.severity == LogsSeverity.NoLogs:
            if log_type in self._log_type_allowed_in_no_logs:
                return True
        elif self.severity == LogsSeverity.ErrorsOnly:
            if log_type in self._log_type_allowed_in_error_only:
                return True
        elif self.severity == LogsSeverity.WaningsAndErrors:
            if log_type in self._log_type_allowed_in_waring_and_errors:
                return True
        elif self.severity == LogsSeverity.InfoOnly:
            if log_type in self._log_type_allowed_in_info_only:
                return True
        elif self.severity == LogsSeverity.Regular:
            if log_type in self._log_type_allowed_in_regular:
                return True
        elif self.severity == LogsSeverity.Debug:
            if log_type in self._log_type_allowed_in_debug:
                return True
        return False

    def _is_str(self, string):
        if isinstance(string, str):
            return True
        else:
            self._print_strict(self._logger_type_error())
            if self.val_error_raise:
                raise ValueError
            return False

    def _get_str_for_timing_log(self, msg, time_offset):
        t = time.strftime('%H:%M:%S', time.localtime(msg.time))
        return f'Capture time: {t},\tCapture offset: {msg.time-time_offset:.9f},\tSequence ID: {msg.sequenceId}'

    def _prepare_path(self):
        p = os.path.dirname(__file__)
        if os.name == 'nt':
            p = p[:p.rfind('\\')] + '\\reports\\' + self._log_file_name
        else:
            p = p[:p.rfind('/')] + '/reports/' + self._log_file_name
        return p

    def _print_strict(self, string):
        if self.print_options == PrintOption.PrintToConsole:
            print(string)

    def _logger_type_error(self):
        return "{0}{1}: Passed variable is not a string!".format(self.ERR_PREAMPULE, self._logger_type_error.__name__)
