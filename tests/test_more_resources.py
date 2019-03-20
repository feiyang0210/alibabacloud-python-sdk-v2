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
        # Loop to delete the ecs instance
        ecs = self._get_resource("ecs")
        for instance in list(ecs.instances.all()):
            if instance.status == 'Stopped':
                instance.delete()

        # Loop delete EIP
        for eip in vpc.eip_addresses.all():
            eip.release()

        describe_vswitches_request = DescribeVSwitchesRequest()
        describe_vswitches_response = self.client.do_action_with_exception(describe_vswitches_request)
        describe_vswitches_response = json.loads(describe_vswitches_response.decode("utf-8"), encoding="utf-8")
        print(describe_vswitches_response)

        # Loop deletion switch
        slb = self._get_resource("slb")
        describe_db_instance_request = DescribeDBInstancesRequest()
        for vswitch in describe_vswitches_response["VSwitches"]["VSwitch"]:
            # Determine if the ecs depends on the switch
            for instance in ecs.instances.filter(VSwitchId=vswitch["VSwitchId"]):
                if instance is not None:
                    break
            # Determine whether RDS depends on the switch
            # describe_db_instance_request.set_VSwitchId(vswitch["VSwitchId"])
            describe_db_instance_response = self.client.do_action_with_exception(describe_db_instance_request)
            describe_db_instance_response = json.loads(describe_db_instance_response.decode("utf-8"), encoding="utf-8")
            print(describe_db_instance_response)
            for vswitches in describe_db_instance_response["Items"]["DBInstance"]:
                if vswitch["VSwitchId"] == vswitches["VSwitchId"]:
                    break

            # Determine if the load balancer is dependent on the switch
            for load_balancer in slb.load_balancers.filter(VSwitchId=vswitch["VSwitchId"]):
                continue
            print(vswitch["VSwitchId"])
            if vswitch["Status"] == "Available":
                delete_vswitches_request = DeleteVSwitchRequest()
                delete_vswitches_request.set_VSwitchId(vswitch["VSwitchId"])
                delete_vswitches_response = self.client.do_action_with_exception(delete_vswitches_request)

        # Loop delete VPC
        describe_vpc_request = DescribeVpcsRequest()
        describe_vpc_request.set_IsDefault(True)
        describe_vpc_response = self.client.do_action_with_exception(describe_vpc_request)
        describe_vpc_response = json.loads(describe_vpc_response.decode("utf-8"), encoding="utf-8")

        print(describe_vpc_response)
        describe_db_instance_request = DescribeDBInstancesRequest()
        describe_nat_gateway_request = DescribeNatGatewaysRequest()
        describe_security_groups_request = DescribeSecurityGroupsRequest()
        # describe_router_interfaces_request = DescribeRouterInterfacesRequest()
        for vpc in describe_vpc_response["Vpcs"]["Vpc"]:
            # Determine if the ecs depends on the vpc
            for instance in ecs.instances.filter(VpcId=vpc["VpcId"]):
                continue
            # Determine if the RDS depends on the vpc
            describe_db_instance_request.set_VpcId(vpc["VpcId"])
            if self.client.do_action_with_exception(describe_db_instance_request):
                continue
            # Determine if the switch depends on the vpc
            describe_vswitches_request.set_VpcId(vpc["VpcId"])
            if self.client.do_action_with_exception(describe_vswitches_request):
                continue
            # Determine if the NAT depends on the vpc
            describe_nat_gateway_request.set_VpcId(vpc["VpcId"])
            if self.client.do_action_with_exception(describe_nat_gateway_request):
                continue
            # Determine whether the security group depends on VPC
            describe_security_groups_request.set_VpcId(vpc["VpcId"])
            if self.client.do_action_with_exception(describe_security_groups_request):
                continue
            # Determine if the load balancer is dependent on the vpc
            for load_balancer in slb.load_balancers.filter(vpc["VpcId"]):
                continue

            if vpc["Status"] == "Available":
                delete_vpc_request = DeleteVpcRequest()
                delete_vpc_request.set_VpcId(vpc["VpcId"])
                delete_vpc_response = self.client.do_action_with_exception(delete_vpc_request)
                delete_vpc_response = json.loads(delete_vpc_response.decode("utf-8"), encoding="utf-8")

        # # Looping the security group
        # describe_security_groups_request = DescribeSecurityGroupsRequest()
        # describe_security_groups_response = self.client.do_action_with_exception(describe_security_groups_request)
        # describe_security_groups_response = json.loads(describe_security_groups_response.decode("utf-8"), encoding="utf-8")
        # print("daqwde"*30)
        # print(describe_security_groups_response)
        # for security_group in describe_security_groups_response["SecurityGroups"]["SecurityGroup"]:
        #     # if security_group.get("Instances") != None:
        #     # print(security_group["SecurityGroupId"])
        #     delete_security_groups_request = DeleteSecurityGroupRequest()
        #     delete_security_groups_request.set_SecurityGroupId(security_group["SecurityGroupId"])
        #     delete_security_groups_response = self.client.do_action_with_exception(delete_security_groups_request)
        #     response = json.loads(delete_security_groups_response.decode("utf-8"), encoding="utf-8")
        #     print(response.get("RequestId"))
        # print("*"*20)

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

