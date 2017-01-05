from ne_base import NosDeviceAction


class Add_Ipv4_Rule_Acl(NosDeviceAction):
    def run(self, mgmt_ip, username, password, acl_name, seq_id,
            action, protocol_type, source, destination, dscp, vlan_id,
            count, log):
        """Run helper methods to add an L3 IPV4 ACL rule to an existing ACL
        """
        self.setup_connection(host=mgmt_ip, user=username, passwd=password)
        try:
            device = self.asset(ip_addr=self.host, auth=self.auth)
            self.logger.info('successfully connected to %s to enable interface', self.host)
        except AttributeError as e:
            self.logger.error("Failed to connect to %s due to %s", self.host, e.message)
            raise ValueError('Failed to connect to %s due to %s', self.host, e.message)
        except ValueError as verr:
            self.logger.error("Error while logging in to %s due to %s",
                              self.host, verr.message)
            raise ValueError("Error while logging in to %s due to %s",
                             self.host, verr.message)
        except self.ConnectionError as cerr:
            self.logger.error("Connection failed while logging in to %s due to %s",
                              self.host, cerr.message)
            raise ValueError("Connection failed while logging in to %s due to %s",
                             self.host, cerr.message)
        except self.RestInterfaceError as rierr:
            self.logger.error("Failed to get a REST response while logging in "
                              "to %s due to %s", self.host, rierr.message)
            raise ValueError("Failed to get a REST response while logging in "
                             "to %s due to %s", self.host, rierr.message)
        seq = []
        output = {}
        seq_variables_std = ('seq_id', 'action', 'src_host_any_ip', 'src_host_ip',
                             'src_mask', 'count', 'log')
        seq_variables_ext = ('seq_id', 'action', 'protocol_type', 'src_host_any_ip',
                             'src_host_ip', 'src_mask', 'src_port', 'src_port_number_eq_neq_tcp',
                             'src_port_number_lt_tcp', 'src_port_number_gt_tcp',
                             'src_port_number_eq_neq_udp', 'src_port_number_lt_udp',
                             'src_port_number_gt_udp', 'src_port_number_range_lower_tcp',
                             'src_port_number_range_lower_udp', 'src_port_number_range_higher_tcp',
                             'src_port_number_range_higher_udp', 'dst_host_any_ip', 'dst_host_ip',
                             'dst_mask', 'dst_port', 'dst_port_number_eq_neq_tcp',
                             'dst_port_number_lt_tcp', 'dst_port_number_gt_tcp',
                             'dst_port_number_eq_neq_udp', 'dst_port_number_lt_udp',
                             'dst_port_number_gt_udp', 'dst_port_number_range_lower_tcp',
                             'dst_port_number_range_lower_udp', 'dst_port_number_range_higher_tcp',
                             'dst_port_number_range_higher_udp', 'dscp', 'urg', 'ack', 'push',
                             'fin', 'rst', 'sync', 'vlan', 'count', 'log')
        try:
            acl_type = self._get_acl_type_(device, acl_name)['type']
            self.logger.info('successfully identified the acl_type as %s', acl_type)
        except:
            self.logger.error('cannot get acl_type')
            raise ValueError('cannot get acl_type')
        if acl_type == 'standard':
            seq_variables = seq_variables_std
        elif acl_type == 'extended':
            seq_variables = seq_variables_ext
        if acl_type == 'extended' and destination is None:
            self.logger.error('Destination required in extended access list')
            raise ValueError('Destination required in extended access list')
        elif acl_type == 'extended' and protocol_type is None:
            self.logger.error('protocol_type is required for extended access list')
            raise ValueError('protocol_type is required for extended access list')
        elif acl_type == 'standard' and destination:
            self.logger.error('Destination cannot be given for standard access list')
            raise ValueError('Destination cannot be given for standard access list')
        elif acl_type == 'standard' and protocol_type:
            self.logger.error('protocol_type cannot be given for standard access list')
            raise ValueError('protocol_type cannot be given for standard access list')
        try:
            seq_dict = {key: None for key in seq_variables}
        except:
            self.logger.error('Cannot get seq_variables')
            raise ValueError('Cannot get seq_variables')

        if seq_id is None:
            self.logger.info('seq_id not provided getting the seq_id')
            seq_id = self._get_seq_id_(device, acl_name, acl_type)
            if seq_id is None:
                self.logger.error('Cannot get seq_id')
                raise ValueError('Cannot get seq_id')
        self.logger.info('seq_id for the rule is %s', seq_id)
        src_dict = self._parse_(protocol_type, source, 'src')
        if acl_type == 'extended':
            dst_dict = self._parse_(protocol_type, destination, 'dst')
        for variable in seq_dict:
            if 'src' in variable:
                try:
                    seq_dict[variable] = src_dict[variable]
                except:
                    pass
            elif 'dst' in variable:
                try:
                    seq_dict[variable] = dst_dict[variable]
                except:
                    pass
            else:
                try:
                    seq_dict[variable] = eval(variable)
                except:
                    pass
        seq_dict['urg'] = 'False'
        seq_dict['fin'] = 'False'
        seq_dict['rst'] = 'False'
        seq_dict['sync'] = 'False'
        for v in seq_variables:
            seq.append(seq_dict[v])
        try:
            changes = self._add_ipv4_acl_(device,
                                          acl_name=acl_name,
                                          acl_type=acl_type,
                                          seq=tuple(seq))
        except Exception as msg:
            self.logger.error(msg)
            raise ValueError(msg)
        output['result'] = changes
        self.logger.info('closing connection to %s after adding rule access-list-- '
                         'all done!', self.host)
        return output

    def _parse_(self, protocol_type, statement, key):
        self.logger.info('parsing the %s statement', key)
        output = {}
        msg = None
        statement_list = statement.split(" ")
        map(lambda x: x.strip(",. \n-"), statement_list)
        if statement_list[0] == 'any' and len(statement_list) == 1:
            output[key + '_host_any_ip'] = statement_list.pop(0)
        elif statement_list[0] == 'host':
            try:
                output[key + '_host_any_ip'] = statement_list.pop(0)
                host_ip = statement_list.pop(0)
                if self._validate_ip_(host_ip):
                    output[key + '_host_ip'] = host_ip
                else:
                    msg = 'host ip in {} statement is invalid'.format(key)
            except:
                msg = 'host ip missing in {} statement'.format(key)
        elif self._validate_ip_(statement_list[0]):
            output[key + '_host_any_ip'] = statement_list.pop(0)
            try:
                output[key + '_mask'] = statement_list.pop(0)
            except:
                msg = 'IP address mask missing in {} statement'.format(key)
        else:
            msg = 'Incorrect {} statement'.format(key)
        if msg is not None:
            self.logger.error(msg)
            raise ValueError(msg)
        try:
            port = statement_list[0]
        except:
            return output
        if statement_list[0] in ['lt', 'gt', 'eq', 'range', 'neq']:
            output[key + '_port'] = port
            statement_list.pop(0)
            if port in ['eq', 'neq']:
                port = 'eq_neq'
            if port != 'range':
                try:
                    output[key + '_port_number_' + port +
                           '_' + protocol_type] = statement_list.pop(0)
                except:
                    msg = '{} port number {} missing'.format(key, port)
            else:
                try:
                    output[key + '_port_number_' + port + '_lower_' +
                           protocol_type] = statement_list.pop(0)
                    output[key + '_port_number_' + port + '_higher_' +
                           protocol_type] = statement_list.pop(0)
                except:
                    msg = '{} port numbers range missing'.format(key)

        else:
            msg = 'Incorrect {} statement'.format(key)

        if msg is not None:
            self.logger.error(msg)
            raise ValueError(msg)
        return output

    def _add_ipv4_acl_(self, device, acl_name, acl_type, seq):
        self.logger.info('Adding rule on access list- %s',
                         acl_name)
        result = 'False'
        try:
            if acl_type == 'standard':
                add_acl = device.ip_access_list_standard_seq_create
            elif acl_type == 'extended':
                add_acl = device.ip_access_list_extended_seq_create
            else:
                self.logger.error('Invalid access list type %s', acl_type)
                raise ValueError('Invalid access list type %s', acl_type)
            aply = list(add_acl(acl_name, seq))
            result = str(aply[0])
            if str(aply[0]) == 'False':
                self.logger.error('Cannot add rule on %s due to %s', acl_name,
                                  str(aply[1][0][self.host]['response']['json']['output']))
            else:
                self.logger.info('Successfully added rule on %s', acl_name)
        except (KeyError, AttributeError, ValueError) as e:
            self.logger.error('Cannot add rule on %s due to %s', acl_name, e.message)
            raise ValueError(e.message)
        return result
