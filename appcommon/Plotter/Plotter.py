import matplotlib.pyplot as plt
from mptp.PtpCheckers.PtpTiming import PtpTiming
from mptp.PtpPacket.PTPv2 import PtpType

class Plotter:
    
    def __init__(self, plotter_off=False, plot_dir_and_name:str = 'figure.png') -> None:
        self._plotter_off = plotter_off
        self._plot_path = plot_dir_and_name[:plot_dir_and_name.rfind(".")] + ".png"
        
    def general_plots(self):
        pass

    def plot_timings(self, announce: PtpTiming, sync: PtpTiming, follow_up: PtpTiming):
        if self._plotter_off:
            return
        if len(announce.msgs) == 0:
            hist2,hist0 = self._create_subplots_without_announce()
        else:
            hist3, hist2, hist1, hist0 = self._create_subplots_with_announce()
            self._add_timestamp_histogram(hist1, announce)
            self._add_capture_histogram(hist3, announce) 
        ts = self._sync_or_followup_timestamps_input_determine(sync, follow_up)
        self._add_timestamp_histogram(hist0, ts)
        self._add_capture_histogram(hist2, ts)
        self._save_plot_to_file(plt.gcf()) 

    def _create_subplots_without_announce(self):
        plt.rcParams["figure.autolayout"] = True
        fig = plt.figure()
        spec = fig.add_gridspec(ncols=1, nrows=2)
        hist2 = fig.add_subplot(spec[1, 0])
        hist0 = fig.add_subplot(spec[0, 0], sharex=hist2)
        return hist2,hist0 
    
    def _create_subplots_with_announce(self):
        plt.rcParams["figure.autolayout"] = True
        fig = plt.figure()
        spec = fig.add_gridspec(ncols=2, nrows=2) 
        hist3 = fig.add_subplot(spec[1, 1])
        hist2 = fig.add_subplot(spec[1, 0])
        hist1 = fig.add_subplot(spec[0, 1], sharex=hist3)
        hist0 = fig.add_subplot(spec[0, 0], sharex=hist2)
        return hist3,hist2,hist1,hist0 
    
    def _sync_or_followup_timestamps_input_determine(self, sync: PtpTiming, follow_up: PtpTiming):
        if len(follow_up.msgs) == 0:
            return sync
        else:
            return follow_up
        
    def _save_plot_to_file(self, figure):
        figure.set_size_inches((24, 12), forward=False)    # 11, 8,5 inches is A4
        figure.savefig(self._plot_path, dpi=600) 
        
    def _add_timestamp_histogram(self, ax, series):
        hist_range = self._get_range(series)
        num_bins = 40 if (hist_range[1] - hist_range[0]) < 4 else 120
        ax.hist(series.msg_rates, num_bins, range=hist_range, facecolor='green', alpha=0.5, edgecolor='black')
        ax.set(ylabel='occurrence [n]', title=f'{PtpType.get_ptp_type_str(series.msgs[0])} - Time Stamp')
        self._set_grid_and_scale_for_timings(ax)
        
    def _add_capture_histogram(self, ax, series):
        hist_range = self._get_range(series)
        num_bins = 40 if (hist_range[1] - hist_range[0]) < 4 else 120
        ax.hist(series.capture_rates, num_bins, range=hist_range, facecolor='blue', alpha=0.5, edgecolor='black')
        ax.set(xlabel='msg rate [msg/sec]', ylabel='occurrence [n]', title=f'{PtpType.get_ptp_type_str(series.msgs[0])} - Capture')
        self._set_grid_and_scale_for_timings(ax)
        
    def _set_grid_and_scale_for_timings(self, ax):
        ax.grid(linestyle='--', which='minor', alpha=0.4)
        ax.grid(linestyle='--', which='major', alpha=0.7)
        ax.set_yscale('log')
        
    def _get_range(self, x):
        return (round(min(x.capture_rates), 3), round(max(x.capture_rates), 3)) 
        # by some reason when does not round to int sometimes does not print in log scale
