# coding: utf-8
from __future__ import unicode_literals

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

import json
import pytest
import os

import testinfra.utils.ansible_runner

HOST = 'instance'

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts(HOST)


def pp_json(json_thing, sort=True, indents=2):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


def base_directory():
    """
    """
    cwd = os.getcwd()

    if 'group_vars' in os.listdir(cwd):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = f"molecule/{os.environ.get('MOLECULE_SCENARIO_NAME')}"

    return directory, molecule_directory


def read_ansible_yaml(file_name, role_name):
    """
    """
    read_file = None

    for e in ["yml", "yaml"]:
        test_file = f"{file_name}.{e}"
        if os.path.isfile(test_file):
            read_file = test_file
            break

    return f"file={read_file} name={role_name}"


@pytest.fixture()
def get_vars(host):
    """
        parse ansible variables
        - defaults/main.yml
        - vars/main.yml
        - vars/${DISTRIBUTION}.yaml
        - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
    """
    base_dir, molecule_dir = base_directory()
    distribution = host.system_info.distribution
    operation_system = None

    if distribution in ['debian', 'ubuntu']:
        operation_system = "debian"
    elif distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
        operation_system = "redhat"
    elif distribution in ['arch', 'artix']:
        operation_system = f"{distribution}linux"

    # print(" -> {} / {}".format(distribution, os))
    # print(" -> {}".format(base_dir))

    file_defaults = read_ansible_yaml(f"{base_dir}/defaults/main", "role_defaults")
    file_vars = read_ansible_yaml(f"{base_dir}/vars/main", "role_vars")
    file_distibution = read_ansible_yaml(f"{base_dir}/vars/{operation_system}", "role_distibution")
    file_molecule = read_ansible_yaml(f"{molecule_dir}/group_vars/all/vars", "test_vars")
    # file_host_molecule = read_ansible_yaml("{}/host_vars/{}/vars".format(base_dir, HOST), "host_vars")

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distibution_vars = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")
    # host_vars          = host.ansible("include_vars", file_host_molecule).get("ansible_facts").get("host_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(distibution_vars)
    ansible_vars.update(molecule_vars)
    # ansible_vars.update(host_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def local_facts(host):
    """
        return local fact
    """
    return host.ansible("setup").get("ansible_facts").get("ansible_local").get("php_fpm")


def test_installed_package(host, get_vars):
    """
        test insatlled package
    """
    package = 'php-fpm'
    distribution = host.system_info.distribution

    print(distribution)

    if not distribution == "artix":
        if distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
            package_version = local_facts(host).get("version").get("package")
            package = f"php{package_version}-php-fpm"

        if distribution in ['arch', 'artix']:
            package_version = local_facts(host).get("version").get("major")
            if package_version == 7:
                package = f"php{package_version}-fpm"

        p = host.package(package)
        assert p.is_installed


def test_installed_custom_package(host, get_vars):
    """
        custom packages
    """
    custom_packages = get_vars.get("php_packages")
    distribution = host.system_info.distribution

    if not distribution == "artix":
        if custom_packages:
            for pkg in custom_packages:
                package = pkg

                if distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
                    package_version = local_facts(
                        host).get("version").get("package")
                    package = f"php{package_version}-{pkg}"

                p = host.package(package)
                assert p.is_installed


def test_directories(host, get_vars):
    """
        test created directories
    """
    distribution = host.system_info.distribution

    print(distribution)

    package_version = local_facts(host).get("version").get("full")
    directories = [
        f"/etc/php/{package_version}/cli",
        f"/etc/php/{package_version}/fpm"
    ]

    if distribution in ['arch', 'artix']:
        package_version = local_facts(host).get("version").get("major")

        if package_version == 7:
            directories = [
                f"/etc/php{package_version}/conf.d",
                f"/etc/php{package_version}/mods-available",
                f"/etc/php{package_version}/php-fpm.d"
            ]
        else:
            directories = [
                "/etc/php/conf.d",
                "/etc/php/mods-available",
                "/etc/php/php-fpm.d"
            ]

    if distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
        directories = [
            f"/etc/php/{package_version}/php.d",
            f"/etc/php/{package_version}/php-fpm.d"
        ]

    print(f"directory: {directories}")

    for dirs in directories:

        d = host.file(dirs)

        if distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
            assert d.exists
        else:
            assert d.is_directory


def test_user(host, get_vars):
    """
        test service user and group
    """
    user = local_facts(host).get("user")
    group = local_facts(host).get("group")

    assert host.group(group).exists
    assert host.user(user).exists
    assert group in host.user(user).groups


def test_service(host):
    """
        is service running and enabled
    """
    service = host.service(local_facts(host).get("daemon"))

    assert service.is_enabled
    assert service.is_running


def test_fpm_pools(host, get_vars):
    """
        test sockets
    """
    for i in host.socket.get_listening_sockets():
        print(i)

    for pool in get_vars.get("php_fpm_pools"):
        name = pool.get("name")
        listen = pool.get("listen")

        local_facts(host).get("socket_directory"),

        socket_name = listen.replace('$pool', name)

        print(socket_name)

        assert host.file(socket_name).exists
        assert host.socket(f"unix://{socket_name}").is_listening

