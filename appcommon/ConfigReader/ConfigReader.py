import json
import os

class ConfigReader:
    def __init__(self):
        self._ptp_rate_err = self.get_allowed_relative_ptp_rate_error()
        
    @property
    def ptp_rate_err(self):
        return self._ptp_rate_err
    
    def get_allowed_relative_ptp_rate_error(self) -> float:
        with open(self._get_path(), "r") as f:
            config = json.load(f)
        percent_err = config["allowed_relative_ptp_rate_error"]
        self._check_correctness(percent_err)
        return self._percent_err_to_float(percent_err)

    def _check_correctness(self, percent_err: str):
        if not percent_err.endswith("%"):
            raise Exception('Provided config invalid')

    def _percent_err_to_float(self, percent_err: str) -> float:
        num_in_str = percent_err[:-1]
        return float(num_in_str) / 100

    def _get_path(self) -> str:
        p = os.path.dirname(__file__)
        if os.name == "nt":
            tmp_p = p[: p.rfind("\\")]
            p = tmp_p[: tmp_p.rfind("\\")] + "\\config.json"
        else:
            tmp_p = p[: p.rfind("/")]
            p = tmp_p[: tmp_p.rfind("/")] + "/config.json"
        return p
