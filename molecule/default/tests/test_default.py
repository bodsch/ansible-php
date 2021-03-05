
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import pytest
import os
import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

"""
    get molecule directories
"""


def base_directory():
    """ ... """
    cwd = os.getcwd()

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


"""
    parse ansible variables
    - defaults/main.yml
    - vars/main.yml
    - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
"""


@pytest.fixture()
def get_vars(host):
    """ ... """
    base_dir, molecule_dir = base_directory()

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


"""
    return local fact
"""


def local_facts(host):
    """ ... """
    return host.ansible("setup").get("ansible_facts").get("ansible_local").get("php_fpm")


"""
    test insatlled package
"""


def test_installed_package(host, get_vars):
    """ ... """
    package = 'php-fpm'
    distribution = host.system_info.distribution

    if(distribution in ['redhat', 'centos', 'ol']):
        package_version = local_facts(host).get("version").get("package")
        package = 'php{version}-php-fpm'.format(version=package_version)

    p = host.package(package)
    assert p.is_installed


"""
    test created directories
"""


@pytest.mark.parametrize("dirs", [
    "/etc/php/{}/cli",
    "/etc/php/{}/fpm"
])
def test_directories(host, dirs, get_vars):
    """ ... """
    package_version = local_facts(host).get("version").get("full")

    d = host.file(dirs.format(package_version))
    pp.pprint("directory: {}".format(d))

    assert d.is_directory
    assert d.exists


"""
    test service user and group
"""


def test_user(host, get_vars):

    user = local_facts(host).get("user")
    group = local_facts(host).get("group")

    assert host.group(group).exists
    assert host.user(user).exists
    assert group in host.user(user).groups


"""
    is service running and enabled
"""


def test_service(host):
    """ ... """
    service = host.service(local_facts(host).get("daemon"))

    assert service.is_enabled
    assert service.is_running


"""
    test sockets
"""


def test_fpm_pools(host, get_vars):
    """ ... """
    for i in host.socket.get_listening_sockets():
        print(i)

    for pool in get_vars.get("php_fpm_pools"):
        #pp.pprint(pool)
        name = pool.get("name")
        listen = pool.get("listen")
        socket_name = listen.replace('$pool', name)
        pp.pprint(socket_name)

        assert host.file(socket_name).exists
        assert host.socket("unix://{0}".format(socket_name)).is_listening
