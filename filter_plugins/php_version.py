# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from packaging.version import Version

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible filters. Python string operations.
    """

    def filters(self):
        return {
            'add_php_version': self.add_version,
            'verify_version': self.verify_version,
        }

    def add_version(self, data, version):
        """
        """
        display.vv("add_version(data, version)")
        display.vv(f"  - {data}")
        display.vv(f"  - {version}")

        packages = []

        for i in data:
            if i in ["php-opcache"]:
                packages.append(i.replace("php", f"php{version}"))
            else:
                packages.append(i)

        display.v(f"  = {packages}")

        return packages

    def verify_version(self, data, version):
        """
        """
        display.vv("verify_version(data, version)")
        display.vv(f"  - data   : {data}")
        display.vv(f"  - version: {version}")

        result = False

        php_version = data.get('version', None)
        php_major_version = data.get('major_version', None)

        display.vv(f"    php_version        : {php_version}")
        display.vv(f"    php_major_version  : {php_major_version}")

        if "." in version:
            if not php_version:
                return False
            display.vv(f"    {version} != {php_version}")
            result = (Version(version) == Version(php_version))
        else:
            if not php_major_version:
                return False
            display.vv(f"    {version} != {php_major_version}")
            result = (Version(version) == Version(php_major_version))

        display.v(f"  = {result}")

        return result
