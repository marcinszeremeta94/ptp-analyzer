from enum import Enum
import os
import time
import datetime as date


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
    _log_type_common = (LogType.banner_large, LogType.newline)

    _log_type_allowed_in_error_only = _log_type_common + (LogType.error,)
    _log_type_allowed_in_info_only = _log_type_common + \
        (LogType.error, LogType.info)
    _log_type_allowed_in_waring_and_errors = _log_type_common + \
        (LogType.error, LogType.warning, LogType.msg_timing, LogType.banner_small)
    _log_type_allowed_in_regular = _log_type_common + \
        (LogType.error, LogType.warning, LogType.info, LogType.msg_timing, LogType.banner_small)
    _log_type_allowed_in_debug = _log_type_common + \
        (LogType.error, LogType.warning, LogType.info, LogType.debug, LogType.msg_timing, LogType.banner_small)

    BANNER_LEN = 140
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
        self.log_dir_and_name = self._prepare_path()
        LOGS_TITLE = 'PTP ANALYSER'
        if self.severity is LogsSeverity.NoLogs:
            return
        with open(self.log_dir_and_name, 'w') as self._logFile:
            self.banner_small('--------------------------')
            self.banner_large(LOGS_TITLE)
            self.info(f'Started at: {date.datetime.now()}')

    def _write_to_log_file(self, in_string: str):
        with open(self.log_dir_and_name, 'a') as self._logFile:
            self._logFile.write(in_string + self.LOGS_SEPARATOR)

    def info(self, in_string: str):
        self._loggerCall(self.LogType.info, in_string)

    def debug(self, in_string: str):
        self._loggerCall(self.LogType.debug, in_string)

    def warning(self, in_string: str):
        self._loggerCall(self.LogType.warning, in_string)

    def error(self, in_string: str):
        self._loggerCall(self.LogType.error, in_string)

    def msg_timing(self, msg, time_offset=0):
        self._loggerCall(self.LogType.msg_timing,
                         self._get_str_for_timing_log(msg, time_offset))

    def banner_small(self, in_string: str):
        self._loggerCall(self.LogType.banner_small,
                         self._prepare_small_banner(in_string.upper()))

    def banner_large(self, in_string: str):
        self._loggerCall(self.LogType.banner_large,
                         self._prepare_large_banner(in_string.upper()))

    def new_line(self):
        self._loggerCall()

    def _loggerCall(self, log_type: LogType = LogType.newline, in_string=''):
        if self._is_in_severity(log_type) and self._is_str(in_string):
            preamble = self._get_log_preamble(log_type)
            log_str = preamble + in_string
            self._write_to_log_file(log_str)
            self._print_strict(log_str)

    def _get_log_preamble(self, log_type: LogType) -> str:
        if log_type == self.LogType.info:
            return self.INF_PREAMPULE
        elif log_type == self.LogType.debug:
            return self.DBG_PREAMPULE
        elif log_type == self.LogType.warning:
            return self.WRN_PREAMPULE
        elif log_type == self.LogType.error:
            return self.ERR_PREAMPULE
        elif log_type == self.LogType.msg_timing:
            return self.TIME_PREAMPULE
        else:
            return ''

    def _is_in_severity(self, log_type: LogsSeverity) -> bool:
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

    def _is_str(self, string) -> bool:
        if isinstance(string, str):
            return True
        else:
            self._print_strict(self._logger_type_error())
            if self.val_error_raise:
                raise ValueError
            return False

    def _get_str_for_timing_log(self, msg, time_offset) -> str:
        t = time.strftime('%H:%M:%S', time.localtime(msg.time))
        return f'Capture time: {t},\tCapture offset: {msg.time-time_offset:.9f},\tSequence ID: {msg.sequenceId}'

    def _prepare_path(self):
        p = os.path.dirname(__file__)
        if os.name == 'nt':
            p = p[:p.rfind('\\')] + '\\reports\\' + self._log_file_name
        else:
            p = p[:p.rfind('/')] + '/reports/' + self._log_file_name
        return p

    def _print_strict(self, string: str):
        if self.print_options == PrintOption.PrintToConsole:
            print(string)

    def _prepare_small_banner(self, in_string: str) -> str:
        banner_frame_verdical = '-----------------------------------------------------------'
        title_len = self.BANNER_LEN - 2 * len(banner_frame_verdical)
        banner_title = f'{in_string:^{title_len}}'
        prepared_banner = f'{banner_frame_verdical}{banner_title}{banner_frame_verdical}'
        return  prepared_banner[:self.BANNER_LEN]

    def _prepare_large_banner(self, in_string: str) -> str:
        banner_frame_horizontal = self.BANNER_LEN * '='
        banner_frame_verdical = '||'
        title_len = self.BANNER_LEN - 2 * len(banner_frame_verdical)
        banner_title = f'{in_string:^{title_len}}'
        return banner_frame_horizontal + self.LOGS_SEPARATOR + banner_frame_verdical + banner_title + \
            banner_frame_verdical + self.LOGS_SEPARATOR + banner_frame_horizontal

    def _logger_type_error(self):
        return "{0}{1}: Passed variable is not a string!".format(self.ERR_PREAMPULE, self._logger_type_error.__name__)
