#!/usr/bin/python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

import pytest
import os
import json

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


def read_ansible_yaml(file_name, role_name):
    ext_arr = ["yml", "yaml"]

    read_file = None

    for e in ext_arr:
        test_file = "{}.{}".format(file_name, e)
        if os.path.isfile(test_file):
            read_file = test_file
            break

    return "file={} name={}".format(read_file, role_name)

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

    if distribution in ['debian', 'ubuntu']:
        os = "debian"
    elif distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
        os = "redhat"
    elif distribution in ['arch']:
        os = "archlinux"

    print(" -> {} / {}".format(distribution, os))

    file_defaults      = read_ansible_yaml("{}/defaults/main".format(base_dir), "role_defaults")
    file_vars          = read_ansible_yaml("{}/vars/main".format(base_dir), "role_vars")
    file_distibution   = read_ansible_yaml("{}/vars/{}".format(base_dir, os), "role_distibution")
    file_molecule      = read_ansible_yaml("{}/group_vars/all/vars".format(base_dir), "test_vars")
    # file_host_molecule = read_ansible_yaml("{}/host_vars/{}/vars".format(base_dir, HOST), "host_vars")

    defaults_vars      = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars          = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distibution_vars   = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars      = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")
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

            if distribution in ['redhat', 'centos', 'ol']:
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

    print(distribution)

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
    if distribution in ['redhat', 'centos', 'ol']:
        directories = [
            "/etc/php/{}/php.d",
            "/etc/php/{}/php-fpm.d"
        ]

    for dirs in directories:
        d = host.file(dirs.format(package_version))
        print("directory: {0}".format(d))

        if distribution in ['redhat', 'centos', 'ol']:
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
        # listen = listen.replace('//', "/{}/".format(daemon))

        local_facts(host).get("socket_directory"),

        socket_name = listen.replace('$pool', name)

        print(socket_name)

        assert host.file(socket_name).exists
        assert host.socket("unix://{0}".format(socket_name)).is_listening
