import sys
import threading

from openpyxl import Workbook
import textfsm
from openpyxl.styles import PatternFill, Alignment
from openpyxl.styles import Font

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
            'M1': 'TRUNK NUMBER', 'N1': 'TRUNK STATE','O1': 'TOTAL LINKS','P1': 'MEMBERS INTERFACES',
            'S1': 'LICENSE DESCRIPTION', 'T1': 'AVAILABLE LICENSES', 'U1': 'USED LICENSES',
            'V1': 'LICENSE EXPIRY', 'W1': 'ITEM NAME',
            'N30': 'SLOT', 'O30': 'SUB SLOT', 'P30': 'STATUS',
            'Q30': 'TYPE', 'R30': 'PORT COUNT',
            'Z1': 'PORT', 'AA1': 'STATUS', 'AB1': 'DUPLEX',
            'AC1': 'TYPE', 'AD1': 'WL', 'AE1': 'RX POWER', 'AF1': 'TX POWER', 'AG1': 'MODE',
            'AI1': 'CHASSIS DETAILS', 'AI2': 'VRP VERSION', 'AI3': 'SOFTWARE VERSION',
            'AI4': 'MODEL', 'AI5': 'UPTIME', 'AI8': 'SFU SLOTS', 'AI9': 'LPU SLOTS',
            'AI11': 'MODULE TYPE', 'AK11': 'BOARD TYPE', 'AL11': 'BAR CODE', 'AM11': 'DESCRIPTION'
        }

        worksheet.column_dimensions['P'].width = 20
        worksheet.column_dimensions['D'].width = 40

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
            if cell.startswith(('P')):
                worksheet[cell].alignment = Alignment(horizontal='left',vertical='center', wrap_text=True)

        # Write data to worksheet
        def write_data(data, start_row, columns):
            for row, item in enumerate(data, start=start_row):
                for col, key in columns.items():
                    worksheet[f"{col}{row}"] = item[key]

        write_data(interface_descriptions, 2, {'A': 'interface', 'B': 'phy', 'C': 'opr_status', 'D': 'description'})
        write_data(physical_interfaces, 2, {'G': 'interface', 'H': 'link_status', 'I': 'port_bw', 'J':'type'})
        write_data(trunks, 2, {'M': 'trunk_number','O': 'no_of_links','P': 'member_interfaces'})
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
