import pytest
import os
import yaml
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


@pytest.fixture()
def get_vars(host):
    defaults_files = "file=../../defaults/main.yml name=role_defaults"
    vars_files = "file=../../vars/main.yml name=role_vars"

    ansible_vars = host.ansible(
        "include_vars",
        defaults_files)["ansible_facts"]["role_defaults"]

    ansible_vars.update(host.ansible(
        "include_vars",
        vars_files)["ansible_facts"]["role_vars"])

    print(ansible_vars)

    return ansible_vars

# def test_tmp_directory(host, get_vars):
#     dir = host.file(get_vars['php_fpm_conf_path'])
#     assert dir.exists
#     assert dir.is_directory
#
#
# def test_tmp_directory(host, get_vars):
#     dir = host.file(get_vars['php_fpm_pool_conf_path'])
#     assert dir.exists
#     assert dir.is_directory
#
#
# def test_tmp_directory(host, get_vars):
#     dir = host.file(get_vars['php_modules_conf_paths'])
#     assert dir.exists
#     assert dir.is_directory


# @pytest.mark.parametrize("files", [
#     "php-fpm.conf",
# ])
# def test_files(host, get_vars, files):
#     dir = host.file(get_vars['php_fpm_conf_path'])
#     f = host.file("%s/%s" % (dir.linked_to, files))
#     assert f.exists
#     assert f.is_file
#
