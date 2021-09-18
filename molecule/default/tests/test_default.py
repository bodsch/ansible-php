#!/usr/bin/python3
# -*- coding: utf-8 -*-

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import pytest
import os
import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def base_directory():
    """
        get molecule directories
    """
    cwd = os.getcwd()

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{0}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


@pytest.fixture()
def get_vars(host):
    """
        parse ansible variables
        - defaults/main.yml
        - vars/main.yml
        - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
    """
    base_dir, molecule_dir = base_directory()

    file_defaults = "file={0}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={0}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={0}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

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

    pp.pprint(distribution)

    if(distribution in ['redhat', 'centos', 'ol']):
        package_version = local_facts(host).get("version").get("package")
        package = 'php{0}-php-fpm'.format(package_version)

    if distribution == 'arch':
        package_version = local_facts(host).get("version").get("major")
        package = 'php{0}-fpm'.format(package_version)

    p = host.package(package)
    assert p.is_installed


def test_installed_custom_package(host, get_vars):
    """
        custom packages
    """
    custom_packages = get_vars.get("php_custom_packages")

    if(custom_packages):
        distribution = host.system_info.distribution

        for pkg in custom_packages:
            package = pkg

            if(distribution in ['redhat', 'centos', 'ol']):
                package_version = local_facts(host).get("version").get("package")
                package = 'php{0}-{1}'.format(
                    package_version,
                    pkg
                )

            p = host.package(package)
            assert p.is_installed


@pytest.mark.parametrize("dirs", [
    "/etc/php/{}/cli",
    "/etc/php/{}/fpm"
])
def test_directories(host, dirs, get_vars):
    """
        test created directories
    """
    distribution = host.system_info.distribution

    package_version = local_facts(host).get("version").get("full")
    directories = [
        "/etc/php/{}/cli",
        "/etc/php/{}/fpm"
    ]

    if distribution == 'arch':
        package_version = local_facts(host).get("version").get("major")
        directories = [
            "/etc/php{0}/conf.d",
            "/etc/php{0}/mods-available",
            "/etc/php{0}/php-fpm.d"
        ]

    for dirs in directories:
        d = host.file(dirs.format(package_version))
        pp.pprint("directory: {0}".format(d))

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

    daemon = local_facts(host).get("daemon")

    for pool in get_vars.get("php_fpm_pools"):
        name = pool.get("name")
        listen = pool.get("listen")
        listen = listen.replace('//', "/{}/".format(daemon))

        socket_name = listen.replace('$pool', name)

        assert host.file(socket_name).exists
        assert host.socket("unix://{0}".format(socket_name)).is_listening
