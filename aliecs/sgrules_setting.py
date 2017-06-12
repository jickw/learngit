# -*- encoding: utf-8 -*-
import sys
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import AuthorizeSecurityGroupRequest, CreateSecurityGroupRequest
from aliyunsdkecs.request.v20140526 import DescribeSecurityGroupsRequest, JoinSecurityGroupRequest, DescribeSecurityGroupAttributeRequest
import json


#创建一个新的安全组
def create_sg(sg_name):
    request = CreateSecurityGroupRequest.CreateSecurityGroupRequest()
    request.set_accept_format('json')
    request.set_SecurityGroupName(sg_name)
    results = json.loads(client.do_action_with_exception(request))
    return results

#安全组准入规则
def securitygroup_in(sg_id,sourcecidrip,ipprotocol,portrange,nictype,policy):
    request = AuthorizeSecurityGroupRequest.AuthorizeSecurityGroupRequest()
    request.set_accept_format('json')
    request.set_SecurityGroupId(sg_id)
    #设置安全规则的源IP地址范围|IP协议|端口号范围|网络类型|授权策略
    request.set_SourceCidrIp(sourcecidrip)
    request.set_IpProtocol(ipprotocol)
    request.set_PortRange(portrange)
    request.set_NicType(nictype)
    request.set_Policy(policy)
    results = json.loads(client.do_action_with_exception(request))
    return results

#获取对应账户的所有ECS实例id,ip,sg_id
def get_instancesinfo():
    request = DescribeInstancesRequest.DescribeInstancesRequest()
    request.set_accept_format('json')
    request.set_PageSize(100)
    results = json.loads(client.do_action_with_exception(request)).get('Instances').get('Instance')
    id_list = []
    ip_list = []
    sgip_list = {}
    for result in results:
        id_list.append(result['InstanceId'])
        ip_list.append(
            (result['PublicIpAddress']['IpAddress'][0], result['InnerIpAddress']['IpAddress'][0]))
        sgip_list[result['InstanceId']] = result['SecurityGroupIds']['SecurityGroupId'][0]
    return (id_list, ip_list, sgip_list)

#根据安全组名字获取对应的安全组id
def get_sg_id(sg_name):
    request = DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest()
    request.set_accept_format('json')
    results = json.loads(client.do_action_with_exception(request))
    json.dumps(results)
    # print results[u'SecurityGroups'][u'SecurityGroup']
    for name in results[u'SecurityGroups'][u'SecurityGroup']:
        # print name
        if sg_name == name[u'SecurityGroupName']:
            return name[u'SecurityGroupId']

#添加所有ECS内网ip加入安全组准入规则
def create_sg_rule(ip_list, sg_id, ipprotocol, portrange, nicetype, policy):
    exist_ip = get_sg_inrules(sg_id)
    for ip in ip_list:
        if ip[1] not in exist_ip:
            securitygroup_in(sg_id, ip[1], ipprotocol, portrange, nicetype, policy)

#将ECS加入对应的安全组
def join_sg(id_list, sg_id, sgid_list):
    print id_list
    for id in id_list:
        if sg_id not in sgid_list[id]:
            request = JoinSecurityGroupRequest.JoinSecurityGroupRequest()
            request.set_accept_format('json')
            request.set_InstanceId(id)
            request.set_SecurityGroupId(sg_id)
            results = json.loads(client.do_action_with_exception(request))
            print results

#获取安全组准入规则SourceCidrIp
def get_sg_inrules(sg_id):
    request = DescribeSecurityGroupAttributeRequest.DescribeSecurityGroupAttributeRequest()
    request.set_accept_format('json')
    request.set_SecurityGroupId(sg_id)
    request.set_NicType('intranet')
    request.set_Direction('ingress')
    results = json.loads(client.do_action_with_exception(request))
    json.dumps(results)
    rules_ip = []
    for permission in results['Permissions']['Permission']:
        rules_ip.append(permission['SourceCidrIp'])
    return rules_ip

if __name__ == '__main__':

    '''
    用法说明：
	使用本脚本需要安装python及Acs python SDK 
	pip install aliyunsdkcore
	pip install aliyunsdkecs
    python sgrules_setting.py Access_Key_ID Access_Key_Secret 安全组名称
	
    '''
	
    Access_Key_ID = sys.argv[1]
    Access_Key_Secret = sys.argv[2]
    sg_name = sys.argv[3]
    client = AcsClient(Access_Key_ID, Access_Key_Secret, 'cn-hangzhou')
    #create_sg('pre-test')
    sg_id = get_sg_id('pre-test')
    instancesinfo = get_instancesinfo()
    ipprotocol = 'all'
    portrange = '-1/-1'
    nicetype = 'intranet'
    policy = 'accept'
    innerip_list = instancesinfo[1]
    create_sg_rule(innerip_list, sg_id, ipprotocol, portrange, nicetype, policy)
    id_list = instancesinfo[0]
    sgid_list = instancesinfo[2]
    join_sg(id_list, sg_id, sgid_list)
