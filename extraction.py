from openpyxl import load_workbook
from PyQt5 import QtWidgets
from Signals import signals
from time import time


def error_message(message, caption):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(caption)
    msg.setInformativeText(message)
    msg.setWindowTitle("Error")
    msg.exec_()
    msg.deleteLater()


def information_message(message):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText("Alert")
    msg.setInformativeText(message)
    msg.setWindowTitle("Warning")
    msg.exec_()


def check_credentials(username, password):
    if username == "" or password == "":
        error_message("Login Credentials not provided", "Login Error!")
        return False
    return True


class Execute():

    def __init__(self):
        super().__init__()  # inherit logging Signal objects form Signals file
        self.init()

    def init(self):
        self.therads_list = []
        self.input_file_path = ""
        self.output_file_path = ""
        self.input_file_ready = 0
        self.output_path_ready = 0
        self.username = ""
        self.password = ""
        self.device_ips = []
        self.device_name_list = []
        self.execution_started = False
        self.total_device_count = 0
        self.successful_device_count = 0
        self.failed_device_count = 0
        self.failed_device_list = []
        self.Thread_control = 0
        self.check_boxes_checked = 0
        self.sig = signals()



    # ================================================INPUT/OUTPUT File Check
    def check_input_output_files(self, ui):
        if self.input_file_ready != 1:
            error_message("No input file provided, please provide path to an Excel file "
                          "under \"Device List\" option", "Error!")
            return False
        if self.output_path_ready != 1 and ui.le_output_file.text() != self.output_file_path:
            information_message("No Output Folder selected in \"Output Path\" field, output files will be saved "
                                "in the same folder as the RIDE program")
            ui.le_output_file.setText(self.output_file_path)
            self.output_path_ready = 1
            return True
        return True

    # ==============================================
    def device_list_reader(self, ui):
        try:
            device_list = load_workbook(self.input_file_path)
            self.device_ips = []  #everytime a list is read the the old values in array must delete
            for row in device_list.active.values:
                if row[0] is not None:
                    self.device_ips.append(
                        row[0])  # All the device IPs should be stored in first column of Excel
            self.input_file_ready = 1
            self.total_device_count = self.device_ips.__len__()
            ui.lcd_total_devices.display(self.total_device_count)
            self.sig.set_logging_signal.emit("Device List Reading Complete")

        except Exception as e:
            error_message(e, "Error in Loading Device List!")
            self.input_file_path = ""
