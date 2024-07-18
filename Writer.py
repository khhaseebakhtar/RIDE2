import sys
import threading

from openpyxl import Workbook
import textfsm
from openpyxl.styles import PatternFill
from openpyxl.styles import Font


def make_file(output, sheet_name, path,vendor):
    int_des = output['interface description']
    dis_int = output['physical interfaces']
    dis_int_eth = output['trunks']
    int_lic = output['licenses']
    lic_res = output['license usage']
    pic_status = output['inventory pic status']
    opt_module = output['optics']
    port_basic = output['license usage on ports']
    dis_version = output['version']
    dis_elable_brief = output['inventory details']

    new_workbook = Workbook()
    work_sheet = new_workbook.active
    work_sheet.title = sheet_name

    work_sheet['A1'] = 'INTERFACE'
    work_sheet['B1'] = 'PHY STATE'
    work_sheet['C1'] = 'DESCRIPTION'
    work_sheet['E1'] = 'PHYSICAL INTERFACE'
    work_sheet['F1'] = 'PHY STATE'
    work_sheet['G1'] = 'PORT BANDWIDTH'
    work_sheet['I1'] = 'TRUNK NUMBER'
    work_sheet['J1'] = 'TRUNK STATE'

    work_sheet['N1'] = 'LICENSE DESCRIPTION'
    work_sheet['O1'] = 'AVAILABLE LICENSES'
    work_sheet['P1'] = 'USED  LICENSES'
    work_sheet['Q1'] = 'LICENSE EXPIRY '
    work_sheet['R1'] = 'ITEM NAME '
    work_sheet['N20'] = 'SLOT '
    work_sheet['O20'] = 'SUB SLOT '
    work_sheet['P20'] = 'STATUS '
    work_sheet['Q20'] = 'TYPE '
    work_sheet['R20'] = 'PORT COUNT'
    work_sheet['T1'] = 'PORT '
    work_sheet['U1'] = 'STATUS'
    work_sheet['V1'] = 'DUPLEX'
    work_sheet['W1'] = 'TYPE'
    work_sheet['X1'] = 'WL'
    work_sheet['Y1'] = 'RX POWER'
    work_sheet['Z1'] = 'TX POWER'
    work_sheet['AA1'] = 'MODE'

    work_sheet['AI1'] = 'CHASSIS DETAILS'
    work_sheet['AI2'] = 'VRP VERSION'
    work_sheet['AI3'] = 'SOFTWARE VERSION'
    work_sheet['AI4'] = 'MODEL'
    work_sheet['AI5'] = 'UPTIME'

    work_sheet['AI8'] = 'SFU SLOTS'
    work_sheet['AI9'] = 'LPU SLOTS'
    work_sheet['AI11'] = 'MODULE TYPE'

    work_sheet['AK11'] = 'BOARD TYPE'
    work_sheet['AL11'] = 'BAR CODE'
    work_sheet['AM11'] = 'DESCRIPTION'

    if 'huawei' in vendor:
        work_sheet['K1'] = 'MAX BANDWIDTH'
        work_sheet['L1'] = 'AVAILABLE BANDWIDTH'
        work_sheet['AI6'] = 'MPU SLOTS'
        work_sheet['AI7'] = 'SRU SLOTS'
        work_sheet['AC1'] = 'PORT'
        work_sheet['AD1'] = 'FEATURE NAME'
        work_sheet['AE1'] = 'NEEDED COUNT'
        work_sheet['AF1'] = 'USED COUNT'
        work_sheet['AG1'] = 'STATUS'
        work_sheet['AJ11'] = 'SLOT NUMBER'

    if 'juniper' in vendor:
        work_sheet['K1'] = 'NO OF LINKS'
        work_sheet['L1'] = 'MEMBER INTERFACES'
        work_sheet['AI6'] = '<MPU SLOTS>'
        work_sheet['AI7'] = '<SRU SLOTS>'
        work_sheet['AJ11'] = 'VERSION'

    # --------------- STYLING ---------------------------
    red_fill = PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')
    yellow_fill = PatternFill(start_color='00FFFF00', end_color='00FFFF00', fill_type='solid')
    blue_fill = PatternFill(start_color='00CCFFCC', end_color='00CCFFCC', fill_type='solid')
    work_sheet['A1'].fill = yellow_fill
    work_sheet['B1'].fill = yellow_fill
    work_sheet['C1'].fill = yellow_fill
    work_sheet['E1'].fill = blue_fill
    work_sheet['F1'].fill = blue_fill
    work_sheet['G1'].fill = blue_fill
    work_sheet['I1'].fill = red_fill
    work_sheet['J1'].fill = red_fill
    work_sheet['K1'].fill = red_fill
    work_sheet['L1'].fill = red_fill
    work_sheet['N1'].fill = yellow_fill
    work_sheet['O1'].fill = yellow_fill
    work_sheet['P1'].fill = yellow_fill
    work_sheet['Q1'].fill = yellow_fill
    work_sheet['R1'].fill = yellow_fill
    work_sheet['N20'].fill = blue_fill
    work_sheet['O20'].fill = blue_fill
    work_sheet['P20'].fill = blue_fill
    work_sheet['Q20'].fill = blue_fill
    work_sheet['R20'].fill = blue_fill
    work_sheet['T1'].fill = red_fill
    work_sheet['U1'].fill = red_fill
    work_sheet['U1'].fill = red_fill
    work_sheet['V1'].fill = red_fill
    work_sheet['W1'].fill = red_fill
    work_sheet['X1'].fill = red_fill
    work_sheet['Y1'].fill = red_fill
    work_sheet['Z1'].fill = red_fill
    work_sheet['AA1'].fill = red_fill
    work_sheet['AC1'].fill = yellow_fill
    work_sheet['AD1'].fill = yellow_fill
    work_sheet['AE1'].fill = yellow_fill
    work_sheet['AF1'].fill = yellow_fill
    work_sheet['AG1'].fill = yellow_fill
    work_sheet['AI1'].fill = blue_fill
    work_sheet['AI11'].fill = blue_fill
    work_sheet['AJ11'].fill = blue_fill
    work_sheet['AK11'].fill = blue_fill
    work_sheet['AL11'].fill = blue_fill
    work_sheet['AM11'] .fill = blue_fill

    font = Font(name='Calibri', size=12, bold=True)
    work_sheet['A1'].font = font
    work_sheet['B1'].font = font
    work_sheet['C1'].font = font
    work_sheet['E1'].font = font
    work_sheet['F1'].font = font
    work_sheet['G1'].font = font
    work_sheet['I1'].font = font
    work_sheet['J1'].font = font
    work_sheet['K1'].font = font
    work_sheet['L1'].font = font
    work_sheet['N1'].font = font
    work_sheet['O1'].font = font
    work_sheet['P1'].font = font
    work_sheet['Q1'].font = font
    work_sheet['R1'].font = font
    work_sheet['N20'].font = font
    work_sheet['O20'].font = font
    work_sheet['P20'].font = font
    work_sheet['Q20'].font = font
    work_sheet['R20'].font = font
    work_sheet['T1'].font = font
    work_sheet['U1'].font = font
    work_sheet['V1'].font = font
    work_sheet['W1'].font = font
    work_sheet['X1'].font = font
    work_sheet['Y1'].font = font
    work_sheet['Z1'].font = font
    work_sheet['AA1'].font = font
    work_sheet['AC1'].font = font
    work_sheet['AD1'].font = font
    work_sheet['AE1'].font = font
    work_sheet['AF1'].font = font
    work_sheet['AG1'].font = font
    work_sheet['AI1'].font = font
    work_sheet['AI2'].font = font
    work_sheet['AI3'].font = font
    work_sheet['AI4'].font = font
    work_sheet['AI5'].font = font
    work_sheet['AI6'].font = font
    work_sheet['AI7'].font = font
    work_sheet['AI8'].font = font
    work_sheet['AI9'].font = font
    work_sheet['AI11'].font = font
    work_sheet['AJ11'].font = font
    work_sheet['AK11'].font = font
    work_sheet['AL11'].font = font
    work_sheet['AM11'].font = font
    # ----------------------------- Writing Outputs ---------------------------------
    row_number = 2
    for interface_details in int_des:  # Writes all interfaces their physical status and descriptions
        cell = str(row_number)
        work_sheet['A' + cell] = interface_details['interface']
        work_sheet['B' + cell] = interface_details['phy']
        work_sheet['C' + cell] = interface_details['description']
        row_number += 1

    row_number = 2
    for interface_details in dis_int:  # Writes only physical interfaces their physical status and Bandwidth
        cell = str(row_number)
        work_sheet['E' + cell] = interface_details['interface']  # Interface
        work_sheet['F' + cell] = interface_details['link_status']  # Link Status
        work_sheet['G' + cell] = interface_details['port_bw']  # Bandwidth

        row_number += 1

    row_number = 2
    for interface_details in dis_int_eth:  # Writes only Eth-Trunks i their physical status Max and current Bandwidth
        cell = str(row_number)
        work_sheet['I' + cell] = interface_details['interface']  # Interface
        work_sheet['J' + cell] = interface_details['link_status']  # Link Status
        work_sheet['K' + cell] = interface_details['max_bw']  # Max Bandwidth
        work_sheet['L' + cell] = interface_details['current_bw']  # Current Bandwidth
        row_number += 1

    row_number = 2
    for interface_details in int_lic:  # Writes all interfaces their physical status and descriptions
        cell = str(row_number)
        work_sheet['N' + cell] = interface_details['description']  # LICENSE DESCRIPTION
        work_sheet['Q' + cell] = interface_details['expired_date']  # LICENSE EXPIRY
        for license_resources in lic_res:
            if license_resources['lic_name'] == interface_details['lic_name'] or license_resources['lic_name'] == \
                    interface_details['lic_name'] + " ":
                work_sheet['O' + cell] = license_resources['avil_lic']  # AVAILABLE LICENSES
                work_sheet['P' + cell] = license_resources['used_lic']  # USED  LICENSES
                work_sheet['R' + cell] = license_resources['lic_name']  # LICENSE NAME
        row_number += 1

    row_number = 21
    for device_pic_status in pic_status:  # Writes Pic status in file
        cell = str(row_number)
        work_sheet['N' + cell] = device_pic_status['pic_slot']  # SLOT
        work_sheet['O' + cell] = device_pic_status['pic_sub']  # SUB_SLOT
        work_sheet['P' + cell] = device_pic_status['status']  # STATUS
        work_sheet['Q' + cell] = device_pic_status['type']  # LPU
        work_sheet['R' + cell] = device_pic_status['port_count']  # PORT COUNT
        row_number += 1

    row_number = 2
    for opt_module_detail in opt_module:  # Writes all interfaces their physical status and descriptions
        cell = str(row_number)
        work_sheet['T' + cell] = opt_module_detail['port']  # PORT
        work_sheet['U' + cell] = opt_module_detail['status']  # STATUS
        work_sheet['V' + cell] = opt_module_detail['duplex']  # DUPLEX
        work_sheet['W' + cell] = opt_module_detail['type']  # TYPE
        work_sheet['X' + cell] = opt_module_detail['wl']  # Wavelength
        work_sheet['Y' + cell] = opt_module_detail['rxpw']  # RxPower
        work_sheet['Z' + cell] = opt_module_detail['txpw']  # TxPower
        work_sheet['AA' + cell] = opt_module_detail['mode']  # MODE

        row_number += 1

    row_number = 2
    for port_basic_detail in port_basic:
        cell = str(row_number)
        work_sheet['AC' + cell] = port_basic_detail['port']
        work_sheet['AD' + cell] = port_basic_detail['fname']
        work_sheet['AE' + cell] = port_basic_detail['ncount']
        work_sheet['AF' + cell] = port_basic_detail['ucount']
        work_sheet['AG' + cell] = port_basic_detail['status']
        row_number += 1

    work_sheet['AJ2'] = dis_version[0]['vrp_version']
    work_sheet['AJ3'] = dis_version[0]['product_version']
    work_sheet['AJ4'] = dis_version[0]['model']
    work_sheet['AJ5'] = dis_version[0]['uptime']
    work_sheet['AJ6'] = (dis_version[0]['mpu_q'])
    work_sheet['AJ7'] = (dis_version[0]['sru_q'])
    work_sheet['AJ8'] = (dis_version[0]['sfu_q'])
    work_sheet['AJ9'] = (dis_version[0]['lpu_q'])

    row_number = 12
    for elable in dis_elable_brief:
        cell = str(row_number)
        work_sheet['AI' + cell] = elable['module']
        if elable['module'] == 'PIC':
            work_sheet['AJ' + cell] = 'sub slot'+elable['slot_no']
        else:
            work_sheet['AJ' + cell] = elable['slot_no']

        work_sheet['AK' + cell] = elable['board_type']
        work_sheet['AL' + cell] = elable['bar_code']
        work_sheet['AM' + cell] = elable['description']
        row_number += 1

    new_workbook.save(path + "/" + sheet_name + ".xlsx")

