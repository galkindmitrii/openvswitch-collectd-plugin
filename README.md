openvswitch-collectd-plugin
===========================

OpenVSwitch plugin for Collectd

A simple OpenVSwitch plugin made for Collectd.

- Collects the hit, miss and lost stats from the OpenVSwitch DataPath (Both
numbers and percent ratios).
- Collects number of active VXLANs
- Collects number of running VMs (in case run on Compute node)
- Collects the CPU usage of Openvswitch (user-space) service

Install
-------

Execute 'python setup.py install'

Setup.py assumes, that:

 - Collectd plugins folder is /usr/lib64/collectd/
 - Collectd.d folder is /etc/collectd.d/

If that isn't the case, you'll have to either copy the files manually or adjust the setup.py

Plugin is using a [custom TypesDB](https://collectd.org/documentation/manpages/types.db.5.shtml#custom_types) to save metrics.
If you don't specify the default TypesDB + the plugin TypesDB file, it's not going to work.

You can either edit the default TypesDB file and add the openvswitch.db line or specify the openvswitch.db file directly.

Compatibility
-------------------------

1. Should work on all OpenVSwitch versions.

2. Uses 'virsh' to get the list of running instances (on Compute nodes only).

3. collectd-python is needed for plugin to work ('pip install collectd').
