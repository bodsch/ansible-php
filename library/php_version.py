#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import re

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}


class PHPHelper(object):
    """
        Main Class
    """
    module = None

    def __init__(self):
        """
          Initialize all needed Variables
        """

        self.os_family = module.params.get("os_family")
        self.redhat_version = module.params.get("redhat_version")

    def run(self):
        res = dict(
            failed=False,
            available_php_version="none"
        )

        version = ''

        module.log(msg="os_family      : {}".format(self.os_family))
        module.log(msg="redhat_version : {}".format(self.redhat_version))

        if(self.os_family == "Debian"):
            error, version, msg = self._search_apt()

        if(self.os_family == "RedHat"):
            error, version, msg = self._search_yum(self.redhat_version)

        res['failed'] = error
        res['available_php_version'] = version
        res['msg'] = msg

        return res

    def _search_apt(self):
        """
            apt-cache show php | grep Version | sort | tail -n1 | awk -F'[:+]' '{print $3}' | tr -d '[:space:]'

            bionic provides PHP 7.2
            buster provides PHP 7.3
            stretch provides PHP 7.0
        """
        import apt

        version = ''

        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        pkg = cache['php']

        # module.log(msg="pkg       : {}".format(pkg))
        # module.log(msg="installed : {}".format(pkg.is_installed))
        # module.log(msg="shortname : {}".format(pkg.shortname))

        if(pkg):
            pkg_version = pkg.versions[0]
            version = pkg_version.version
            pattern = re.compile(r'^\d:(?P<version>\d.+)\+.*')
            result = re.search(pattern, version)

            version = result.group(1)

        return False, version, ''

    def _search_yum(self, redhat_version=None):
        """
            yum info php73 | grep Summary | cut -d ':' -f 2 | tr -d '[:space:]' | cut -c23-25

            centos7 provides PHP 5.4(.16) m(
            we use remi packages for newer version
            https://blog.remirepo.net/post/2018/12/10/Install-PHP-7.3-on-CentOS-RHEL-or-Fedora
        """
        # module.log(msg="search version {}".format(redhat_version))

        import subprocess

        version = ''
        versions = []

        result = subprocess.Popen(
            ["yum", "info", "php{}*common".format(redhat_version)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        pattern = re.compile(r'^Version.*: (?P<version>\d\.\d)')

        for line in result.stdout:
            for match in re.finditer(pattern, line):
                result = re.search(pattern, line)
                versions.append(result.group(1))

        if(len(versions) == 0):
            msg = 'nothing found'
            error = True

        if(len(versions) == 1):
            msg = ''
            error = False
            version = versions[0]

        if(len(versions) > 1):
            msg = 'more then one result found! choose one of them!'
            error = True
            version = ', '.join(versions)

        return error, version, msg


# ===========================================
# Module execution.
#

def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="present", choices=["absent", "present"]),
            os_family=dict(required=True),
            redhat_version=dict(required=False, default=None)

        ),
        supports_check_mode=False,
    )

    helper = PHPHelper()
    result = helper.run()

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
