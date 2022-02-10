#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import re

from ansible.module_utils import distro
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}


class PHPVersion(object):
    """
        Main Class
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.package_version = module.params.get("package_version")

        (self.distribution, self.version, self.codename) = distro.linux_distribution(full_distribution_name=False)

    def run(self):
        result = dict(
            failed=False,
            available_php_version="none"
        )

        version = ''
        error = True
        msg = "not supported distribution: {}".format(self.distribution)

        self.module.log(msg="  distribution : '{}'".format(self.distribution))

        if self.distribution.lower() in ["debian", "ubuntu"]:
            error, version, msg = self._search_apt()

        if self.distribution.lower() in ["centos", "oracle", "redhat", "fedora"]:
            error, version, msg = self._search_yum()

        if self.distribution.lower() in ["arch", "artix"]:
            self.pacman_bin = self.module.get_bin_path('pacman', True)
            error, version, msg = self._search_pacman()

        package_version = version.replace('.', '')
        major_version = version.split('.')[0]

        version = dict(
            version=version,
            package_version=package_version,
            major_version=major_version
        )

        result = dict(
            failed=error,
            available=version,
            msg=msg
        )

        return result

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

    def _search_yum(self):
        """
            yum info php73 | grep Summary | cut -d ':' -f 2 | tr -d '[:space:]' | cut -c23-25

            centos7 provides PHP 5.4(.16) m(
            we use remi packages for newer version
            https://blog.remirepo.net/post/2018/12/10/Install-PHP-7.3-on-CentOS-RHEL-or-Fedora
        """
        pattern = re.compile(r".*Version.*: (?P<version>\d\.\d)", re.MULTILINE)

        package_version = self.package_version

        if(package_version):
            package_version = package_version.replace('.', '')

        package_mgr = self.module.get_bin_path('yum', False)

        if(not package_mgr):
            package_mgr = self.module.get_bin_path('dnf', True)

        if(not package_mgr):
            return True, "", "no valid package manager (yum or dnf) found"

        self.module.log(msg="  '{0}'".format(package_mgr))

        rc, out, err = self.module.run_command(
            [package_mgr, "info", "php{}*common".format(package_version)],
            check_rc=False)

        version = ''

        if(rc == 0):
            versions = []

            for line in out.splitlines():
                # self.module.log(msg="line     : {}".format(line))
                for match in re.finditer(pattern, line):
                    result = re.search(pattern, line)
                    versions.append(result.group('version'))

            self.module.log(msg="versions      : '{0}'".format(versions))

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
        else:
            msg = 'nothing found'
            error = True

        return error, version, msg

    def _search_pacman(self):
        """
            pacman support

            pacman --noconfirm --sync --search php7 | grep -E "^(extra|world)\/php7 (.*)\[installed\]" | cut -d' ' -f2
        """
        self.module.log(msg="= {function_name}()".format(function_name="_search_pacman"))

        pattern = re.compile(r'^(?P<repository>extra|world)\/php\d?[ ](?P<version>\d\.\d).*-.*', re.MULTILINE)

        results = []
        args = []
        args.append("--noconfirm")
        args.append("--sync")
        args.append("--search")
        args.append("php")

        rc, out, err = self._pacman(args)

        version = re.findall(pattern, out)
        versions = []

        if version:
            if len(version) == 1:
                return False, version[0].group('version'), ""
            else:
                v = ""
                for _, v in version:
                    versions.append(v)

                    if v.startswith(self.package_version) or v == self.package_version:
                         break
                    else:
                        v = None

                if v is None and len(versions) == 0:
                    return True, "", "not found"
                elif v is None and len(versions) != 0:
                    return True, "", "you want version {}, but i found versions {}".format(self.package_version, versions)
                else:
                    return False, v, ""

        else:
            return True, "", "not found"

    def _pacman(self, args):
        '''   '''
        cmd = [self.pacman_bin] + args

        self.module.log(msg="cmd: {}".format(cmd))

        rc, out, err = self.module.run_command(cmd, check_rc=True)
        # self.module.log(msg="  rc : '{}'".format(rc))
        # self.module.log(msg="  out: '{}' ({})".format(out, type(out)))
        # self.module.log(msg="  err: '{}'".format(err))
        return rc, out, err

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            package_version=dict(required=False, default=''),
        ),
        supports_check_mode=False,
    )

    helper = PHPVersion(module)
    result = helper.run()

    module.log(msg="  result : '{}'".format(result))

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
