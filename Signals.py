from PyQt5.QtCore import pyqtSignal, QObject



class signals(QObject):
    set_logging_signal = pyqtSignal(str)
    raise_error_signal = pyqtSignal(str)

    def __init__(self):
        super(signals, self).__init__()

