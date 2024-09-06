ttp_huawei_display_interface = ''' 
<vars>
default_values = {
    "bw": "un-known",
    "type": "un-known"
}
</vars>

<group name="interface_details" default ="default_values">
##to catch where if index is present and in 2nd line where if index is not present 
{{interface | _start_ }} current state : {{ link_status }} ({{ ignore(".*") }})
{{interface | _start_ }} current state : {{ link_status }}

##to catch the state where reason for port down is also mentioned e.g "DOWN(transceiver offline)"
{{interface | _start_ }} current state : {{ link_status | re("\w+\(.*?\)")}} ({{ ignore(".*") }})

##to catch two worded state e.g "Admin Down"
{{interface | _start_ }} current state : {{link_status | re("\S+\s+\S+")}}

Connector Type: {{type | re("\S+")}},{{ ignore(".*") }}
Port Mode: {{type}}{{ ignore(".*") }}
Port BW: {{bw}},{{ ignore(".*") }}
{{ ignore(".*") }}Current BW: {{bw}},{{ ignore(".*") }}
Physical is {{type}}
</group>
'''

ttp_huawei_display_interface_description = ''' 
<vars>
default_values = {
    "description": "Not Assigned"
}
</vars>

<group name="record">
Interface PHY Protocol Description {{ _start_ }}
<group name="interface_descriptions" default="default_values">
{{interface | _start_}} {{phy}} {{opr_status}} {{description | re(".*")}}
{{interface | _start_}} {{phy}} {{opr_status}}
</group>
</group>
'''

ttp_huawei_display_interface_eth_trunk = ''' 
<vars>
default_values = {
    "member_interface": "No Interfaces",
    "state" : "",
    "no_of_links" : "0"
}
</vars>
<group name="trunk_details" default = "default_values">
{{trunk_number | _start_ }} current state : {{ trunk_state }}
{{trunk_number | _start_ }} current state : {{ trunk_state | re("\S+\s+.*") }}
The Number of Ports in Trunk : {{no_of_links}}
<group name="members">
{{member_interface}} {{state}} {{ignore}}
</group>

</group>
'''

ttp_juniper_show_interface_description = ''' 
<group name="interface_descriptions" containsall="description">
{{interface}}    {{admin}}    {{phy | contains('up','down')}}   {{description | re(".*")}}
</group>
'''

ttp_juniper_show_version = ''' 
<group name="version">
Model: {{model}}
Junos: {{main_os}}-{{os_version}}
</group>
'''
