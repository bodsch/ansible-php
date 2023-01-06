#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2020-2023, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import hashlib
from pathlib import Path

from ansible.module_utils import distro
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

TPL_MODULE = """; generated by ansible
{% if item is defined %}
{{ item }}
{% endif %}
"""


class PHPModules(object):
    """
        Main Class
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.php_modules = module.params.get("php_modules")
        self.php_modules_path = module.params.get("php_modules_path")
        self.dest = module.params.get("dest")
        self.force = module.params.get("force")

        self.php_modules_cache_directory = f"{Path.home()}/.ansible/cache/php"

        (self.distribution, self.version, self.codename) = distro.linux_distribution(full_distribution_name=False)

    def run(self):
        """
        """
        result_state = []

        self.__create_directory(self.php_modules_cache_directory)

        # redhet needs an extrawurst ...

        # {{ '/conf.d/' if ansible_os_family | lower != 'redhat' else '/' }}"
        conf_d = "conf.d"

        #if self.distribution.lower() in ["debian", "ubuntu"]:
        #    conf_d = "conf.d"

        if self.distribution.lower() in ["redhat", "centos", "oracle", "fedora", "rocky", "almalinux"]:
            conf_d = ""

        if isinstance(self.php_modules, list):
            for module in self.php_modules:
                """
                """
                changed = False
                w_changed = False
                e_changed = False

                module_state_msg = None
                res = {}

                module_name = module.get("name")
                module_state = module.get("enabled", False)
                module_priority = module.get("priority", 10)
                module_content = module.get("content", None)
                module_file_name = os.path.join(self.php_modules_path, f"{module_name}.ini")
                module_link_name = None
                module_link_names = []

                if isinstance(self.dest, list):
                    for path in self.dest:
                        module_link_names.append(os.path.join(path, conf_d, f"{module_priority}-{module_name}.ini"))
                else:
                    module_link_name = os.path.join(self.dest, conf_d, f"{module_priority}-{module_name}.ini")

                # self.module.log(msg=f"module_name   : {module_name}")
                # self.module.log(msg=f"  - state     : {module_state}")
                # self.module.log(msg=f"  - priority  : {module_priority}")
                # self.module.log(msg=f"  - file name : {module_file_name}")
                # self.module.log(msg=f"  - link name : {module_link_name}")
                # self.module.log(msg=f"  - link names : {module_link_names}")

                res[module_name] = dict()

                if module_content:

                    w_changed = self._write_module(module_name, module_file_name, module_content)

                    if w_changed:
                        module_state_msg = "module sucessful written"

                    if module_state:
                        e_changed, msg = self._enable_module(module_file_name, module_link_names)

                        if e_changed:
                            self.module.log(msg=f"    - {msg}")

                            if module_state_msg:
                                module_state_msg += " and enabled"
                            else:
                                module_state_msg = "module sucessful enabled"

                    changed = (w_changed or e_changed)

                    res[module_name].update({"changed": changed})
                    if changed and module_state_msg:
                        res[module_name].update({"state": module_state_msg})

                if not module_state:
                    changed = self._disable_module(module_link_names)

                    if changed:
                        module_state_msg = "module succesfull disabled."

                        res[module_name].update({"state": module_state_msg})

                    res[module_name].update({"changed": changed})

                if len(res) > 0:
                    result_state.append(res)

        # define changed for the running tasks
        # migrate a list of dict into dict
        combined_d = {key: value for d in result_state for key, value in d.items()}
        # find all changed and define our variable
        changed = (len({k: v for k, v in combined_d.items() if v.get('changed')}) > 0)

        result = dict(
            changed = changed,
            failed = False,
            msg = result_state
        )

        self.module.log(msg=f"= result {result}")

        return result

    def create_link(self, source, destination, force=False):
        """
        """
        if force:
            os.remove(destination)
            os.symlink(source, destination)
        else:
            if os.path.exists(destination):
                if not os.path.islink(destination):
                    # rename
                    os.rename(destination, f"{destination}.DIST")

            os.symlink(source, destination)

    def _write_module(self, module_name, file_name, data=None):
        """
        """
        checksum_file = os.path.join(self.php_modules_cache_directory, f"{module_name}.checksum")

        if not data:
            if os.path.exists(file_name):
                os.remove(file_name)
            if os.path.exists(checksum_file):
                os.remove(checksum_file)

            return False

        changed, new_checksum, old_checksum = self.__has_changed(file_name, checksum_file, data)

        if changed:
            self.__write_template(data=data, data_file=file_name, checksum=new_checksum, checksum_file=checksum_file)

        return changed

    def _enable_module(self, module_file_name, module_link_names):
        """
        """
        changed = False
        result = {}

        for link in module_link_names:
            result[link] = dict()

            if os.path.islink(link) and os.readlink(link) == module_file_name:
                # self.module.log(msg="link exists and is valid")
                result[link].update({"msg": "link exists and is valid", "changed": False})
                pass
            else:
                if not os.path.islink(link):
                    self.create_link(module_file_name, link)
                else:
                    if os.readlink(link) != module_file_name:
                        # self.module.log(msg=f"path '{module_link_name}' is a broken symlink")
                        self.create_link(module_file_name, link, True)
                    else:
                        self.create_link(module_file_name, link)

                result[link].update({"msg": f"link {link} created", "changed": True})

                changed = True

        changed = (len({k: v for k, v in result.items() if v.get('changed')}) > 0)

        return changed, result

    def _disable_module(self, module_link_names):
        """
        """
        result = {}
        changed = False

        for link in module_link_names:
            result[link] = dict()
            if os.path.exists(link):
                os.remove(link)
                result[link].update({"msg": f"link {link} removed", "changed": True})
            else:
                result[link].update({"msg": f"no link for {link} found", "changed": False})

        changed = (len({k: v for k, v in result.items() if v.get('changed')}) > 0)

        return changed

    def __write_template(self, data, data_file, checksum, checksum_file):
        """
        """
        data = self.__templated_data(data)

        with open(data_file, "w") as f:
            f.write(data)
            f.close()

            with open(checksum_file, "w") as f:
                f.write(checksum)
                f.close()

    def __checksum(self, plaintext):
        """
        """
        _bytes = plaintext.encode('utf-8')
        _hash = hashlib.sha256(_bytes)
        return _hash.hexdigest()

    def __templated_data(self, data):
        """
          generate data from dictionary
        """
        from jinja2 import Template

        tm = Template(TPL_MODULE)
        d = tm.render(item=data)

        return d

    def __has_changed(self, data_file, checksum_file, data):
        """
        """
        old_checksum = ""

        if not os.path.exists(data_file) and os.path.exists(checksum_file):
            """
            """
            os.remove(checksum_file)

        if os.path.exists(checksum_file):
            with open(checksum_file, "r") as f:
                old_checksum = f.readlines()[0]

        if isinstance(data, str):
            _data = sorted(data.split())
            _data = '\n'.join(_data)

        checksum = self.__checksum(_data)
        changed = not (old_checksum == checksum)

        if self.force:
            changed = True
            old_checksum = ""

        # self.module.log(msg=f" - new  checksum '{checksum}'")
        # self.module.log(msg=f" - curr checksum '{old_checksum}'")
        # self.module.log(msg=f" - changed       '{changed}'")

        return changed, checksum, old_checksum

    def __create_directory(self, dir):
        """
        """
        try:
            os.makedirs(dir, exist_ok=True)
        except FileExistsError:
            pass

        if os.path.isdir(dir):
            return True
        else:
            return False


# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            php_modules=dict(
                required=True,
                type=list
            ),
            php_modules_path=dict(
                required=True,
                type=str
            ),
            dest=dict(
                required=True,
                type=list
            ),
            force=dict(
                required=False,
                type=bool,
                default=False
            ),
        ),
        supports_check_mode=False,
    )

    helper = PHPModules(module)
    result = helper.run()

    module.log(msg=f" = result : '{result}'")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
