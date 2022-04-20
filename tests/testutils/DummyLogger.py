from appcommon.AppLogger.ILogger import ILogger

class DummyLogger(ILogger):
    def info(self, in_string: str):
        pass

    def debug(self, in_string: str):
        pass

    def warning(self, in_string: str):
        pass

    def error(self, in_string: str):
        pass

    def msg_timing(self, msg, time_offset=0):
        pass

    def banner_small(self, in_string: str):
        pass

    def banner_large(self, in_string: str):
        pass

    def new_line(self):
        pass
    
    def get_log_dir_and_name(self) -> str:
        pass