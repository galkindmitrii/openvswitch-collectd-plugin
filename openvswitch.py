# openvswitch-collectd-plugin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; only version 2
# of the License is applicable.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import re
import collectd
from subprocess import Popen, PIPE


last_values = {}

def fetch_ovs_statistics():
    """
    Runs the Openvswitch Datapath Control utility to grab statistics.
    """
    data = {}
    try:
        ovs_dp_out = Popen(("/usr/bin/ovs-dpctl", "show"),
                           stdout=PIPE,
                           stderr=PIPE,
                           close_fds=True)

        ovs_std_out = ovs_dp_out.stdout.readlines()

        for i, line in enumerate(ovs_std_out):
            if line.find("@") != -1:
                bridge = line.strip().replace(":", "")
                data[bridge] = ovs_std_out[i+1].strip()
        return struct_info(data)

    except (OSError, IOError) as exc:
        collectd.error("Error while running ovs-dpctl: %s" % exc)

def struct_info(lines):
    """
        
    """
    struct = {}
    for line in lines:
        struct[line] = {}
        for d in re.split(":? ", lines[line], 3):
            if d.find(":") != -1:
                stats = d.split(":")
                struct[line][stats[0]] = float(stats[1])
    return struct

def calculate_ratio(last, values):
    """
    
    """
    d = []
    total = 0
    ratio_keys = ["hit_ratio", "missed_ratio", "lost_ratio"]

    if (last):
        for i in range(len(ratio_keys)):
            if (values[i] and last[i]):
                d.append(values[i] - last[i])
                total += (values[i] - last[i])
            else:
                d.append(0.00)

        if (total != 0):
            return [(d[i]/total)*100 for i, key in enumerate(ratio_keys)]

    return [0.00, 0.00, 0.00]

def dispatch_all_values(info):
    """
    
    """
    global last_values
    keys = ["hit", "missed", "lost"]

    for val in info:
        values = []
        cc = collectd.Values(plugin="openvswitch")
        cc.type_instance = val

        cc.type = "openvswitch"
        for key in keys:
            if (info[val].get(key) is not None):
                values.append(info[val][key])
            else:
                values.append(0.00)
        cc.values = values
        cc.dispatch()

        cc.type = "openvswitch_ratio"
        cc.values = calculate_ratio(last_values.get(val), values)
        cc.dispatch()

        last_values[val] = values

def read_callback():
    """
    A callback method used by collectd.
    """
    data = fetch_ovs_statistics()

    if not data:
        collectd.error("Did not receive the OVS data")
        return None

    dispatch_all_values(data)

collectd.register_read(read_callback)
