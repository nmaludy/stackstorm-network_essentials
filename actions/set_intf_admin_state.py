# Copyright 2016 Brocade Communications Systems, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ne_base import NosDeviceAction


class SetIntfAdminState(NosDeviceAction):
    """
       Implements the logic to enable ports/port-channel on VDX switches.
       This action acheives the below functionality
           1.Interface validation
           2.Enable physical interface/port-channel/ve/loopback on a device
    """

    def run(self, mgmt_ip, username, password, intf_type, intf_name, rbridge_id, enabled,
            intf_desc):
        """Run helper methods to implement the desired state.
        """
        self.setup_connection(host=mgmt_ip, user=username, passwd=password)
        changes = {}

        intf_type = intf_type.lower()
        with self.pmgr(conn=self.conn, auth=self.auth) as device:
            self.logger.info('successfully connected to %s to enable interface', self.host)
            # Check is the user input for Interface Name is correct
            interface_list = self.expand_interface_range(intf_type=intf_type, intf_name=intf_name,
                             rbridge_id=rbridge_id)
            valid_desc = True
            if intf_desc and intf_type not in ['ve', 'loopback']:
                # if description is passed we validate that the length is good.
                valid_desc = self.check_int_description(intf_description=intf_desc)

            if interface_list and valid_desc:
                changes['interface'] = self._set_intf_admin_state(device, intf_type=intf_type,
                                                                  intf_name=interface_list,
                                                                  rbridge_id=rbridge_id,
                                                                  enabled=enabled,
                                                                  intf_desc=intf_desc)
            else:
                raise ValueError('Input is not a valid Interface / description')
            self.logger.info('closing connection to %s after configuring enable interface -- '
                             'all done!', self.host)
        return changes

    def _set_intf_admin_state(self, device, intf_type, intf_name, rbridge_id, enabled, intf_desc):
        """Configure the interface to be administratively up or down.
        """
        for intf in intf_name:
            is_intf_interface_present = False
            intf = str(intf)
            if rbridge_id and intf_type in ['ve', 'loopback']:
                # This verification will not work if ve and loopback is not already configured
                conf = device.interface.admin_state(get=True, name=intf, int_type=intf_type,
                                                    rbridge_id=rbridge_id)
            else:
                # This verification will not work if port-channel is not already configured or
                # interface is already enabled
                conf = device.interface.admin_state(get=True, name=intf, int_type=intf_type)
            if conf and enabled:
                self.logger.info('Interface %s %s is already enabled', intf_type, intf)
                is_intf_interface_present = True
            elif not conf and not enabled:
                self.logger.info('Interface %s %s is already disabled on %s',
                                 intf_type, intf, self.host)
                is_intf_interface_present = True
            if not is_intf_interface_present:
                self.logger.info('Setting admin state on intf-type-%s intf-name-%s',
                                 intf_type, intf)
                if rbridge_id and intf_type in ['ve', 'loopback']:
                    device.interface.admin_state(enabled=enabled, name=intf, int_type=intf_type,
                                                 rbridge_id=rbridge_id)
                else:
                    device.interface.admin_state(enabled=enabled, name=intf, int_type=intf_type)

            if intf_type not in ['ve', 'loopback']:
                if intf_desc:
                    device.interface.description(int_type=intf_type, name=intf,
                                                 desc=intf_desc)
                else:
                    self.logger.debug('Skipping description configuration')

        return True
