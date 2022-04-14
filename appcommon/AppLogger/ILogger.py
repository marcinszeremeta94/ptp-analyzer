from abc import ABC, abstractmethod

class ILogger(ABC):
    @abstractmethod
    def info(self, in_string: str):
        pass

    @abstractmethod
    def debug(self, in_string: str):
        pass

    @abstractmethod
    def warning(self, in_string: str):
        pass

    @abstractmethod
    def error(self, in_string: str):
        pass

    @abstractmethod
    def msg_timing(self, msg, time_offset=0):
        pass

    @abstractmethod
    def banner_small(self, in_string: str):
        pass

    @abstractmethod
    def banner_large(self, in_string: str):
        pass

    @abstractmethod
    def new_line(self):
        pass
    
    @abstractmethod
    def get_log_dir_and_name(self) -> str:
        pass