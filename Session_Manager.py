import json
import pprint
import re
import time
import traceback

from PyQt5.QtCore import QObject
from netmiko import ConnectHandler, NetmikoAuthenticationException
from textfsm import TextFSMTemplateError
from Writer import Writer


def extract_device_name(text):  # check for the patter for different vendors and returns device name
    pattern = r'<(.*?)>|@(.*?)>'  # <(DEVICE_NAME)> is pattern for Huawei , @(DEVICE_NAME) is pattern for Juniper
    match = re.search(pattern, text)
    return match.group(0).strip()[1:-1] if match else "<cant read name>"


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
        exe.Thread_control += 1

        self.huawei_output_format = {
            'physical interfaces': [{'interface': '', 'link_status': '', 'port_bw': ''}],
            'Trunks': [{'interface': '', 'link_status': '', 'max_bw': '', "current_bw": ''}],
            'interface descriptions': [{'interface': '', 'phy': '', 'description': ''}],
            'inventory pic status': [{'pic_slot': '', 'pic_sub': '', 'status': '', 'type': '', 'port_count': ''}],
            'licenses': [{'description': '', 'expired_date': '', 'lic_name': ''}],
            'license usage': [{'lic_name': '', 'avil_lic': '', 'used_lic': ''}],
            'optics': [
                {'port': '', 'status': '', 'duplex': '', 'type': '', 'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''}],
            'license usage on ports': [
                {'port': '', 'fname': '', 'ncount': '', 'ucount': '', 'status': ''}],
            'version': [{'vrp_version': '', 'product_version': '', 'model': '', 'uptime': '', 'mpu_q': '', 'sru_q': '',
                         'sfu_q': '', 'lpu_q': ''}],
            'inventory details': [{'module': '', 'slot_no': '', 'board_type': '', 'bar_code': '', 'description': ''}]

        }

        self.juniper_output_format = {
            'physical interfaces': [{'interface': '', 'link_status': '', 'port_bw': '', 'type': ''}],
            'trunks': [{'trunk_number': '', 'no_of_links': '', "member_interfaces": ''}],
            'interface descriptions': [{'interface': '', 'phy': '', 'opr_status': '', 'description': ''}],
            'inventory pic status': [{'pic_slot': '', 'pic_sub': '', 'status': '', 'type': '', 'port_count': ''}],
            'licenses': [{'description': '', 'expired_date': '', 'lic_name': '', 'avil_lic': '', 'used_lic': ''}],
            'optics': [
                {'port': '', 'status': "", 'vendor': '', 'duplex': '', 'part_number': '', 'type': '', 'wl': '',
                 'rxpw': '', 'txpw': '', 'mode': ''}],
            'version': [{'vrp_version': '', 'product_version': '', 'model': '', 'uptime': '', 'mpu_q': '', 'sru_q': '',
                         'sfu_q': '', 'lpu_q': ''}],
            'inventory details': [{'module': '', 'version': '', 'board_type': '', 'bar_code': '', 'description': ''}]

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
                'username': self.ui.le_username.text(),
                'password': self.ui.le_password.text(),
                'session_timeout': 300,
                'session_log': f"logs//{self.device_ip}.log",
                }

    def start_execution(self):
        self.device_name, self.identified_vendor = self.identify_device_type()
        if self.device_state:
            self.set_command_set(vendor=self.identified_vendor)
            self.make_connection()

    def set_command_set(self, vendor: str):
        if vendor == self.huawei_os:
            self.physical_interface_command: str = 'display interface | no-more'
            self.all_interface_description_command: str = "display interface description | no-more"
            self.trunks_bandwidth_command: str = "display interface eth-trunk | no-more"
            self.loaded_licenses_command_1: str = "display license verbose | no-more"
            self.loaded_licenses_command_2: str = "display license resource usage | no-more"
            self.license_usage_on_port_command: str = "display license resource usage port-basic all | no-more"
            self.optical_module_commands_1: str = "display optical-module brief | no-more"
            self.inventory_report_command_1: str = "display device "
            self.inventory_report_command_2: str = "display version | no-more"
            self.inventory_report_command_3: str = "display device elabel | no-more"

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
            self.physical_interface_command: str = "show interfaces detail | display json | no-more"
            self.all_interface_description_command: str = "show interfaces descriptions"
            self.trunks_bandwidth_command: str = "show lacp interfaces | display json | no-more"
            self.loaded_licenses_command_1: str = "show system license detail | display json | no-more"
            self.optical_module_commands_1: str = "show chassis fpc pic-status | display json | no-more"
            self.optical_module_commands_2: str = "show chassis pic fpc-slot"
            self.inventory_report_command_1: str = "show chassis fpc pic-status | display json | no-more "
            self.inventory_report_command_2: str = "show version | display json | no-more"
            self.inventory_report_command_3: str = "show chassis hardware | display json | no-more "

            self.all_interface_description_fsm: str = "TEXT_FSM_FILES//juniper_junos_show_interfaces_description"



    def make_connection(self):
        if self.device_state:  # if device is identified as accessible : proceed with setting up SSH
            self.exe.sig.set_logging_signal.emit(f"({self.device_number}) -> Accessing Device at {self.device_ip}")
            router = self.return_node_dictionary(self.identified_vendor)
            try:
                self.exe.device_name_list.append(self.device_name)
                output = self.execute_commands(router)

                if output != [] and self.identified_vendor == self.juniper_os:
                    structured_output = self.convert_to_json(output[0])
                    self.convert_to_writable_formate(structured_output)
                self.exe.Thread_control -= 1
                self.exe.sig.set_logging_signal.emit(
                    f'({self.device_number}) -> Data Collection Done for {self.device_name} ')
                Writer(self.juniper_output_format, self.device_name, self.exe.output_file_path,self.identified_vendor)  # initiating the data writing
                self.exe.sig.set_logging_signal.emit(f'({self.device_number}) -> File Saved for {self.device_name} ')
                self.exe.successful_device_count += 1

            except KeyError as e:
                self.exe.sig.set_logging_signal.emit(
                    f'({self.device_number}) -> [JSON CONVERSION ERROR] : cannot obtain processed output, \n {traceback.format_exc()}')
                self.handle_failed_device()
            except Exception as e:
                self.exe.sig.set_logging_signal.emit(
                    f'({self.device_number}) -> [MAKE CONNECTION ERROR] :, \n {traceback.format_exc()}')
                self.handle_failed_device()

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
                                                                               use_textfsm=if_huawei,
                                                                               textfsm_template=self.physical_interface_fsm, )

            if self.ui.cb_interface_decription.isChecked():
                all_interface_description_output = SSH_connection.send_command_timing(
                    self.all_interface_description_command,
                    use_textfsm=True,
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
                optical_module_commands_1_output = SSH_connection.send_command_timing(
                    self.optical_module_commands_1,
                    use_textfsm=if_huawei,
                    textfsm_template=self.optical_module_fsm_1)
                if self.identified_vendor == self.juniper_os:
                    processed_pic_status_output = self.convert_to_json(
                        [{self.optical_module_commands_1: optical_module_commands_1_output}])
                    fpcs_record = \
                        processed_pic_status_output[0][0]['show chassis fpc pic-status | display json | no-more'][
                            'fpc-information'][0]['fpc']

                    fpc_pic_record = {}
                    for each_fpc in fpcs_record:
                        pic_slots = []
                        fpc_slot = each_fpc['slot'][0]['data']
                        if 'pic' in each_fpc.keys():
                            for each_pic in each_fpc['pic']:
                                pic_slots.append(each_pic['pic-slot'][0]['data'])
                        fpc_pic_record.update({fpc_slot: pic_slots})
                    for each_fpc in fpc_pic_record:  #each_fpc will be the Key of fpc_pic_record i.e FPC slot number
                        for each_pic in fpc_pic_record[each_fpc]:
                            if each_pic != []:
                                command = f"show chassis pic fpc-slot {each_fpc} pic-slot {each_pic} | display json | no-more"
                                temp_output = SSH_connection.send_command_timing(command)
                                temp_output1 = self.convert_to_json([{"show chassis pic fpc-slot": temp_output}])
                                pic_port_data: dict = \
                                    temp_output1[0][0]['show chassis pic fpc-slot']['fpc-information'][0]['fpc'][0][
                                        'pic-detail'][0]
                                if 'port-information' in pic_port_data.keys():
                                    if pic_port_data['port-information'][0] != {}:
                                        ports_record = pic_port_data["port-information"][0]['port']

                                    for each_port in ports_record:
                                        try:
                                            each_port_data = {'port': '', 'vendor': '', 'part_number': '', 'type': '',
                                                              'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''}
                                            each_port_data[
                                                "port"] = f"{each_fpc}/{each_pic}/{each_port['port-number'][0]['data']}"
                                            each_port_data["vendor"] = each_port['sfp-vendor-name'][0]['data']
                                            each_port_data["part_number"] = each_port['sfp-vendor-pno'][0]['data']
                                            each_port_data["type"] = each_port['cable-type'][0]['data']
                                            each_port_data["wl"] = each_port['wavelength'][0]['data']
                                            each_port_data["mode"] = each_port['fiber-mode'][0]['data']
                                            optical_module_commands_2_output.append(each_port_data)
                                        except KeyError as e:
                                            self.exe.sig.set_logging_signal.emit(
                                                f'({self.device_number}) -> [KEY ERROR]: in getting Optics data\n'
                                                f' [Error Command] : {command}\n'
                                                f'[Error Device] : {self.device_name}\n {traceback.format_exc()} ')

                            pass

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
                if self.identified_vendor == self.juniper_os:
                    license_usage_on_port_output = SSH_connection.send_command_timing(self.loaded_licenses_command_1,
                                                                                      use_textfsm=if_huawei,
                                                                                      textfsm_template=self.loaded_licenses_fsm_1)

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
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number}) -> [FSM ERROR]: for  {self.device_name}, \n {traceback.format_exc()}')

        except KeyError as e:
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number}) -> [KEY ERROR]: in execute_command()  {self.device_name}, \n {traceback.format_exc()} ')

        except Exception as e:
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number}) -> [COMMAND EXECUTION ERROR]: in execute_command()  for {self.device_name}, \n {traceback.format_exc()}')
        return output

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
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number}) -> [DEVICE IDENTIFCAION ERROR] : for {self.device_name}, in identify_device_type \n {traceback.format_exc()}')
            self.handle_failed_device()

        except Exception as e:
            self.exe.sig.set_logging_signal.emit(
                f'({self.device_number}) -> [DEVICE IDENTIFCAION ERROR] : for {self.device_name}, in identify_device_type \n {traceback.format_exc()}')
            self.handle_failed_device()
        return name, device_type

    def convert_to_json(self, output_dict: list[dict]):
        processed_output = []
        for each_set in output_dict:
            for command, output_string in each_set.items():
                #pprint.pprint(f"[1]- command  : {command}\n[1]- output : {output_string} ")
                if output_string != "" and isinstance(output_string,
                                                      str):  # if there is no output or output is already processed then don't proceed
                    try:
                        if command in output_string:  # if output string contains actual command itself then commit the first two lines
                            output_string = "\n".join(output_string.split("\n")[2:])
                        processed_output.append([{command: json.loads("\n".join(output_string.split("\n")[2:]))}])
                    except json.decoder.JSONDecodeError as e:
                        processed_output.append([{command: json.loads(output_string)}])
                    except Exception as e:
                        self.exe.sig.set_logging_signal.emit(
                            f'({self.device_number}) -> [JSON CONVERSION ERROR] in {command}: for {self.device_name}, \n {traceback.format_exc()}')
                else:
                    processed_output.append([{command: output_string}])
        return processed_output

    def convert_to_writable_formate(self, data):
        for command in data:
            keys = command[0].keys()
            # 'physical interfaces': 'interface': '', 'link_status': '', 'port_bw': '', 'type': ''
            # 'trunks': 'interface': '', 'link_status': '', 'no_of_links': '', "members": ''
            # 'interface descriptions': 'interface': '', 'phy_status': '', 'opr_status': '', 'description': ''
            # 'inventory pic status': 'pic_slot': '', 'pic_sub': '', 'status': '', 'type': '', 'port_count': ''
            # 'licenses': 'description': '', 'expired_date': '', 'lic_name': '', 'avil_lic': '', 'used_lic': ''
            # 'optics': 'port': '', 'status': '', 'duplex': '', 'type': '', 'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''
            # 'version':'vrp_version': '', 'product_version': '', 'model': '', 'uptime': '', 'mpu_q': '', 'sru_q': '',
            #              'sfu_q': '', 'lpu_q': ''
            # 'inventory details': 'module': '', 'version': '', 'board_type': '', 'bar_code': '', 'description': ''

            if 'show interfaces detail | display json | no-more' in keys and command[0][
                'show interfaces detail | display json | no-more'] != "":
                all_physical_interfaces: list = \
                    command[0]['show interfaces detail | display json | no-more']['interface-information'][0][
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



            if 'show interfaces descriptions' in keys and command[0][
                'show interfaces descriptions'] != "":
                interface_descriptions = []
                for each_interface in command[0]['show interfaces descriptions']:
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
                self.juniper_output_format['interface descriptions']= interface_descriptions


            if 'show lacp interfaces | display json | no-more' in keys and command[0]['show lacp interfaces | display json | no-more'] != "":
                trunks = []
                for each_interface in command[0]['show lacp interfaces | display json | no-more']['lacp-interface-information-list'][0]['lacp-interface-information']:
                    trunk_number = each_interface['lag-lacp-header'][0]['aggregate-name'][0]['data']
                    no_of_links = each_interface['lag-lacp-protocol'].__len__()
                    member_interfaces = ""
                    for each_member in each_interface['lag-lacp-protocol']:
                        try:
                            member_interfaces = member_interfaces+" \n"+str(each_member['name'][0]['data'])
                        except KeyError:
                            pass
                    trunks.append({'trunk_number' : trunk_number,
                                       'no_of_links': no_of_links,
                                       'member_interfaces': member_interfaces})
                self.juniper_output_format['trunks'] = trunks

            if 'show system license detail | display json | no-more' in keys and command[0][
                'show system license detail | display json | no-more'] != "":
                pass
            if 'show chassis fpc pic-status | display json | no-more' in keys and command[0][
                'show chassis fpc pic-status | display json | no-more'] != "":
                pass

            if 'show chassis pic fpc-slot' in keys and command[0]['show chassis pic fpc-slot']:
                optics_data = []
                all_optics = command[0]['show chassis pic fpc-slot']
                for each_sfp in all_optics:  # 'optics': 'port': '', 'status': '', 'duplex': '', 'type': '', 'wl': '', 'rxpw': '', 'txpw': '', 'mode': ''
                    if '100G' in each_sfp['type'] :
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
                self.juniper_output_format['optics']= optics_data



            if 'show version | display json | no-more' in keys:
                pass
            if 'show chassis hardware | display json | no-more' in keys:
                pass

        return self.juniper_output_format

    def if_key_found(self, input: dict, key: str):
        if key in input.keys():
            return input[key][0]['data']
        return ""

    def huawei_output(self, data):
        pass
