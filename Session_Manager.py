import json
import pprint
import re
import time
import traceback

from PyQt5.QtCore import QObject
from netmiko import ConnectHandler, NetmikoAuthenticationException
from textfsm import TextFSMTemplateError
from Writer import Writer
import ttp_templates as ttp


def key_exists(data: dict, key: str) -> bool:  # checks if a certain key exists in the provided dictionary
    if key in data.keys():
        return True
    return False


class SessionManager(QObject):
    huawei_os = 'huawei_vrpv8'
    juniper_os = 'juniper_junos'
    unknown_os = 'terminal_server'

    def __init__(self, node_ip, exe, ui, node_number):
        super(SessionManager, self).__init__()
        self.device_ip = node_ip
        self.ssh_port = exe.ssh_port
        self.exe = exe
        self.ui = ui
        self.read_timeout = 0
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
        exe.Thread_control += 1

        self.huawei_output_format = {
            'physical interfaces': [{'interface': '', 'link_status': '', 'port_bw': '', 'type': ''}],
            'trunks': [{'trunk_number': '', 'trunk_state': '', 'no_of_links': '', "member_interfaces": '', 'max_bw': '',
                        "current_bw": ''}],
            'interface descriptions': [{'interface': '', 'phy': '', 'opr_status': '', 'description': ''}],
            'inventory pic status': [
                {'pic_slot': '', 'pic_sub': '', 'status': '', 'type': '', 'port_count': '', 'port_type': ''}],
            'licenses': [{'description': '', 'expired_date': '', 'lic_name': ''}],
            'license usage': [{'lic_name': '', 'avil_lic': '', 'used_lic': ''}],
            'optics': [
                {'port': '', 'status': '', 'duplex': '', 'type': '', 'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''}],
            'license usage on ports': [
                {'port': '', 'fname': '', 'ncount': '', 'ucount': '', 'status': ''}],
            'version': [{'main_os': '', 'os_version': '', 'model': '', 'uptime': '', 'mpu_q': '', 'sru_q': '',
                         'sfu_q': '', 'lpu_q': ''}],
            'inventory details': [{'module': '', 'slot_no': '', 'board_type': '', 'bar_code': '', 'description': ''}]

        }

        self.juniper_output_format = {
            'physical interfaces': [{'interface': '', 'link_status': '', 'port_bw': '', 'type': ''}],
            'trunks': [{'trunk_number': '', 'trunk_state': '', 'no_of_links': '', "member_interfaces": ''}],
            'interface descriptions': [{'interface': '', 'phy': '', 'opr_status': '', 'description': ''}],
            'inventory pic status': [
                {'pic_slot': '', 'pic_sub': '', 'status': '', 'type': '', 'port_count': '', 'port_type': ''}],
            'licenses': [{'description': '', 'expired_date': '', 'lic_name': ''}],
            'license usage': [{'lic_name': '', 'avil_lic': '', 'used_lic': ''}],
            'license usage on ports': [
                {'port': '', 'fname': '', 'ncount': '', 'ucount': '', 'status': ''}],
            'optics': [
                {'port': '', 'status': "", 'vendor': '', 'duplex': '', 'part_number': '', 'type': '', 'wl': '',
                 'rxpw': '', 'txpw': '', 'mode': ''}],
            'version': [{'main_os': '', 'os_version': '', 'model': '', 'uptime': '', 'mpu_q': '', 'sru_q': '',
                         'sfu_q': '', 'lpu_q': ''}],
            'inventory details': [{'module': '', 'version': '', 'part_number': '', 'bar_code': '', 'description': ''}]

        }

    def handle_failed_device(self):
        if self.exe.Thread_control > 0:
            self.exe.Thread_control -= 1
        self.exe.failed_device_count += 1
        self.exe.failed_device_list.append(self.device_ip)
        self.device_state = 0

    def return_node_dictionary(self, vendor_OS):
        return {'device_type': vendor_OS,
                'host': self.device_ip,
                'port' : self.ssh_port,
                'username': self.ui.le_username.text(),
                'password': self.ui.le_password.text(),
                'session_timeout': 300,
                'session_log': f"logs//{self.device_number}-{self.device_ip}.log",
                }

    def start_execution(self):
        self.device_name, self.identified_vendor = self.identify_device_type()
        if self.device_state:
            self.set_command_set(vendor=self.identified_vendor)
            self.make_connection()

    def set_command_set(self, vendor: str):
        if vendor == self.huawei_os:
            self.physical_interface_command: str = 'display interface main | no-more'
            self.all_interface_description_command: str = "display interface description | no-more"
            self.trunks_bandwidth_command: str = "display interface eth-trunk main | no-more"
            self.loaded_licenses_command_1: str = "display license verbose | no-more"
            self.loaded_licenses_command_2: str = "display license resource usage | no-more"
            self.license_usage_on_port_command: str = "display license resource usage port-basic all | no-more"
            self.optical_module_commands_1: str = "display optical-module brief | no-more"
            self.inventory_report_command_1: str = "display device pic-status | no-more"
            self.inventory_report_command_2: str = "display version | no-more"
            self.inventory_report_command_3: str = "display elabel brief  | no-more"

            self.physical_interface_fsm: str = ttp.ttp_huawei_display_interface
            self.all_interface_description_fsm: str = ttp.ttp_huawei_display_interface_description
            self.trunks_bandwidth_fsm: str = ttp.ttp_huawei_display_interface_eth_trunk
            self.loaded_licenses_fsm_1: str = "TEXT_FSM_FILES//huawei_vrp_display_license_verbose"
            self.loaded_licenses_fsm_2: str = "TEXT_FSM_FILES//huawei_vrp_display_license_resource_usage"
            self.license_usage_on_port_fsm: str = ttp.ttp_huawei_display_licesnse_resource_usage_port_basic_all
            self.optical_module_fsm_1: str = ttp.ttp_huawei_display_optical_module_brief
            #for inventory reprort
            # 1 : pic status FSM
            # 2 : version FSM
            # 3 : elable FSM
            self.inventory_report_fsm_1: str = ttp.ttp_huawei_display_device_pic_status
            self.inventory_report_fsm_2: str = ttp.ttp_huawei_display_version
            self.inventory_report_fsm_3: str = ttp.ttp_huawei_display_elabel_brief

        if vendor == self.juniper_os:
            self.physical_interface_command: str = "show interfaces detail | display json | no-more"
            self.all_interface_description_command: str = "show interfaces descriptions | no-more"
            self.trunks_bandwidth_command: str = "show lacp interfaces | display json | no-more"
            self.loaded_licenses_command_1: str = "show system license | display json | no-more"
            self.optical_module_commands_1: str = "show chassis fpc pic-status | display json | no-more "  #one extra space to distinguish between inventory command 1
            self.optical_module_commands_2: str = "show chassis pic fpc-slot | no-more"
            self.inventory_report_command_1: str = "show chassis fpc pic-status | display json | no-more"
            self.inventory_report_command_2: str = "show version | no-more"
            self.inventory_report_command_3: str = "show chassis hardware | display json | no-more"

            self.all_interface_description_fsm: str = ttp.ttp_juniper_show_interface_description
            self.inventory_report_fsm_2: str = ttp.ttp_juniper_show_version

    def make_connection(self):
        if not self.device_state:  # Exit if the device was not accessible while vendor identification
            return

        self.print_log(log_type='INFO', message="Accessing Device")
        router = self.return_node_dictionary(self.identified_vendor)

        try:
            self.exe.device_name_list.append(self.device_name)
            output = self.execute_commands(router)

            if output:
                ready_to_write_output = self.process_output_by_vendor(output[0])

            self.exe.Thread_control -= 1
            self.print_log(log_type='INFO', message='Data Collection Done')

            Writer(ready_to_write_output, self.device_name, self.exe.output_file_path, self.identified_vendor, self.exe)
            self.print_log(log_type='INFO', message='File Saved')
            self.exe.successful_device_count += 1

        except KeyError:
            self.print_log('JSON CONVERSION ERROR', 'Cannot obtain processed output', traceback.format_exc())
            self.handle_failed_device()
        except Exception:
            self.print_log('MAKE CONNECTION ERROR', 'Cannot process connection', traceback.format_exc())
            self.handle_failed_device()

    def process_output_by_vendor(self, output):  # returns only vendor specific format
        if self.identified_vendor == self.juniper_os:
            structured_output = self.convert_to_json(output)
            self._juniper_convert_to_writable_formate(structured_output)
            return self.juniper_output_format

        if self.identified_vendor == self.huawei_os:
            self._huawei_convert_to_writable_formate(output)
            return self.huawei_output_format

        return None

    def execute_commands(self, router: dict):
        output = []
        if_huawei = self.identified_vendor == self.huawei_os  #Text FSM will only run if vendor is Huawei
        try:
            SSH_connection = ConnectHandler(**router)  # exceptions will be handled in make_connection function
            physical_interface_output: str = ""
            all_interface_description_output: str = ""
            trunks_bandwidth_output: str = ""
            loaded_licenses_1_output: str = ""
            loaded_licenses_2_output: str = ""
            license_usage_on_port_output: str = ""
            optical_module_commands_1_output: str = ""
            optical_module_commands_2_output: list = []
            inventory_report_command_1_output: str = ""
            inventory_report_command_2_output: str = ""
            inventory_report_command_3_output: str = ""

            # check what options user has checked in the UI and then execute commands accordingly
            if self.ui.cb_physical_inteface.isChecked():
                physical_interface_output = SSH_connection.send_command_timing(self.physical_interface_command,
                                                                               use_ttp=if_huawei,
                                                                               ttp_template=self.physical_interface_fsm,
                                                                               read_timeout=self.read_timeout)

            if self.ui.cb_interface_decription.isChecked():
                all_interface_description_output = SSH_connection.send_command_timing(
                    self.all_interface_description_command,
                    use_ttp=True,
                    ttp_template=self.all_interface_description_fsm,
                    read_timeout=self.read_timeout)

            if self.ui.cb_trunks.isChecked():
                trunks_bandwidth_output = SSH_connection.send_command_timing(self.trunks_bandwidth_command,
                                                                             use_ttp=if_huawei,
                                                                             ttp_template=self.trunks_bandwidth_fsm,
                                                                             read_timeout=self.read_timeout)

            if self.ui.cb_licenses.isChecked():
                loaded_licenses_1_output = SSH_connection.send_command_timing(self.loaded_licenses_command_1,
                                                                              use_textfsm=if_huawei,
                                                                              read_timeout=self.read_timeout,
                                                                              textfsm_template=self.loaded_licenses_fsm_1)
                loaded_licenses_2_output = ""
                if self.identified_vendor == self.huawei_os:
                    loaded_licenses_2_output = SSH_connection.send_command_timing(self.loaded_licenses_command_2,
                                                                                  use_textfsm=if_huawei,
                                                                                  read_timeout=self.read_timeout,
                                                                                  textfsm_template=self.loaded_licenses_fsm_2)

            if self.ui.cb_optical_modules.isChecked():
                optical_module_commands_1_output = SSH_connection.send_command_timing(
                    self.optical_module_commands_1,
                    use_ttp=if_huawei,
                    read_timeout=self.read_timeout,
                    ttp_template=self.optical_module_fsm_1, last_read=4.0)
                if self.identified_vendor == self.juniper_os:
                    processed_pic_status_output = self.convert_to_json(
                        [{self.optical_module_commands_1: optical_module_commands_1_output}])

                    # this will list of dictionaries (FPCs) contiaining Pic data
                    fpcs_record = \
                        processed_pic_status_output[0][0][self.optical_module_commands_1]['fpc-information'][0]['fpc']
                    fpc_pic_record = self.get_pic_data_from_fpc_record(fpcs_record)
                    for each_fpc in fpc_pic_record:  # each_fpc will be the Key of fpc_pic_record i.e FPC slot number
                        for each_pic in fpc_pic_record[each_fpc]:  # sends individual command to router for each PIC
                            try:
                                if each_pic != []:
                                    command = f"show chassis pic fpc-slot {each_fpc} pic-slot {each_pic} | display json | no-more"
                                    temp_output = SSH_connection.send_command_timing(command,
                                                                                     read_timeout=self.read_timeout)
                                    time.sleep(1)
                                    temp_output1 = self.convert_to_json([{self.optical_module_commands_2: temp_output}])
                                    pic_port_data: dict = \
                                        temp_output1[0][0][self.optical_module_commands_2]['fpc-information'][0]['fpc'][
                                            0][
                                            'pic-detail'][0]
                                    if self.if_key_found_bool(pic_port_data, 'port-information'):
                                        if pic_port_data['port-information'][0] != {}:
                                            ports_record = pic_port_data["port-information"][0]['port']

                                        for each_port in ports_record:
                                            try:
                                                each_port_data = {'port': '', 'vendor': '', 'part_number': '',
                                                                  'type': '',
                                                                  'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''}
                                                each_port_data[
                                                    "port"] = f"{each_fpc}/{each_pic}/{each_port['port-number'][0]['data']}"
                                                each_port_data["vendor"] = self.if_key_found(each_port,
                                                                                             'sfp-vendor-name')
                                                each_port_data["part_number"] = self.if_key_found(each_port,
                                                                                                  'sfp-vendor-pno')
                                                each_port_data["type"] = self.if_key_found(each_port, 'cable-type')
                                                each_port_data["wl"] = self.if_key_found(each_port, 'wavelength')
                                                each_port_data["mode"] = self.if_key_found(each_port, 'fiber-mode')
                                                optical_module_commands_2_output.append(each_port_data)
                                            except KeyError as e:
                                                self.print_log('[KEY ERROR]', f' in {command}', traceback.format_exc())
                                                optical_module_commands_2_output.append(
                                                    {f'fpc-slot {each_fpc} pic-slot {each_pic}': '', 'vendor': '',
                                                     'part_number': '',
                                                     'type': 'DATA MISSING',
                                                     'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''})
                                                continue
                            except TypeError:
                                self.print_log('[OPTICS ERROR]', f' cannot read output for {command}',
                                               trace=traceback.format_exc())
                                optical_module_commands_2_output.append(
                                    {f'fpc-slot {each_fpc} pic-slot {each_pic}': '', 'vendor': '', 'part_number': '',
                                     'type': 'DATA MISSING',
                                     'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''})
                                continue

            if self.ui.cb_lpu_cards.isChecked(): # inventory report
                inventory_report_command_1_output = SSH_connection.send_command_timing(
                    self.inventory_report_command_1,
                    use_ttp=if_huawei,
                    read_timeout=self.read_timeout,
                    ttp_template=self.inventory_report_fsm_1, last_read=4.0)
                inventory_report_command_2_output = SSH_connection.send_command_timing(
                    self.inventory_report_command_2,
                    use_ttp=True,
                    read_timeout=self.read_timeout,
                    ttp_template=self.inventory_report_fsm_2, last_read=4.0)
                inventory_report_command_3_output = SSH_connection.send_command_timing(
                    self.inventory_report_command_3,
                    use_ttp=if_huawei,
                    read_timeout=self.read_timeout,
                    ttp_template=self.inventory_report_fsm_3, last_read=4.0)

            if self.ui.cb_port_lic_utilization.isChecked():
                license_usage_on_port_output = ""
                if self.identified_vendor == self.huawei_os:
                    license_usage_on_port_output = SSH_connection.send_command_timing(
                        self.license_usage_on_port_command,
                        use_ttp=if_huawei,
                        read_timeout=self.read_timeout,
                        ttp_template=self.license_usage_on_port_fsm)

            SSH_connection.disconnect()

            output.append([{self.physical_interface_command: physical_interface_output},
                           {self.all_interface_description_command: all_interface_description_output},
                           {self.trunks_bandwidth_command: trunks_bandwidth_output},
                           {self.loaded_licenses_command_1: loaded_licenses_1_output},
                           {self.loaded_licenses_command_2: loaded_licenses_2_output},
                           {self.license_usage_on_port_command: license_usage_on_port_output},
                           {self.optical_module_commands_1: optical_module_commands_1_output},
                           {self.optical_module_commands_2: optical_module_commands_2_output},
                           {self.inventory_report_command_1: inventory_report_command_1_output},
                           {self.inventory_report_command_2: inventory_report_command_2_output},
                           {self.inventory_report_command_3: inventory_report_command_3_output}])

        except TextFSMTemplateError as e:
            self.print_log('[FSM ERROR]', traceback.format_exc())
        except KeyError as e:
            self.print_log('[KEY ERROR]', f'in execute_command()', traceback.format_exc())
        except Exception as e:
            self.print_log('[EXECUTE COMMAND ERROR]', f'in execute_command()', traceback.format_exc())

        return output

    def extract_device_name(self, text):  # check for the patter for different vendors and returns device name
        pattern = r'<(.*?)|@(.*?)>'  # <(DEVICE_NAME)> is pattern for Huawei , @(DEVICE_NAME) is pattern for Juniper
        match = re.search(pattern, text)
        return match.group(0).strip()[1:-1] if match else self.device_ip

    def identify_device_type(self):
        self.print_log('INFO', 'Trying to identify the equipment vendor')

        unidentified_node = self.return_node_dictionary(self.unknown_os)
        device_type = self.unknown_os
        name = self.device_ip

        try:
            net_connect = ConnectHandler(**unidentified_node)
            net_connect.write_channel("\r")
            time.sleep(0.3)
            output = net_connect.read_channel()

            huawei_pattern = re.compile(r'<(.*?)>')  # Compile regex once

            # Check JUNOS or Huawei patterns in the output
            if 'JUNOS' in output:
                self.print_log('INFO', f'{self.device_ip} is identified as a Juniper node')
                device_type = self.juniper_os

            elif 'Warning: The initial password' in output or huawei_pattern.search(output):
                self.print_log('INFO', f'{self.device_ip} is identified as a Huawei node')
                device_type = self.huawei_os

                # Interact with the Huawei prompt
                net_connect.write_channel("N")
                time.sleep(0.3)
                net_connect.set_base_prompt(">")
                net_connect.write_channel("\r")
                time.sleep(0.3)
                output = net_connect.read_until_prompt()

            else:
                self.print_log('INFO', f"{self.device_ip}'s vendor is not identified. Setting it as Huawei for now")
                device_type = self.huawei_os

            net_connect.disconnect()

            # Extract device name (for Huawei, adjust output slicing as "<" is included in output)
            name = self.extract_device_name(output) if device_type != self.huawei_os else output[2:]

            self.device_state = 1

        except NetmikoAuthenticationException:
            self.print_log('[AUTHENTICATION FAILED ERROR]', traceback.format_exc())
            self.handle_failed_device()

        except Exception:
            self.print_log('[DEVICE IDENTIFICATION ERROR]', 'Unable to identify the device', traceback.format_exc())
            self.handle_failed_device()

        return name, device_type

    def convert_to_json(self, output_dict: list[dict]):
        processed_output = []
        for each_set in output_dict:
            for command, output_string in each_set.items():
                if output_string != "" and isinstance(output_string,
                                                      str):  # if there is no output or output is already processed then don't proceed
                    try:
                        if command in output_string:  # if output string contains actual command itself then commit the first two lines
                            output_string = output_string[output_string.index('no-more') + 9:]
                        processed_output.append([{command: json.loads(output_string)}])
                    except Exception as e:
                        self.print_log('[JSON CONVERSION ERROR]', traceback.format_exc())
                        with open(f"logs//{self.device_ip}_JSON_DATA.txt", "w") as JsonErrorFile:
                            JsonErrorFile.write(f"Command: {command} \n Output:\n{output_string}")
                else:
                    processed_output.append([{command: output_string}])
        return processed_output

    def _juniper_convert_to_writable_formate(self, data):
        for command in data:
            # 'physical interfaces': 'interface': '', 'link_status': '', 'port_bw': '', 'type': ''
            # 'trunks': 'interface': '', 'link_status': '', 'no_of_links': '', "members": ''
            # 'interface descriptions': 'interface': '', 'phy': '', 'opr_status': '', 'description': ''
            # 'inventory pic status': 'pic_slot': '', 'pic_sub': '', 'status': '', 'type': '', 'port_count': '', 'port_type': ''
            # 'licenses': 'description': '', 'expired_date': '', 'lic_name': '', 'avil_lic': '', 'used_lic': ''
            # 'optics': 'port': '', 'status': '', 'duplex': '', 'type': '', 'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''
            # 'version':'main_os': '', 'os_version': '', 'model': '', 'uptime': '', 'mpu_q': '', 'sru_q': '',
            #              'sfu_q': '', 'lpu_q': ''
            # 'inventory details': 'module': '', 'version': '', 'part_number': '', 'bar_code': '', 'description': ''

            if command[0].get(self.physical_interface_command):
                all_physical_interfaces: list = \
                    command[0][self.physical_interface_command]['interface-information'][0][
                        'physical-interface']
                interfaces = []
                for each_interface in all_physical_interfaces:
                    interface_type = self.if_key_found(each_interface, 'if-type')
                    if interface_type == "":
                        interface_type = self.if_key_found(each_interface, 'link-level-type')
                    if "Ethernet" in interface_type:
                        name = self.if_key_found(each_interface, 'name')
                        status = self.if_key_found(each_interface, 'oper-status')
                        speed = self.if_key_found(each_interface, 'speed')
                        interfaces.append({'interface': name,
                                           'link_status': status,
                                           'port_bw': speed,
                                           'type': interface_type})
                self.juniper_output_format['physical interfaces'] = interfaces

            if command[0].get(self.all_interface_description_command):
                interface_descriptions = []
                for each_interface in command[0][self.all_interface_description_command][0][0][
                    'interface_descriptions']:
                    name = each_interface['interface']
                    phy_status = each_interface['phy']
                    description = each_interface['description']
                    opr_status = each_interface['admin']
                    interface_descriptions.append({
                        'interface': name,
                        'phy': phy_status,
                        'opr_status': opr_status,
                        'description': description
                    })
                self.juniper_output_format['interface descriptions'] = interface_descriptions

            if command[0].get(self.trunks_bandwidth_command):
                trunks = []
                for each_interface in \
                        command[0][self.trunks_bandwidth_command]['lacp-interface-information-list'][0][
                            'lacp-interface-information']:
                    trunk_number = each_interface['lag-lacp-header'][0]['aggregate-name'][0]['data']
                    no_of_links = each_interface['lag-lacp-protocol'].__len__()
                    member_interfaces = ""
                    for each_member in each_interface['lag-lacp-protocol']:
                        try:
                            member_interfaces = member_interfaces + " , " + str(each_member['name'][0]['data'])
                        except KeyError:
                            pass
                    trunks.append({'trunk_number': trunk_number,
                                   'trunk_state': '',
                                   'no_of_links': no_of_links,
                                   'member_interfaces': member_interfaces})
                self.juniper_output_format['trunks'] = trunks

            if command[0].get(self.loaded_licenses_command_1):
                license_data = []
                lic_usage_data = []
                try:
                    lic_usage_summary = command[0][self.loaded_licenses_command_1]['license-summary-information'][0][
                        'license-usage-summary'][0]
                    if self.if_key_found_bool(lic_usage_summary, 'feature-summary'):
                        feature_summary = lic_usage_summary['feature-summary']
                        for feature in feature_summary:
                            license_data.append(
                                {'description': feature['description'][0]['data'],
                                 'expired_date': feature['validity-type'][0]['data'],
                                 'lic_name': feature['name'][0]['data']})
                            lic_usage_data.append({'lic_name': feature['name'][0]['data'],
                                                   'avil_lic': feature['licensed'][0]['data'],
                                                   'used_lic': feature['used-licensed'][0]['data']})

                    self.juniper_output_format['licenses'] = license_data
                    self.juniper_output_format['license usage'] = lic_usage_data
                except KeyError:
                    self.print_log('[LICENSE DATA ERROR]', 'cannot obtain License data', traceback.format_exc())

            try:
                if command[0].get(self.inventory_report_command_1):
                    device_fpc_and_pic_record = []
                    fpcs = data[8][0][self.inventory_report_command_1]['fpc-information'][0][
                        'fpc']
                    for each_fpc in fpcs:
                        pic_slot = each_fpc['slot'][0]['data']
                        if self.if_key_found_bool(each_fpc, 'pic'):
                            for each_pic in each_fpc['pic']:
                                pic_sub = each_pic['pic-slot'][0]['data']
                                status = each_pic['pic-state'][0]['data']
                                type = each_pic['pic-type'][0]['data']
                                search_ports = re.search(r'(\d+)(x|X)(\w+)', type)
                                port_count = search_ports.group(1) if search_ports is not None else ""
                                port_type = search_ports.group(3) if search_ports is not None else ""
                                device_fpc_and_pic_record.append({'pic_slot': pic_slot,
                                                                  'pic_sub': pic_sub,
                                                                  'status': status,
                                                                  'type': type,
                                                                  'port_count': port_count,
                                                                  'port_type': port_type})
                        else:
                            device_fpc_and_pic_record.append({'pic_slot': pic_slot,
                                                              'pic_sub': '0',
                                                              'status': each_fpc['state'][0]['data'],
                                                              'type': each_fpc['description'][0]['data'],
                                                              'port_count': '',
                                                              'port_type': ''})

                        self.juniper_output_format['inventory pic status'] = device_fpc_and_pic_record
                        fpc_slots_count = fpcs.__len__()


            except KeyError:
                fpc_slots_count = 'you can count, right ?'
                self.print_log('[PIC ERROR]', f'in (show chassis fpc pic-status ) in FPC{pic_slot}',
                               traceback.format_exc())

            if command[0].get(self.optical_module_commands_2):
                optics_data = []
                spf_filter = False if self.exe.sfp_filter == -1 else True
                all_optics = command[0][self.optical_module_commands_2]
                for each_sfp in all_optics:  # 'optics': 'port': '', 'status': '', 'duplex': '', 'type': '', 'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''
                    optics_data.append(
                        {"port": each_sfp['port'],
                         "status": "",
                         "vendor": each_sfp['vendor'],
                         "duplex": "",
                         "part_number": each_sfp['part_number'],
                         "type": each_sfp['type'],
                         "wl": each_sfp['wl'],
                         "rxpw": "",
                         "txpw": "",
                         "mode": each_sfp['mode']})
                self.juniper_output_format['optics'] = optics_data

            if command[0].get(self.inventory_report_command_2):
                self._process_show_version(command[0][self.inventory_report_command_2][0][0]['version'],
                                           fpc_slots_count)

            if command[0].get(self.inventory_report_command_3):
                hardware = self._process_show_hardware_chassis(
                    command[0][self.inventory_report_command_3]['chassis-inventory'][0]['chassis'][0]['chassis-module'])
                self.juniper_output_format['inventory details'] = hardware
        return self.juniper_output_format

    def _huawei_convert_to_writable_formate(self, data):
        if data[0].get(self.physical_interface_command):
            self.huawei_output_format['physical interfaces'] = data[0][self.physical_interface_command][0][0][
                'interface_details']

        if data[1].get(self.all_interface_description_command):
            self.huawei_output_format['interface descriptions'] = \
                data[1][self.all_interface_description_command][0][0]['record']['interface_descriptions']

        if data[2].get(self.trunks_bandwidth_command):
            trunks_data = []
            trunk_details = data[2][self.trunks_bandwidth_command][0][0]['trunk_details']

            for trunk in trunk_details:
                members = ""
                if self.if_key_found_bool(trunk, "members"):
                    members: str = self.list_dict_to_string(trunk["members"])
                trunk["member_interfaces"] = members
                trunks_data.append(trunk)
            self.huawei_output_format['trunks'] = trunks_data

        if data[6].get(self.optical_module_commands_1):
            self.huawei_output_format['optics'] = data[6][self.optical_module_commands_1][0][0]['optics']

        if data[8].get(self.inventory_report_command_1):
            self.huawei_output_format['inventory pic status'] = data[8][self.inventory_report_command_1][0][0]['pic_details']

        if data[9].get(self.inventory_report_command_2):
            self.huawei_output_format['version'] = [data[9][self.inventory_report_command_2][0][0]['version_details']]

        if data[10].get(self.inventory_report_command_3):
            self.huawei_output_format['inventory details'] = data[10][self.inventory_report_command_3][0][0]['inventory_details']

    def list_dict_to_string(self,members: list) -> str:  # takes a list of dictionaries as input and returns the string of member interfaces
        if isinstance(members, dict):  # if there is only one memeber interface in then
            return members["member_interface"]
        string = ""
        for member in members:
            string = f"{string}, {member["member_interface"]}"
        return string

    def _process_show_version(self, version_output: dict, fpc_count):
        # 'version':'main_os': '', 'os_version': '', 'model': '', 'uptime': '', 'mpu_q': '', 'sru_q': '',
        #              'sfu_q': '', 'lpu_q': ''
        main_os = f"JUNOS {version_output["main_os"].split(".")[0]}"
        os_version = f"{version_output["main_os"]}-{version_output["os_version"]}"
        model = version_output['model']
        lpu_q = fpc_count

        self.juniper_output_format['version'] = [{
            'main_os': main_os,
            'os_version': os_version,
            'model': model,
            'lpu_q': lpu_q, 'uptime': '', 'mpu_q': '', 'sru_q': '', 'sfu_q': ''}]

    def _extract_slot_details(self, slot, prefix=''):
        module = f'{prefix}{slot["name"][0]["data"]}'
        version = self.if_key_found(slot, 'version')
        part_number = self.if_key_found(slot, 'part-number')
        bar_code = self.if_key_found(slot, 'serial-number')
        description = self.if_key_found(slot, 'description')
        return {
            'module': module,
            'version': version,
            'part_number': part_number,
            'bar_code': bar_code,
            'description': description
        }

    def _process_show_hardware_chassis(self, chassis_hardware):
        each_slot_record = []

        def process_slots(slots, prefix=''):
            for slot in slots:
                each_slot_record.append(self._extract_slot_details(slot, prefix))
                if self.if_key_found_bool(slot, 'chassis-sub-module'):
                    process_slots(slot['chassis-sub-module'], prefix + ' ')
                if self.if_key_found_bool(slot, 'chassis-sub-sub-module'):
                    process_slots(slot['chassis-sub-sub-module'], prefix + '  ')

        process_slots(chassis_hardware)
        return each_slot_record

    def if_key_found(self, input: dict, key: str) -> str:
        if key in input.keys():
            try:
                return input[key][0]['data']
            except KeyError:
                return "Key Error in data"
        return ""

    def if_key_found_bool(self, input: dict, key: str) -> bool:
        if key in input.keys():
            return True
        return False

    def get_pic_data_from_fpc_record(self, fpcs: list[dict]) -> dict:
        fpc_pic_record = {}
        for each_fpc in fpcs:  # Gets all the online FPCs as fpc_pic_record "keys" and relevant PICs (a list) as the "value"
            pic_slots = []
            fpc_slot = each_fpc['slot'][0]['data']  # FPC slot number
            if 'pic' in each_fpc.keys():  # iterates over FPC slot to get PIC numbers
                for each_pic in each_fpc['pic']:
                    pic_slots.append(each_pic['pic-slot'][0]['data'])
            fpc_pic_record.update({fpc_slot: pic_slots})
        return fpc_pic_record

    def print_log(self, log_type: str, message: str = "", trace=None):
        if 'ERROR' in log_type:
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number}) -> {log_type} : {message} : Device IP is {self.device_ip}, \n {trace}')
        else:
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number}) ->  {message} : Device IP is {self.device_ip}')
