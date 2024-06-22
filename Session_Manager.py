import re
import time

from PyQt5.QtCore import QObject
from netmiko import ConnectHandler, NetmikoAuthenticationException
from Writer import Writer


class SessionManager(QObject) :
    huawei_os = 'huawei_vrpv8'
    juniper_os = 'juniper_junos'
    unknown_os = 'terminal_server'

    def __init__(self, node_ip, exe, ui, node_number):
        super(SessionManager, self).__init__()
        self.device_ip = node_ip
        self.exe = exe
        self.ui = ui
        self.device_number = node_number
        self.device_name = ""
        self.identified_vendor = ""
        self.device_state = 0; # 0 =  access failed, 1 == device accessible
        self.init()
        exe.Thread_control += 1

    def init(self):
        self.device_name, self.identified_vendor = self.identify_device_type()

    def make_connection(self):
        if self.device_state: # if device is identified as accessible : proceed with setting up SSH
            self.exe.sig.set_logging_signal.emit(f"Accessing Device number {self.device_number} at {self.device_ip}")
            router = self.return_node_dictionary(self.identified_vendor)
            try:
                self.SSH_connection = ConnectHandler(**router)
                self.exe.device_name_list.append(self.device_name)
                if self.identified_vendor is self.huawei_os:
                    print("executing huawei commands")
                elif self.identified_vendor is self.juniper_os:
                    print("execute juniper commands")
                else:
                    print("cant identify vendor")
                self.SSH_connection.disconnect()

                self.exe.Thread_control -= 1
                # self.exe.sig.set_logging_signal.emit(
                #     f'Data Collection Done for device number : {self.device_number} i.e {self.device_name} ')
                # write = Writer(output, self.device_name, self.exe.output_file_path)  # initiating the data writing
                # self.exe.sig.set_logging_signal.emit(f'{self.device_name}: File Saved')
                self.exe.successful_device_count += 1
            except Exception as e:
                print(f'({self.device_number})-> ****[ERROR]**** : occurred for {self.device_name}, \n {e.with_traceback(None)}')
                self.handle_failed_device()


    def handle_failed_device (self):
        if self.exe.Thread_control > 0:
            self.exe.Thread_control -= 1
        self.exe.failed_device_count += 1
        self.exe.failed_device_list.append(self.device_ip)
        self.device_state = 0

    def return_node_dictionary(self, vendor_OS):
        return {'device_type': vendor_OS,
                'host': self.device_ip,
                'username': self.ui.le_username.text(),
                'password': self.ui.le_password.text(),
                'session_timeout': 120,
                'session_log': f"logs//{self.device_ip}.log",
                }

    def identify_device_type(self):
        self.exe.sig.set_logging_signal.emit(f"({self.device_number}) -> Trying to identify the equipment vendor of {self.device_ip}")
        unidentified_node = self.return_node_dictionary(self.unknown_os)
        device_type = self.unknown_os
        name = self.device_ip
        try:
            net_connect = ConnectHandler(**unidentified_node)
            net_connect.write_channel("\r")
            time.sleep(0.3)
            output = net_connect.read_channel()
            if 'JUNOS' in output:
                self.exe.sig.set_logging_signal.emit(f"({self.device_number}) -> {self.device_ip} is identified as Juniper node")
                device_type = self.juniper_os
            elif 'Warning: The initial password' in output:
                self.exe.sig.set_logging_signal.emit(f"({self.device_number}) -> {self.device_ip} is identified as Huawei node")
                device_type = self.huawei_os
                net_connect.write_channel("N")
                time.sleep(0.3)
                net_connect.write_channel("\r")
                time.sleep(0.3)
                output = net_connect.read_channel()
            else:
                self.exe.sig.set_logging_signal.emit(f"({self.device_number}) -> {self.device_ip} is identified as Huawei node")
                device_type = self.huawei_os

            name = extract_device_name(output)
            net_connect.disconnect()
            self.device_state = 1
        except NetmikoAuthenticationException as e:
            print(f"Authentication exception happend for {self.device_ip}")
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number})-> ****[ERROR]**** : occurred for {self.device_name}, \n {e.with_traceback(None)}')

        except Exception as e:
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number})-> ****[ERROR]**** : occurred for {self.device_name}, \n {e.with_traceback(None)}')
            print(e.with_traceback(None))
            self.handle_failed_device()
        return name,device_type

def extract_device_name(text):
    pattern = r'<(.*?)>|@(.*?)>'
    match = re.search(pattern, text)
    return match.group(0).strip()[1:-1] if match else "<cant read name>"
