
ansible role to install fpm-php on varous systems.

inspired by [geerlingguy](https://github.com/geerlingguy/ansible-role-php)


[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bodsch/ansible-php/CI)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-php)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-php)][releases]

[ci]: https://github.com/bodsch/ansible-php/actions
[issues]: https://github.com/bodsch/ansible-php/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-php/releases


## Requirements & Dependencies

### Operating systems

Tested on

* Debian 9 / 10
* Ubuntu 18.04 / 20.04
* CentOS 7 / 8
* OracleLinux 8


## usage

```
php_redhat_version: "7.3"

php_packages_state: present

php_fpm_log_directory: /var/log/php-fpm
php_fpm_tmp_upload_diectory: /tmp/php-fpm
php_fpm_socket_directory: /run/php

php_fpm_log_level: notice

php_enable_php_fpm: true

php_fpm_listen: "127.0.0.1:9000"
php_fpm_listen_allowed_clients: "127.0.0.1"
php_fpm_pm:
  max_children: 50
  start_servers: 5
  spare_servers:
    min: 5
    max: 5

php_use_managed_ini: true

php_expose_php: "On"
php_memory_limit: "256M"
php_max_execution_time: "60"
php_max_input_time: "60"
php_max_input_vars: "1000"
php_realpath_cache_size: "32K"

php_file_uploads: "On"
php_upload_max_filesize: "64M"
php_max_file_uploads: "20"

php_post_max_size: "32M"
php_date_timezone: "Europe/Berlin"
php_allow_url_fopen: "On"

php_sendmail_path: "/usr/sbin/sendmail -t -i"
php_output_buffering: "4096"
php_short_open_tag: "Off"
php_disable_functions: []

php_session_cookie_lifetime: 0
php_session_gc_probability: 1
php_session_gc_divisor: 1000
php_session_gc_maxlifetime: 1440
php_session_save_handler: files
php_session_save_path: ''
php_session_cache_expire: 180

php_error_reporting: "E_ALL & ~E_DEPRECATED & ~E_STRICT"
php_display_errors: "Off"
php_display_startup_errors: "Off"

php_custom_packages: []

php_fpm_default_pool:
  delete: false
  name: www.conf
```

### custom packages

To install more PHP packages, you can find a list at `php_custom_packages` specify.

E.G.:

```
php_custom_packages:
  - php-ldap
```

The packages do not require version information, as it would be necessary for RedHat and Remis packages, for example. The role takes care that the package name is valid.

As an example, `php-ldap` would be `php73-php-ldap`.


### php pools

```
php_fpm_pools:
  - name: worker-01
    user: "{{ php_fpm_pool_user }}"
    group: "{{ php_fpm_pool_group }}"
    listen.owner: "{{ php_fpm_pool_user }}"
    listen.group: "{{ php_fpm_pool_group }}"
    listen: "{{ php_fpm_socket_directory }}/$pool.sock"
    # static, dynamic or ondemand
    pm: ondemand
    pm.max_children: 10
    pm.start_servers: 4
    pm.min_spare_servers: 2
    pm.max_spare_servers: 6
    pm.status_path: /status

  - name: worker-02
    user: "{{ php_fpm_pool_user }}"
    group: "{{ php_fpm_pool_group }}"
    listen.owner: "{{ php_fpm_pool_user }}"
    listen.group: "{{ php_fpm_pool_group }}"
    listen: "{{ php_fpm_socket_directory }}/$pool.sock"
    pm: dynamic
    pm.max_children: 10
    pm.start_servers: 4
    pm.min_spare_servers: 2
    pm.max_spare_servers: 6
    pm.status_path: /status
    ping.path: /ping
    ping.response: pong
    access.log: "{{ php_fpm_log_directory }}/$pool_access.log"
    access.format: "%R - %n - %{HTTP_HOST}e - %u %t \"%m %r [%Q%q]\" %s %f %{mili}d %{kilo}M %C%%"
    chdir: /
    env:
      PATH: "/usr/local/bin:/usr/bin:/bin"
      TMPDIR: "{{ php_fpm_tmp_upload_diectory }}"
    php_admin_value:
      date.timezone: "Europe/Berlin"
      log_errors: 'on'
      max_execution_time: 300
      memory_limit: 512M
      upload_max_filesize: 32M
```

### php modules

```
php_modules:
  # gd
  - name: gd
    enabled: true
    priority: 20
    content: |
      extension=gd.so
  # OpCache settings
  - name: opcache
    enabled: true
    priority: 10
    content: |
      zend_extension=opcache.so
      opcache.enable=1
      opcache.enable_cli=1
      opcache.memory_consumption=128
      opcache.interned_strings_buffer=16
      opcache.max_accelerated_files=10000
      opcache.max_wasted_percentage=5
      opcache.validate_timestamps=1
      opcache.revalidate_path=0
      opcache.revalidate_freq=1
      opcache.max_file_size=0
  # PDO mysql
  - name: pdo_mysql
    enabled: true
    priority: 20
    content: |
      extension=pdo_mysql.so
```
