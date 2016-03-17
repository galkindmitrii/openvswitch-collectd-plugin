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


#TODO: last_values should only keep 1 iteration
last_values = {}


def get_popen_cmd_stdout(cmd, stdin=None):
    """
        
    """
    try:
        cmd_out = Popen(cmd,
                        stdout=PIPE, stderr=PIPE, stdin=stdin, close_fds=True)

        cmd_std_err = cmd_out.stderr.read()
        if cmd_std_err:
            collectd.info("ovs-ctl wrote to stderr: %s" % ovs_std_err)

        return cmd_out.stdout

    except (OSError, IOError) as exc:
        collectd.error("An error occured while running %s cmd: %s" % (cmd, exc))

def get_ovs_ctl_stdout(cmd, stdin=None):
    """
    Using Popen, runs the given 'cmd' and returns its stdout.
    Logs stderr if any.
    """
    try:
        ovs_out = Popen(cmd,
                        stdout=PIPE, stderr=PIPE, stdin=stdin, close_fds=True)

        ovs_std_err = ovs_out.stderr.read()
        if ovs_std_err:
            collectd.info("ovs-ctl wrote to stderr: %s" % ovs_std_err)

        return ovs_out.stdout.readlines()

    except (OSError, IOError) as exc:
        collectd.error("An error occured while running ovs-ctl: %s" % exc)
        return []

def fetch_ovs_statistics():
    """
    Runs the Openvswitch Datapath Control utility to grab statistics.
    """
    data = {}
    cmd = ("ovs-dpctl", "show", "--timeout=5")

    ovs_stdout = get_ovs_ctl_stdout(cmd)

    for i, line in enumerate(ovs_stdout):
        if line.find("@ovs-system") != -1:
            # TODO: find vs regex
            # TODO: a better parsing?
            bridge = line.strip().replace(":", "")
            data[bridge] = ovs_stdout[i+1].strip()
            flows_number = ovs_stdout[i+2].strip()
            break  # we run only 1 DP

    flows_number = flows_number.split(": ")[1]
    all_vals = struct_info(data)
    all_vals['system@ovs-system']['flows'] = flows_number

    return all_vals

def get_ps_ovs_cpu_usage():
    """
    Returns a cpu usage of ovs-vswitchd (userspace) service in percent.
    This represents the load generated by data-path 'missed' packets plus
    internal OVS stuff.
    """
    cpu_usage = 0.0

    try:
        with open("/var/run/openvswitch/ovs-vswitchd.pid", "r") as pid_file:
            pid = pid_file.read().strip()

        cmd = ("ps", "-p", pid, "-o" "%cpu")
        ps_out = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True)
        std_err = ps_out.stderr.readlines()

        if std_err:
            collectd.info("ps wrote to stderr: %s" % std_err)

        cpu_usage = float(ps_out.stdout.readlines()[-1].strip())

    except (OSError, IOError, ValueError) as exc:
        collectd.error("An error occured while getting cpu usage: %s" % exc)

    return cpu_usage

def get_num_of_vxlans():
    """
    Returns a number of vxlan tunnels as reported by ovs-ofctl;
    All should be on br-tun interface.
    """
    num_vxlans = 0

    # grep all vxlans on br-tun and count them:
    cmd = ("ovs-ofctl", "show", "br-tun", "--timeout=5")
    try:
        ovs_stdout = get_popen_cmd_stdout(cmd)
        grep_out = get_popen_cmd_stdout(("grep", "(vxlan-"), ovs_stdout)
        wc_out = get_popen_cmd_stdout(("wc", "-l"), grep_out)
        num_vxlans = int(wc_out.read())  # no extra line here
    except TypeError as exc:
        collectd.error("An error occured while getting vxlan count: %s" % exc)

    return num_vxlans

# TODO: this should not be executed on the Network Nodes!
def get_virsh_list_num_instances():
    """
    Returns the number of VMs running on current host as reported by
    'virsh list --uuid --state-running'
    """
    num_instances = 0

    # cmd to list all running VM uuids and count their number (-1 line):
    cmd = ("virsh", "list", "--uuid", "--state-running")
    try:
        virsh_list_out = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True)

        std_err = virsh_list_out.stderr.readlines()
        if std_err:
            collectd.info("virsh wrote to stderr: %s" % std_err)

        wc_out = Popen(("wc", "-l"),
                       stdout=PIPE,
                       stdin=virsh_list_out.stdout,
                       close_fds=True)
        num_instances = int(wc_out.stdout.read()) - 1  # an empty line

    except (OSError, IOError, TypeError) as exc:
        collectd.error("An error occured while running virsh: %s" % exc)

    return num_instances

def struct_info(lines):
    """
    Returns a parced data from given lines.
    """
    struct = {}
    for line in lines:
        #TODO: why?
        struct[line] = {}
        for d in re.split(":? ", lines[line], 3):
            if d.find(":") != -1:
                stats = d.split(":")
                struct[line][stats[0]] = float(stats[1])
    return struct

def calculate_ratio(last, values):
    """
    Calculates the current ratio between hit/miss/lost packets
    based on given last values and new values. Returns ratios as percent.
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

def dispatch_to_collectd(data_type, values):
    """
    Submits the given values of the given type to collectd.
    """
    cc = collectd.Values(plugin="openvswitch")
    cc.type_instance = "system@ovs-system"  # TODO: needed with only 1 DP?
    cc.type = data_type
    cc.values = values
    cc.dispatch()

def send_data_to_collectd(ovs_data, cpu_usage, vms_running, vxlan_count):
    """
    Sends all acquired statistics to collectd.
    """
    global last_values
    keys = ["hit", "missed", "lost", "flows"]

    for val in ovs_data:
        values = []
        # OVS DP (hit/miss/loss/flows):
        for key in keys:
            if (ovs_data[val].get(key) is not None):
                values.append(ovs_data[val][key])
            else:
                values.append(0.00)
        dispatch_to_collectd("ovs_dp_overall", values)

        # OVS DP as percentage:
        ratio_values = calculate_ratio(last_values.get(val), values)
        dispatch_to_collectd("ovs_dp_overall_ratio", ratio_values)

        last_values[val] = values

    dispatch_to_collectd("ovs_cpu_usage", (cpu_usage,))
    dispatch_to_collectd("ovs_running_vms", (vms_running,))
    dispatch_to_collectd("ovs_total_vxlans", (vxlan_count,))

def read_openvswitch_stats():
    """
    A callback method used by collectd.
    An entry point. Gets all the possible stats and sends them to collectd.
    """
    ovs_data = fetch_ovs_statistics()  # OVS DP data
    ovs_cpu_usage = get_ps_ovs_cpu_usage()  # ps %cpu for OVS
    vms_running = get_virsh_list_num_instances()  # libvirt VM count
    vxlan_count = get_num_of_vxlans()  # OVS OF vxlan count

    if not ovs_data:
        collectd.error("Did not receive the OVS data")
        return None

    send_data_to_collectd(ovs_data, ovs_cpu_usage, vms_running, vxlan_count)

collectd.register_read(read_openvswitch_stats)
