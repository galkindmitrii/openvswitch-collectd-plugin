from distutils.core import setup

setup(name='openvswitch-plugin-collectd',
      version='0.1.2',
      description='OpenVSwitch plugin for Collectd',
      author='Luiz Ozaki',
      author_email='luiz.ozaki@locaweb.com.br',
      url='https://github.com/galkindmitrii/openvswitch-collectd-plugin',
      data_files=[('/etc/collectd.d/',
                   ['openvswitch.conf', 'openvswitch.db', 'graphite.conf']),
                  ('/usr/lib64/collectd/', ['openvswitch.py'])]
     )
