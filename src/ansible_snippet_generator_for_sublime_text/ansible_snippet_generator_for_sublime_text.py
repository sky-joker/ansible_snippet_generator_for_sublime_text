#!/usr/bin/env python
import json
import re
import subprocess
from subprocess import PIPE
from collections import OrderedDict
from typing import List, Dict


def get_all_module() -> List:
    module_list = []
    result = subprocess.Popen(['ansible-doc', '-l'], stdout=PIPE, stderr=PIPE)
    for module in result.communicate()[0].decode('utf-8').split("\n"):
        if module:
            module_name = re.findall(r'^[a-z0-9_.]+', module)[0]
            module_list.append(module_name)

    return module_list

def get_module_doc(module: str) -> Dict:
    result = subprocess.Popen(['ansible-doc', module, '-j'], stdout=PIPE, stderr=PIPE)
    try:
        module_doc = json.loads(result.communicate()[0])
    except Exception:
        module_doc = {}

    return module_doc

def get_suboptions(value: dict) -> List:
    params = []
    for key, value in OrderedDict(sorted(value['suboptions'].items())).items():
        #params.append("  %s: # %s" % (key, value['type']))
        params.append("%s:" % key)
        if 'suboptions' in value.keys():
            suboptions = get_suboptions(value)
            params += list(map(lambda x: "  %s" % x, suboptions))

    return params

def generate_snippet_file(module: str, params: List):
    with open('origin/%s.sublime-snippet' % module, 'a') as f:
        num = 1
        f.write("<snippet>\n")
        f.write("<content><![CDATA[\n")
        f.write("- name: ${%s:task name}\n" % num)
        f.write("  %s:\n" % module)
        for param in params:
            f.write("    ${%s:%s${%s:}}\n" % (num+1, param, num+2))
            num += 2

            #f.write("    ${%s:%s: ${%s:%s}}\n" % (num+1, param.split(":")[0], num+2, param.split(":")[1]))
            #num += 2
        f.write("]]></content>\n")
        f.write("    <tabTrigger>%s</tabTrigger>\n" % module.split('.').pop())
        f.write("    <scope>source.ansible</scope>\n")
        f.write("</snippet>\n")

def main():
    module_list = get_all_module()

    list_of_modules_that_had_problems = []
    #for module in ['community.vmware.vmware_host_iscsi', 'community.vmware.vmware_host_iscsi_info']:
    for module in module_list:
        params = []
        module_doc = get_module_doc(module)
        if not module_doc:
            list_of_modules_that_had_problems.append(module)
            continue

        if 'options' in module_doc[module]['doc']:
            for key, value in OrderedDict(sorted(module_doc[module]['doc']['options'].items())).items():
                #params.append("%s: # %s" % (key, value['type']))
                params.append("%s:" % key)
                if 'suboptions' in value.keys():
                    suboptions = get_suboptions(value)
                    params += list(map(lambda x: "  %s" % x, suboptions))
        #else:
        #    list_of_modules_that_had_problems.append(module)

        generate_snippet_file(module, params)

    if list_of_modules_that_had_problems:
        print(list_of_modules_that_had_problems)

if __name__ == "__main__":
    main()
