#!/usr/bin/env python

import re #imports regular expression library

class FilterModule:

    @staticmethod
    def filters():
        return {
                'bgp_as_from_rt': FilterModule.bgp_as_from_rt,
                'ios_vrf_rt': FilterModule.ios_vrf_rt,
                'rt_diff': FilterModule.rt_diff
                }

    @staticmethod
    def bgp_as_from_rt(rt_list):
        bgp_as_list = []
        for my_rt in rt_list:
            rt_halves = my_rt.split(':')
            bgp_as_list.append(int(rt_halves[0]))

        return bgp_as_list

    @staticmethod
    def ios_vrf_rt(text):
        vrf_list = ['vrf' + s for s in text.split('vrf') if s]
        return_dict = {}
        for vrf in vrf_list:
            # Parse the VRF name from the definition line
            # little \s matches spaces
            # '+' = match atleast 1 instance (but match all if there is more)
            # big \S matches every other chacter
            name_regex = re.compile(r'vrf\s+definition\s+(?P<name>\S+)')
            name_match = name_regex.search(vrf)
            sub_dict = {}
            vrf_dict = {name_match.group('name'): sub_dict}

            # Parse the RT imports into a list of strings
            rti_regex = re.compile(r'route-target\s+import\s+(?P<rti>\d+:\d+)')
            rti_matches = rti_regex.findall(vrf)
            sub_dict.update({'route_import': rti_matches})

            # Parse the RT exports into a list of strings
            rte_regex = re.compile(r'route-target\s+export\s+(?P<rte>\d+:\d+)')
            rte_matches = rte_regex.findall(vrf)
            sub_dict.update({'route_export': rte_matches})

            # Append dictionary to return list
            return_dict.update(vrf_dict)


        return return_dict

    @staticmethod
    def rt_diff(int_vrf_list, run_vrf_dict):
        """
        Uses set theory to determine the import/export route-targets that should be added or deleted. Only differences are captured, which helps Ansible achieve idempotence when making configuration updates.

        int_vrf_list = intended vrf list
        run_vrf_dict = current running vrf list
        """

        return_list = []
        for int_vrf in int_vrf_list:
            # Copy benign parameteres from intended configuration
            vrf_dict = {
            'name': int_vrf['name'],
            'rd': int_vrf['rd'],
            'description': int_vrf['description']
            }

            # If the intended VRF exists in the running configuration
            run_vrf = run_vrf_dict.get(str(int_vrf['name']))
            if run_vrf:
                # Convert each list to a set
                int_rti = set(int_vrf['route_import'])
                int_rte = set(int_vrf['route_export'])
                run_rti = set(int_vrf['route_import'])
                run_rte = set(int_vrf['route_export'])

                # Perform set "difference" operation
                vrf_dict.update({'add_rti': list(int_rti - run_rti)})
                vrf_dict.update({'del_rti': list(run_rti - int_rti)})
                vrf_dict.update({'add_rte': list(int_rte - run_rte)})
                vrf_dict.update({'del_rte': list(run_rte - int_rte)})


            # Intended VRF Doesn't exist, so add all the RTs
            else:
                vrf_dict.update({'add_rti': int_vrf['route_import']})
                vrf_dict.update({'del_rti': []})
                vrf_dict.update({'add_rte': int_vrf['route_export']})

            # Add the newly created dictionary to the list of Directories
            return_list.append(vrf_dict)

        return return_list
