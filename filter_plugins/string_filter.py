# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# from ansible.errors import AnsibleError, AnsibleParserError
# from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

# https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html
# https://blog.oddbit.com/post/2019-04-25-writing-ansible-filter-plugins/

display = Display()


class FilterModule(object):
    '''
        Ansible filters. Python string operations.
    '''

    def filters(self):
        return {
            'string_prefix': self.string_prefix,
            'string_postfix': self.string_postfix
        }

    def string_prefix(self, prefix, s):
        """
        """
        return prefix + s

    def string_postfix(self, postfix, s):
        """
        """
        return s + postfix
