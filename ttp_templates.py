ttp_huawei_display_interface = ''' 
<vars>
default_values = {
    "port_bw": "un-known",
    "type": "un-known"
}
intf_2_ignore = 'Eth-Trunk\S+|Loop|NULL|Virtual'
</vars>

<group name="interface_details" default ="default_values" containsall="interface">
##to catch where if index is present and in 2nd line where if index is not present 
{{interface | notstartswith_re('intf_2_ignore') | _start_ }} current state : {{ link_status }} ({{ ignore(".*") }})
{{interface | notstartswith_re('intf_2_ignore') | _start_ }} current state : {{ link_status }}

##to catch the state where reason for port down is also mentioned e.g "DOWN(transceiver offline)"
{{interface | notstartswith_re('intf_2_ignore') | _start_ }} current state : {{ link_status | re("\w+\(.*?\)")}} ({{ ignore(".*") }})

##to catch two worded state e.g "Admin Down"
{{interface | notstartswith_re('intf_2_ignore') | _start_ }} current state : {{link_status | re("\S+\s+\S+")}}

Connector Type: {{type | re("\S+")}},{{ ignore(".*") }}
Port Mode: {{type}}{{ ignore(".*") }}
Port BW: {{port_bw}},{{ ignore(".*") }}
{{ ignore(".*") }}Current BW: {{port_bw}},{{ ignore(".*") }}
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
default_values1 = {
    "no_of_links" : "0",
    "max_bw" : "N/A",
    "current_bw" : "N/A"
}

deafult_values2 = {
    "member_interface": "No Interfaces",
    "state" : "",
    "weight" : ""
    }

intf_2_ignore = "PortName|physical"
</vars>

<group name="trunk_details" default = "default_values1">
{{trunk_number | _start_ }} current state : {{ trunk_state }}
{{trunk_number | _start_ }} current state : {{ trunk_state | re("\S+") }} 
{{trunk_number | _start_ }} current state : {{ trunk_state | re("\S+") }} {{ignore(".*")}}
{{ignore(".*")}} Maximal BW: {{max_bw}}, Current BW: {{current_bw}}, {{ignore(".*")}}
The Number of Ports in Trunk : {{no_of_links | re("\d+")}}

<group name="members" default = "default_values2">
{{member_interface | notstartswith_re('intf_2_ignore')}} {{state}} {{weight | re("\d+")}}
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