def make_file1(output, sheet_name, path, vendor):

        physical_interfaces = output['physical interfaces']
        trunks = output['trunks']
        interface_descriptions = output['interface descriptions']
        inventory_pic_status = output['inventory pic status']
        licenses = output['licenses']
        optics = output['optics']
        version_info = output['version']
        inventory_details = output['inventory details']
        #license_usage = output['license usage']


        #port_license_usage = output['license usage on ports']



        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = sheet_name

        # Define headers and their positions
        headers = {
            'A1': 'INTERFACE', 'B1': 'PHY STATE', 'C1': 'ADMIN STATUS','D1': 'DESCRIPTION',
            'G1': 'PHYSICAL INTERFACE', 'H1': 'PHY STATE', 'I1': 'PORT BANDWIDTH','J1': 'LINK TYPE',
            'M1': 'TRUNK NUMBER', 'N1': 'TRUNK STATE','O1': 'TOTAL LINKS','P1': 'MEMBERS',
            'S1': 'LICENSE DESCRIPTION', 'T1': 'AVAILABLE LICENSES', 'U1': 'USED LICENSES',
            'V1': 'LICENSE EXPIRY', 'W1': 'ITEM NAME',
            'N20': 'SLOT', 'O20': 'SUB SLOT', 'P20': 'STATUS',
            'Q20': 'TYPE', 'R20': 'PORT COUNT',
            'Z1': 'PORT', 'AA1': 'STATUS', 'AB1': 'DUPLEX',
            'AC1': 'TYPE', 'AD1': 'WL', 'AE1': 'RX POWER', 'AF1': 'TX POWER', 'AG1': 'MODE',
            'AI1': 'CHASSIS DETAILS', 'AI2': 'VRP VERSION', 'AI3': 'SOFTWARE VERSION',
            'AI4': 'MODEL', 'AI5': 'UPTIME', 'AI8': 'SFU SLOTS', 'AI9': 'LPU SLOTS',
            'AI11': 'MODULE TYPE', 'AK11': 'BOARD TYPE', 'AL11': 'BAR CODE', 'AM11': 'DESCRIPTION'
        }

        # Add vendor-specific headers
        if 'huawei' in vendor:
            pass

        if 'juniper' in vendor:
            pass

        # Apply headers and their styles
        yellow_fill = PatternFill(start_color='00FFFF00', end_color='00FFFF00', fill_type='solid')
        blue_fill = PatternFill(start_color='00CCFFCC', end_color='00CCFFCC', fill_type='solid')
        red_fill = PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')
        header_font = Font(name='Calibri', size=12, bold=True)

        for cell, value in headers.items():
            worksheet[cell] = value
            worksheet[cell].font = header_font
            if cell.startswith(('A', 'B', 'C', 'D', 'S1', 'T1', 'U1', 'Q20','R20','AI1','AI2')):
                worksheet[cell].fill = yellow_fill
            elif cell.startswith(('G', 'H', 'I', 'J', 'V', 'W1', 'Z', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG')):
                worksheet[cell].fill = blue_fill
            else:
                worksheet[cell].fill = red_fill

        # Write data to worksheet
        def write_data(data, start_row, columns):
            for row, item in enumerate(data, start=start_row):
                for col, key in columns.items():
                    worksheet[f"{col}{row}"] = item[key]

        write_data(interface_descriptions, 2, {'A': 'interface', 'B': 'phy', 'C': 'opr_status', 'D': 'description'})
        write_data(physical_interfaces, 2, {'G': 'interface', 'H': 'link_status', 'I': 'port_bw', 'J':'type'})
       # write_data(trunks, 2, {'M': 'interface', 'N': 'link_status', 'O': 'max_bw', 'P': 'current_bw'})
        write_data(optics, 2,
                   {'Z': 'port', 'AA': 'status', 'AB': 'duplex', 'AC': 'type', 'AD': 'wl', 'AE': 'rxpw', 'AF': 'txpw',
                    'AG': 'mode'})
        #write_data(port_license_usage, 2, {'AC': 'port', 'AD': 'fname', 'AE': 'ncount', 'AF': 'ucount', 'AG': 'status'})
        #write_data(inventory_pic_status, 21,
                   #{'N': 'pic_slot', 'O': 'pic_sub', 'P': 'status', 'Q': 'type', 'R': 'port_count'})
       # write_data(inventory_details, 12,
                   #{'AI': 'module', 'AJ': 'slot_no', 'AK': 'board_type', 'AL': 'bar_code', 'AM': 'description'})

        # for row, item in enumerate(licenses, start=2):
        #     cell = str(row)
        #     worksheet[f'N{cell}'] = item['description']
        #     worksheet[f'Q{cell}'] = item['expired_date']
        #     for lic in license_usage:
        #         if lic['lic_name'].strip() == item['lic_name'].strip():
        #             worksheet[f'O{cell}'] = lic['avil_lic']
        #             worksheet[f'P{cell}'] = lic['used_lic']
        #             worksheet[f'R{cell}'] = lic['lic_name']
        #
        # worksheet['AJ2'] = version_info[0]['vrp_version']
        # worksheet['AJ3'] = version_info[0]['product_version']
        # worksheet['AJ4'] = version_info[0]['model']
        # worksheet['AJ5'] = version_info[0]['uptime']
        # worksheet['AJ6'] = version_info[0]['mpu_q']
        # worksheet['AJ7'] = version_info[0]['sru_q']
        # worksheet['AJ8'] = version_info[0]['sfu_q']
        # worksheet['AJ9'] = version_info[0]['lpu_q']

        # Save workbook
        workbook.save(f"{path}/{sheet_name}.xlsx")


class Writer():
    def __init__(self, output, device_name, path, vendor):
        self.t = threading.Thread(args=(device_name, output, path,vendor), target=make_file1(output, device_name, path,vendor))
        self.t.start()
