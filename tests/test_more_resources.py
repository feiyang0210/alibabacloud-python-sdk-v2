# Copyright 2019 Alibaba Cloud Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import time

from alibabacloud import ECSInstanceResource
from aliyunsdkecs.request.v20140526.CreateLaunchTemplateRequest import CreateLaunchTemplateRequest
from aliyunsdkecs.request.v20140526.CreateSecurityGroupRequest import CreateSecurityGroupRequest
from aliyunsdkecs.request.v20140526.CreateVSwitchRequest import CreateVSwitchRequest
from aliyunsdkecs.request.v20140526.CreateVpcRequest import CreateVpcRequest
from aliyunsdkecs.request.v20140526.DeleteInstanceRequest import DeleteInstanceRequest
from aliyunsdkecs.request.v20140526.DeleteSecurityGroupRequest import DeleteSecurityGroupRequest
from aliyunsdkecs.request.v20140526.DeleteVSwitchRequest import DeleteVSwitchRequest
from aliyunsdkecs.request.v20140526.DeleteVpcRequest import DeleteVpcRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeNatGatewaysRequest import DescribeNatGatewaysRequest
from aliyunsdkecs.request.v20140526.DescribeRouterInterfacesRequest import DescribeRouterInterfacesRequest
from aliyunsdkecs.request.v20140526.DescribeSecurityGroupsRequest import DescribeSecurityGroupsRequest
from aliyunsdkecs.request.v20140526.DescribeVSwitchesRequest import DescribeVSwitchesRequest
from aliyunsdkecs.request.v20140526.DescribeVpcsRequest import DescribeVpcsRequest
from aliyunsdkrds.request.v20140815.DescribeDBInstancesRequest import DescribeDBInstancesRequest
from tests.base import SDKTestBase

def resources_request(response, key1, key2):
    response_list = list()
    for x in response[key1][key2]:
        for y in x.values():
            response_list.append(y)
    return response_list


