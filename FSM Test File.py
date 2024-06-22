'''
1- Read the IP From File and store in a list
2- Get the SSH connection for each device
3- Retrieve Interface Details
4- Store Interface Details and Summary in new Excel Sheet
5- Repeat from Step 2 for next IP until all the IPs are covered
'''
import traceback
import textfsm
from netmiko import ConnectHandler
from getpass import getpass
from pprint import pprint
from openpyxl import Workbook
from openpyxl import load_workbook
import datetime


# ============================================MAIN FUNCTION=============================================================
# ======================================================================================================================

with open ("Test input file.txt") as test_file:
    output = test_file.read()

with open("TEXT_FSM_FILES//huawei_vrp_display_version.textfsm") as fsm_temp:
    fsm = textfsm.TextFSM(fsm_temp)
    result = fsm.ParseText(output)
print(fsm.header)
pprint(result)

