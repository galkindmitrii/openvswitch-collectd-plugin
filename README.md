openvswitch-collectd-plugin
===========================

OpenVSwitch plugin for Collectd

A simple OpenVSwitch plugin made for Collectd.

- Collects the hit, miss and lost stats from the OpenVSwitch DataPath (Both
numbers and percent ratios as well as average packet per second rate);
- Collects number of active VXLANs;
- Collects number of running VMs (in case run on Compute node);
- Collects the CPU usage of Openvswitch (user-space) service/

This plugin was designed to be used in Openstack with Neutron managing OVS.


Install
-------

Execute 'python setup.py install'

Can be installed either onto Openstack Nova Compute or Neutron Network nodes and
was tested with Liberty and Mitaka releases and OVS 2.4.0 on Centos 7.2

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
