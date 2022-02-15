# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible filters. Python string operations.
    """

    def filters(self):
        return {
            'add_php_version': self.add_version,
        }

    def add_version(self, data, version):
        """
        """
        display.v("add_version(data, version)")
        display.v("  - {}".format(data))
        display.v("  - {}".format(version))

        packages = []

        for i in data:
            if i in ["php-opcache"]:
                packages.append(i.replace("php", "php{}".format(version)))
            else:
                packages.append(i)

        display.v("  = {}".format(packages))

        return packages
