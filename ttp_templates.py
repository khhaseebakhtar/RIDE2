huawei_display_interface = ''' 
<vars>
interface_details = {
    "bw": "un-known",
    "type": "un-known"
}
</vars>

<group name="interface_details">
##to catch where if index is present and in 2nd line where if index is not present 
{{interface | _start_ }} current state : {{ link_status }} ({{ ignore(".*") }})
{{interface | _start_ }} current state : {{ link_status }}

##to catch the state where reason for port down is also mentioned e.g "DOWN(transceiver offline)"
{{interface | _start_ }} current state : {{ link_status | re("\w+\(.*?\)")}} ({{ ignore(".*") }})

##to catch two worded state e.g "Admin Down"
{{interface | _start_ }} current state : {{link_status | re("\S+\s+\S+")}}

Port Mode: {{type}}
Port BW: {{bw}}
BW: {{bw}}
</group>
'''
