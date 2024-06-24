import re
import time

from PyQt5.QtCore import QObject
from netmiko import ConnectHandler, NetmikoAuthenticationException
from textfsm import TextFSMTemplateError

from Writer import Writer


def extract_device_name(text):
    pattern = r'<(.*?)>|@(.*?)>'
    match = re.search(pattern, text)
    return match.group(0).strip()[1:-1] if match else "<cant read name>"


class SessionManager(QObject):
    huawei_os = 'huawei_vrpv8'
    juniper_os = 'juniper_junos'
    unknown_os = 'terminal_server'

    def __init__(self, node_ip, exe, ui, node_number):
        super(SessionManager, self).__init__()
        self.device_ip = node_ip
        self.exe = exe
        self.ui = ui
        self.device_number = node_number
        self.device_state = 0;  # 0 =  access failed, 1 == device accessible
        self.device_name = f"no-name {node_ip}"
        self.identified_vendor = self.unknown_os
        self.physical_interface_command: str = ""
        self.all_interface_description_command: str = ""
        self.trunks_bandwidth_command: str = ""
        self.loaded_licenses_command_1: str = ""
        self.loaded_licenses_command_2: str = ""
        self.license_usage_on_port_command: str = ""
        self.optical_module_commands_1: str = ""
        self.optical_module_commands_2: str = ""
        self.inventory_report_command_1: str = ""
        self.inventory_report_command_2: str = ""
        self.inventory_report_command_3: str = ""

        self.physical_interface_fsm: str = ""
        self.all_interface_description_fsm: str = ""
        self.trunks_bandwidth_fsm: str = ""
        self.loaded_licenses_fsm_1: str = ""
        self.loaded_licenses_fsm_2: str = ""
        self.license_usage_on_port_fsm: str = ""
        self.optical_module_fsm_1: str = ""
        self.optical_module_fsm_2: str = ""
        self.inventory_report_fsm_1: str = ""
        self.inventory_report_fsm_2: str = ""
        self.inventory_report_fsm_3: str = ""
        self.set_command_set(
            self.identified_vendor)  # setting up command set and FSM template formate for later execution.
        exe.Thread_control += 1

    def start_execution(self):
        self.device_name, self.identified_vendor = self.identify_device_type()
        if self.device_state:
            self.set_command_set(vendor=self.identified_vendor)
            self.make_connection()

    def make_connection(self):
        if self.device_state:  # if device is identified as accessible : proceed with setting up SSH
            self.exe.sig.set_logging_signal.emit(f"Accessing Device number {self.device_number} at {self.device_ip}")
            router = self.return_node_dictionary(self.identified_vendor)
            try:
                self.exe.device_name_list.append(self.device_name)
                output = self.execute_commands(router)
                print(output.keys())
                self.exe.Thread_control -= 1
                # self.exe.sig.set_logging_signal.emit(
                #     f'Data Collection Done for device number : {self.device_number} i.e {self.device_name} ')
                # write = Writer(output, self.device_name, self.exe.output_file_path)  # initiating the data writing
                # self.exe.sig.set_logging_signal.emit(f'{self.device_name}: File Saved')
                self.exe.successful_device_count += 1
            except Exception as e:
                print(
                    f'({self.device_number})-> ****[ERROR]**** : occurred for {self.device_name}, \n {e.with_traceback(None)}')
                self.handle_failed_device()

    def set_command_set(self, vendor: str):
        if vendor == self.huawei_os:
            self.physical_interface_command: str = 'display interface | no-more'
            self.all_interface_description_command: str = "display interface description | no-more"
            self.trunks_bandwidth_command: str = "display interface eth-trunk | no-more"
            self.loaded_licenses_command_1: str = "display license verbose | no-more"
            self.loaded_licenses_command_2: str = "display license resource usage | no-more"
            self.license_usage_on_port_command: str = "display license resource usage port-basic all | no-more"
            self.optical_module_commands_1: str = "display optical-module brief | no-more"
            self.inventory_report_command_1: str = "display device pic-status | no-more"
            self.inventory_report_command_2: str = "display version | no-more"
            self.inventory_report_command_3: str = "display elabel brief | no-more"

            self.physical_interface_fsm: str = "TEXT_FSM_FILES//huawei_vrp_display_interface"
            self.all_interface_description_fsm: str = "TEXT_FSM_FILES//huawei_vrp_display_interface_description"
            self.trunks_bandwidth_fsm: str = "TEXT_FSM_FILES//huawei_vrp_display_interface_eth_trunk"
            self.loaded_licenses_fsm_1: str = "TEXT_FSM_FILES//huawei_vrp_display_license_verbose"
            self.loaded_licenses_fsm_2: str = "TEXT_FSM_FILES//huawei_vrp_display_license_resource_usage"
            self.license_usage_on_port_fsm: str = "TEXT_FSM_FILES//huawei_vrp_display_lic_res_usage_port_basic.textfsm"
            self.optical_module_fsm_1: str = "TEXT_FSM_FILES//huawei_vrp_display_optical_module_brief.textfsm"
            #for inventory reprort
            # 1 : pic status FSM
            # 2 : version FSM
            # 3 : elable FSM
            self.inventory_report_fsm_1: str = "TEXT_FSM_FILES//huawei_vrp_display_device_pic_status.textfsm"
            self.inventory_report_fsm_2: str = "TEXT_FSM_FILES//huawei_vrp_display_version.textfsm"
            self.inventory_report_fsm_3: str = "TEXT_FSM_FILES//huawei_vrp_display_elable_brief.textfsm"

        if vendor == self.juniper_os:
            self.physical_interface_command: str = 'show interfaces brief | display json | no-more'
            self.all_interface_description_command: str = "show interfaces descriptions | display json | no-more"
            self.trunks_bandwidth_command: str = "show interfaces ae* detail | display json | no-more"
            self.loaded_licenses_command_1: str = "show system license detail | display json | no-more"
            self.optical_module_commands_1: str = "show chassis fpc pic-status | display json | no-more"
            self.optical_module_commands_2: str = "show chassis pic pic-slot"
            self.inventory_report_command_1: str = "show chassis hardware | display json | no-more "
            self.inventory_report_command_2: str = "show version | display json | no-more"

    def execute_commands(self, router: dict):
        output = {'traceback': 0}
        if_huawei = self.identified_vendor == self.huawei_os  #Text FSM will only run if vendor is Huawei
        try:
            SSH_connection = ConnectHandler(**router)  # exceptions will be handled in make_connection function
            # check what options user has checked in the UI and then execute commands accordingly
            if self.ui.cb_physical_inteface.isChecked():
                physical_interface_output = SSH_connection.send_command_timing(self.physical_interface_command,
                                                                               use_textfsm=if_huawei,
                                                                               textfsm_template=self.physical_interface_fsm)
            if self.ui.cb_interface_decription.isChecked():
                all_interface_description_output = SSH_connection.send_command_timing(
                    self.all_interface_description_command,
                    use_textfsm=if_huawei,
                    textfsm_template=self.all_interface_description_fsm)
            if self.ui.cb_trunks.isChecked():
                trunks_bandwidth_output = SSH_connection.send_command_timing(self.trunks_bandwidth_command,
                                                                             use_textfsm=if_huawei,
                                                                             textfsm_template=self.trunks_bandwidth_fsm)
            if self.ui.cb_licenses.isChecked():
                loaded_licenses_1_output = SSH_connection.send_command_timing(self.loaded_licenses_command_1,
                                                                              use_textfsm=if_huawei,
                                                                              textfsm_template=self.loaded_licenses_fsm_1)
                loaded_licenses_2_output = ""
                if self.identified_vendor == self.huawei_os:
                    loaded_licenses_2_output = SSH_connection.send_command_timing(self.loaded_licenses_command_2,
                                                                                  use_textfsm=if_huawei,
                                                                                  textfsm_template=self.loaded_licenses_fsm_2)
            if self.ui.cb_optical_modules.isChecked():
                optical_module_commands_2_output = ""
                optical_module_commands_1_output = SSH_connection.send_command_timing(
                    self.optical_module_commands_1,
                    use_textfsm=if_huawei,
                    textfsm_template=self.optical_module_fsm_1)
                if self.identified_vendor == self.juniper_os:
                    optical_module_commands_2_output = SSH_connection.send_command_timing(
                        self.optical_module_commands_2,
                        use_textfsm=if_huawei,
                        textfsm_template=self.optical_module_fsm_2)
            if self.ui.cb_lpu_cards.isChecked():
                inventory_report_command_3_output = ""
                inventory_report_command_1_output = SSH_connection.send_command_timing(
                    self.inventory_report_command_1,
                    use_textfsm=if_huawei,
                    textfsm_template=self.inventory_report_fsm_1)
                inventory_report_command_2_output = SSH_connection.send_command_timing(
                    self.inventory_report_command_2,
                    use_textfsm=if_huawei,
                    textfsm_template=self.inventory_report_fsm_2)
                if self.identified_vendor == self.huawei_os:
                    inventory_report_command_3_output = SSH_connection.send_command_timing(
                        self.inventory_report_command_3,
                        use_textfsm=if_huawei,
                        textfsm_template=self.inventory_report_fsm_3)
            if self.ui.cb_port_lic_utilization.isChecked():
                license_usage_on_port_output = ""
                if self.identified_vendor == self.huawei_os:
                    license_usage_on_port_output = SSH_connection.send_command_timing(
                        self.license_usage_on_port_command,
                        use_textfsm=if_huawei,
                        textfsm_template=self.license_usage_on_port_fsm)

            SSH_connection.disconnect()
            output.update({self.physical_interface_command: physical_interface_output,
                           self.all_interface_description_command: all_interface_description_output,
                           self.trunks_bandwidth_command: trunks_bandwidth_output,
                           self.loaded_licenses_command_1: loaded_licenses_1_output,
                           self.loaded_licenses_command_2: loaded_licenses_2_output,
                           self.license_usage_on_port_command: license_usage_on_port_output,
                           self.optical_module_commands_1: optical_module_commands_1_output,
                           self.optical_module_commands_2: optical_module_commands_2_output,
                           self.inventory_report_command_1: inventory_report_command_1_output,
                           self.inventory_report_command_2: inventory_report_command_2_output,
                           self.inventory_report_command_3: inventory_report_command_3_output})
            return output
        except TextFSMTemplateError as e:
            print(f'({self.device_number})->[FSM ERROR]: for  {self.device_name}, \n {e.with_traceback(None)}')

        except Exception as e:
            print(
                f'({self.device_number})->[ERROR]: occurred in command execution for {self.device_name}, \n {e.with_traceback(None)}')

    def handle_failed_device(self):
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
        self.exe.sig.set_logging_signal.emit(
            f"({self.device_number}) -> Trying to identify the equipment vendor of {self.device_ip}")
        unidentified_node = self.return_node_dictionary(self.unknown_os)
        device_type = self.unknown_os
        name = self.device_ip
        try:
            net_connect = ConnectHandler(**unidentified_node)
            net_connect.write_channel("\r")
            time.sleep(0.3)
            output = net_connect.read_channel()
            huawei_pattern = r'<(.*?)>'
            if 'JUNOS' in output:
                self.exe.sig.set_logging_signal.emit(
                    f"({self.device_number}) -> {self.device_ip} is identified as Juniper node")
                device_type = self.juniper_os
            elif 'Warning: The initial password' or huawei_pattern in output:
                self.exe.sig.set_logging_signal.emit(
                    f"({self.device_number}) -> {self.device_ip} is identified as Huawei node")
                device_type = self.huawei_os
                net_connect.write_channel("N")
                time.sleep(0.3)
                net_connect.write_channel("\r")
                time.sleep(0.3)
                output = net_connect.read_channel()
            else:
                self.exe.sig.set_logging_signal.emit(
                    f"({self.device_number}) -> {self.device_ip}'s vendor is not identified,setting it up as huawei node for now")
                device_type = self.huawei_os

            name = extract_device_name(output)
            net_connect.disconnect()
            self.device_state = 1
        except NetmikoAuthenticationException as e:
            print(f"Authentication exception happened for {self.device_ip}")
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number})-> ****[ERROR]**** : occurred for {self.device_name}, \n {e.with_traceback(None)}')
            self.handle_failed_device()

        except Exception as e:
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number})-> ****[ERROR]**** : occurred for {self.device_name}, \n {e.with_traceback(None)}')
            print(e.with_traceback(None))
            self.handle_failed_device()
        return name, device_type
