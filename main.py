import sys
import traceback
from datetime import datetime
from time import sleep
from Session_Manager import SessionManager
from PyQt5 import QtWidgets
from main_layout_1 import Ui_main_window
from extraction import Execute, check_credentials, error_message, information_message
from PyQt5.QtCore import QThread, pyqtSlot
import _cffi_backend


def select_device_list():
    exe.total_device_count = 0
    exe.input_file_path = QtWidgets.QFileDialog.getOpenFileName(parent=main_window,
                                                                caption='Select Input File',
                                                                filter="Excel Files (*.xlsx)")[0]
    ui.le_device_list.setText(exe.input_file_path)
    if exe.input_file_path != "":
        exe.device_list_reader(ui)


def select_output_folder():
    selected_path = QtWidgets.QFileDialog.getExistingDirectory(parent=main_window,
                                                               caption='Select Output Folder',
                                                               options=QtWidgets.QFileDialog.ShowDirsOnly)
    ui.le_output_file.setText(exe.output_file_path)
    if selected_path != "":
        exe.output_file_path = selected_path
    ui.le_output_file.setText(exe.output_file_path)
    exe.output_path_ready = 1


def select_all_options():
    state = ui.b_select_all.text() == "Select All"
    ui.b_select_all.setText("Unselect All" if state else "Select All")
    exe.check_boxes_checked = 7 if state else 0

    ui.cb_trunks.setChecked(state)
    ui.cb_licenses.setChecked(state)
    ui.cb_optical_modules.setChecked(state)
    ui.cb_lpu_cards.setChecked(state)
    ui.cb_physical_inteface.setChecked(state)
    ui.cb_interface_decription.setChecked(state)
    ui.cb_port_lic_utilization.setChecked(state)


def run_checkbox_selection():
    if ui.cb_trunks.isChecked():
        exe.check_boxes_checked += 1
    if ui.cb_licenses.isChecked():
        exe.check_boxes_checked += 2
    if ui.cb_lpu_cards.isChecked():
        exe.check_boxes_checked += 1
    if ui.cb_optical_modules.isChecked():
        exe.check_boxes_checked += 1
    if ui.cb_physical_inteface.isChecked():
        exe.check_boxes_checked += 1
    if ui.cb_interface_decription.isChecked():
        exe.check_boxes_checked += 1
    if ui.cb_port_lic_utilization.isChecked():
        exe.check_boxes_checked += 1

    if exe.check_boxes_checked == 0:
        error_message("Mazy na lo, Hawa main chala doon program\nKia output chahye select to kro", "Selection Error!")
        return False

    return True


def check_threads(user_interface):
    while True:
        try:
            threads = int(user_interface.le_thread_count.text())
            if threads > 20:
                information_message("Accessing higher number of devices in parallel might causes your system to slow "
                                    "down and increases the probability of device access failure")

            return threads
        except ValueError:
            error_message("\'No of Threads\' must be a numeric value, setting \'Max Thread count\' to default value "
                          "i.e 15", "INPUT ERROR")
            return 15


# displays IPs of all the failed devices in the Log output section of GUI
def list_failed_devices():
    exe.sig.set_logging_signal.emit("Execution FAILED for following nodes")
    for i in exe.failed_device_list:
        exe.sig.set_logging_signal.emit(i)


# reset variables to be reused by GUI for another device list.
def reset():
    exe.device_ips = []
    exe.device_name_list = []
    exe.execution_started = False
    exe.total_device_count = 0
    exe.successful_device_count = 0
    exe.failed_device_count = 0
    exe.failed_device_list = []
    exe.Thread_control = 0


@pyqtSlot(str)
def update_output_panel(log):
    ui.te_output_panel.appendPlainText(log)


def log_recording():
    with open(exe.output_file_path + "\\Output_Logs.log", "w") as test_file:
        test_file.write(ui.te_output_panel.toPlainText())


def execute_main_thread():
    execution_time = datetime.now()
    MAX_THREADS = check_threads(ui)
    try:
        if exe.execution_started:
            error_message("Ruko Zara... \nSabr Kro...", "Execution in progress!")
        else:
            if exe.check_input_output_files(ui):
                if check_credentials(ui.le_username.text(), ui.le_password.text()):
                    if run_checkbox_selection():
                        exe.execution_started = True
                        device_number = 0
                        exe.sig.set_logging_signal.emit("Starting Core Execution ...")
                        for node in exe.device_ips:
                            # Keeping MAX THREAD below desired number
                            while exe.Thread_control >= MAX_THREADS:
                                sleep(0.5)
                                exe.sig.set_logging_signal.emit("Processing")
                                app.processEvents()
                            # Controlling Main worker
                            device_number += 1
                            try:
                                worker = SessionManager(node, exe, ui, device_number)  # Each device session is a new worker
                                app.processEvents()
                                thread = QThread()
                                thread.setObjectName(node)
                                exe.therads_list.append((thread, worker))
                                worker.moveToThread(thread)
                                thread.started.connect(worker.start_execution)
                                thread.start()

                            except Exception as e:
                                app.processEvents()
                                print(f"[Error]: Exception caught in main: {e.with_traceback(None)}")

                        done_devices = exe.successful_device_count + exe.failed_device_count
                        while done_devices != exe.total_device_count:
                            sleep(1)
                            exe.sig.set_logging_signal.emit(
                                f"Processing....!!  Devices left : {exe.total_device_count - done_devices}")
                            done_devices = exe.successful_device_count + exe.failed_device_count
                            app.processEvents()

                        execution_time = datetime.now() - execution_time
                        exe.sig.set_logging_signal.emit(f"\nExecution Completed in {execution_time}")

                        # Printing failed devices for user
                        if exe.failed_device_list.__len__() >= 1:
                            list_failed_devices()
                        log_recording()
                        app.processEvents()

                        # Resetting parameters for reuse of GUI with new device list
                        reset()
    except Exception as e:
        print(e.with_traceback)


def exit():
    log_recording()
    sys.exit(0)


app = QtWidgets.QApplication(sys.argv)
main_window = QtWidgets.QMainWindow()
ui = Ui_main_window()
ui.setupUi(main_window)
exe = Execute()

ui.b_device_list_open.clicked.connect(select_device_list)
ui.b_outputfile_open.clicked.connect(select_output_folder)
ui.b_extract.clicked.connect(execute_main_thread)
ui.b_select_all.clicked.connect(select_all_options)
exe.sig.set_logging_signal.connect(update_output_panel)
ui.b_exit.clicked.connect(exit)

main_window.show()
sys.exit(app.exec_())