class MockResponseTest(SDKTestBase):

    def test_ecs_disk(self):
        # Create Disk
        ecs = self._get_resource("ecs")
        disk = ecs.create_disk(ZoneId="cn-hangzhou-e", Size=30, DiskCategory="cloud_ssd")
        while True:
            time.sleep(1)
            disk.refresh()
            if disk.status == "Available":
                break
        # Delete Disk
        disk.delete()

        # Create 2 Disks
        instance = ecs.create_instance(ImageId="coreos_1745_7_0_64_30G_alibase_20180705.vhd",
                                       InstanceType="ecs.n2.small", ZoneId="cn-hangzhou-e")
        disk = ecs.create_disk(ZoneId="cn-hangzhou-e", Size=30, DiskCategory="cloud_ssd")
        while True:
            time.sleep(1)
            disk.refresh()
            if disk.status == "Available":
                break
        # Attach Disk to an Instance
        disk.attach(InstanceId=instance.instance_id)
        # Create 3 Disks
        # get 3 disks and check attributes
        disk = ecs.create_disk(ZoneId="cn-hangzhou-g", Size=30, DiskCategory="cloud_ssd")
        self.assertTrue(disk.disk_id)

    def test_ecs_images(self):
        # create image
        ecs = self._get_resource("ecs")
        instance = ecs.create_instance(ImageId="coreos_1745_7_0_64_30G_alibase_20180705.vhd",
                                       InstanceType="ecs.n2.small", ZoneId="cn-hangzhou-e")
        instance.start()
        instance.wait_until(ECSInstanceResource.STATUS_RUNNING)
        # time.sleep(5)
        while True:
            time.sleep(1)
            instance.refresh()
            if instance.status == "Running":
                break

        image = ecs.create_image(InstanceId = instance.instance_id)
        # delete image
        image.delete()
        # create 2 images
        # get 2 images and check attributes
        image = ecs.create_image(InstanceId = instance.instance_id)
        print(instance.zone_id)
        self.assertTrue(image.image_id)

    def test_vpc_eip_address(self):
        vpc = self._get_resource("vpc")
    #     # Loop to delete the ecs instance
        ecs = self._get_resource("ecs")
        # Let the product SDK stop smoothly
        for instance in ecs.instances.filter(Status='Running').page_size(100):
            instance.refresh()
            print(instance.instance_id)
        print(len(list(ecs.instances.filter(Status='Running').page_size(100))))
        # time.sleep(30)
        for instance in list(ecs.instances.all().page_size(100)):
            if instance.status == 'Stopped':
                instance.delete()
        # Let the product SDK delete smoothly
        time.sleep(30)
        # Loop delete EIP
        for eip in vpc.eip_addresses.all().page_size(100):
            eip.release()

        # Loop deletion switch
        slb = self._get_resource("slb")
        describe_vswitches_request = DescribeVSwitchesRequest()
        describe_vswitches_request.set_PageSize(50)
        describe_vswitches_response = self.client.do_action_with_exception(describe_vswitches_request)
        describe_vswitches_response = json.loads(describe_vswitches_response.decode("utf-8"), encoding="utf-8")

        describe_db_instance_request = DescribeDBInstancesRequest()
        describe_db_instance_request.set_PageSize(50)
        describe_db_instance_response = self.client.do_action_with_exception(describe_db_instance_request)
        describe_db_instance_response = json.loads(describe_db_instance_response.decode("utf-8"), encoding="utf-8")
        for vswitch in describe_vswitches_response["VSwitches"]["VSwitch"]:
            # Determine if the ecs depends on the switch
            if len(list(ecs.instances.filter(VSwitchId=vswitch["VSwitchId"]).page_size(100))) == 0:
                # Determine whether RDS depends on the switch
                if vswitch["VSwitchId"] not in resources_request(describe_db_instance_response, "Items", "DBInstance"):
                    # Determine if the load balancer is dependent on the switch
                    if len(list(slb.load_balancers.filter(VSwitchId=vswitch["VSwitchId"]).page_size(100))) == 0:
                        if vswitch["Status"] == "Available":
                            delete_vswitches_request = DeleteVSwitchRequest()
                            delete_vswitches_request.set_VSwitchId(vswitch["VSwitchId"])

        # Looping the security group
        DescribeInstancesRequest()
        describe_security_groups_request = DescribeSecurityGroupsRequest()
        describe_security_groups_request.set_PageSize(50)
        describe_security_groups_response = self.client.do_action_with_exception(describe_security_groups_request)
        describe_security_groups_response = json.loads(describe_security_groups_response.decode("utf-8"), encoding="utf-8")
        group_list = describe_security_groups_response["SecurityGroups"]["SecurityGroup"]
        for security_group in group_list:
            collections = ecs.instances.filter(SecurityGroupId=security_group["SecurityGroupId"]).page_size(100)
            # collections= ecs.instances.filter(SecurityGroupId="sg-i-bp17add25vlwt2pdehlr").page_size(100)

            # print(len(list(ecs.instances.filter(SecurityGroupId="sg-i-bp17add25vlwt2pdehlr").page_size(100))))
            #
            # print(len(list(ecs.instances.filter(VpcId="vpc-bp1p2w6vzg6plnsek0mxe").page_size(100))))
            # # collections = ecs.instances.all()
            # print(len(list(collections)))
            if len(list(collections)) == 0:
                delete_security_groups_request = DeleteSecurityGroupRequest()
                delete_security_groups_request.set_SecurityGroupId(security_group["SecurityGroupId"])
                delete_security_groups_response = self.client.do_action_with_exception(delete_security_groups_request)

        # Loop delete VPC
        describe_vpc_request = DescribeVpcsRequest()
        describe_vpc_request.set_PageSize(50)
        describe_vpc_response = self.client.do_action_with_exception(describe_vpc_request)
        describe_vpc_response = json.loads(describe_vpc_response.decode("utf-8"), encoding="utf-8")
        describe_nat_gateway_request = DescribeNatGatewaysRequest()
        describe_nat_gateway_request.set_PageSize(50)
        describe_nat_gateway_response = self.client.do_action_with_exception(describe_nat_gateway_request)
        describe_nat_gateway_response = json.loads(describe_nat_gateway_response.decode("utf-8"), encoding="utf-8")
        router_interfaces_request = DescribeRouterInterfacesRequest()
        router_interfaces_request.set_PageSize(50)
        router_interfaces_reqsponse = self.client.do_action_with_exception(router_interfaces_request)
        router_interfaces_reqsponse = json.loads(router_interfaces_reqsponse.decode("utf-8"), encoding="utf-8")

        for vpcs in describe_vpc_response["Vpcs"]["Vpc"]:
            print("0000000000000")
            # Determine if the ecs depends on the vpc
            if len(list(ecs.instances.filter(VpcId=vpcs["VpcId"]).page_size(100))) == 0:
                # Determine if the RDS depends on the vpc
                if vpcs["VpcId"] not in resources_request(describe_db_instance_response, "Items", "DBInstance"):
                    print("1111111111")
                    # Determine if the switch depends on the vpc
                    if vpcs["VpcId"] not in resources_request(describe_vswitches_response,"VSwitches", "VSwitch"):
                        # Determine if the NAT depends on the vpc
                        if vpcs["VpcId"] not in resources_request(describe_nat_gateway_response,"NatGateways", "NatGateway"):
                            # Determine whether the security group depends on VPC
                            if vpcs["VpcId"] not in resources_request(describe_security_groups_response, "SecurityGroups", "SecurityGroup"):
                                # Determine whether the RouterInterfaces depends on VPC
                                if vpcs["VpcId"] not in resources_request(router_interfaces_reqsponse,"RouterInterfaceSet", "RouterInterfaceType"):
                                    print("222222222222222")
                                    # Determine if the load balancer is dependent on the vpc
                                    if len(list(slb.load_balancers.filter(VpcId=vpcs["VpcId"]).page_size(100))) == 0:
                                        if vpcs["Status"] == "Available":
                                            delete_vpc_request = DeleteVpcRequest()
                                            delete_vpc_request.set_VpcId(vpcs["VpcId"])
                                            delete_vpc_response = self.client.do_action_with_exception(delete_vpc_request)

        # Create a VPC
        request = CreateVpcRequest()
        response_vpc = self.client.do_action_with_exception(request)
        response_vpc = json.loads(response_vpc.decode("utf-8"), encoding="utf-8")
        while True:
            time.sleep(1)
            describe_vpc_request = DescribeVpcsRequest()
            describe_vpc_request.set_VpcId(response_vpc.get("VpcId"))
            describe_vpc_response = self.client.do_action_with_exception(describe_vpc_request)
            describe_vpc_response = json.loads(describe_vpc_response.decode("utf-8"), encoding="utf-8")
            if describe_vpc_response["Vpcs"]["Vpc"][0]["Status"] == 'Available':
                break

        # Create switch
        request = CreateVSwitchRequest()
        request.set_ZoneId("cn-hangzhou-b")
        request.set_CidrBlock("172.16.0.0/24")
        request.set_VpcId(response_vpc.get("VpcId"))
        response_vswitch = self.client.do_action_with_exception(request)
        response_vswitch = json.loads(response_vswitch.decode("utf-8"), encoding="utf-8")
        while True:
            time.sleep(1)
            describe_vswitches_request = DescribeVSwitchesRequest()
            describe_vswitches_request.set_VSwitchId(response_vswitch["VSwitchId"])
            describe_vswitches_response = self.client.do_action_with_exception(describe_vswitches_request)
            describe_vswitches_response = json.loads(describe_vswitches_response.decode("utf-8"), encoding="utf-8")
            if describe_vswitches_response["VSwitches"]["VSwitch"][0]["Status"] == 'Available':
                break

        # # Create Security Group
        # request = CreateSecurityGroupRequest()
        # request.set_VpcId(response_vpc.get("VpcId"))
        # response = self.client.do_action_with_exception(request)
        # time.sleep(1)

        # create vpc EIP address
        eip_address = vpc.allocate_eip_address()
        instance = ecs.create_instance(
            ImageId="coreos_1745_7_0_64_30G_alibase_20180705.vhd",
            InstanceType="ecs.n2.small",
            VSwitchId=response_vswitch.get("VSwitchId"))
        while True:
            time.sleep(1)
            instance.refresh()
            if instance.status == "Stopped":
                break

        # associate EIP to an ECS instance
        eip_address.refresh()
        eip_address.associate(InstanceId=instance.instance_id, AllocationId=eip_address.allocation_id, RegionId=eip_address.region_id)
        while True:
            time.sleep(1)
            eip_address.refresh()
            if eip_address.status == "InUse":
                break

        # unassociate eip address
        eip_address.unassociate(InstanceId=instance.instance_id)

        # delete eip address
        while True:
            time.sleep(1)
            eip_address.refresh()
            if eip_address.status == "Available":
                break
        eip_address.release()

        # create 2 EIP addresses
        eip_address = vpc.allocate_eip_address()
        # get 2 eip addresses and check attributes
        eip_address.refresh()
        self.assertTrue(eip_address.ip_address)

    def test_slb_load_balancer(self):
        # create 1 load balancer
        slb = self._get_resource("slb")
        load_balancer = slb.create_load_balancer()
        # rename load balancers and refresh() and check the name
        load_balancer.set_name(LoadBalancerName="test_load_balancer")
        load_balancer.refresh()
        while True:
            time.sleep(1)
            load_balancer.refresh()
            if load_balancer.load_balancer_status == "active":
                break
        self.assertEqual(load_balancer.load_balancer_name, "test_load_balancer")
        # delete load balancer
        load_balancer.delete()
        # create 2 load balancers
        load_balancer = slb.create_load_balancer()
        # get 2 load balancers and check attributes
        self.assertTrue(load_balancer.load_balancer_id)

