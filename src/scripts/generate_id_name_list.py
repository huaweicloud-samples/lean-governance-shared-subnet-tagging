# coding: utf-8
"""
Generate the "type|id|name|..." input string for tag_resources.py.

Run THIS in the *sharing* account (the account that owns the VPC). It lists
every VPC and subnet together with its "Name" tag and prints a pipe-separated
triple string that you then paste into the consuming account's Terraform
variable `ids_to_names`.

It uses the Huawei Cloud VPC API (list_vpcs / list_subnets) to build the string
directly.

Credentials from environment:
  HW_ACCESS_KEY / HW_SECRET_KEY / HW_REGION_NAME / HW_PROJECT_ID

Usage:
  python generate_id_name_list.py [--vpc-id <id>]
"""

import os
import argparse

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkvpc.v2 import *
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion


def name_from(tags):
    if not tags:
        return ""
    for t in tags:
        if getattr(t, "key", None) == "Name":
            return getattr(t, "value", "") or ""
    return ""


def build_client(region):
    ak = os.environ.get("HW_ACCESS_KEY")
    sk = os.environ.get("HW_SECRET_KEY")
    if not ak or not sk:
        raise RuntimeError("HW_ACCESS_KEY / HW_SECRET_KEY must be set in the environment.")
    cred = BasicCredentials(ak, sk, os.environ.get("HW_PROJECT_ID", ""))
    return (
        VpcClient.new_builder()
        .with_credentials(cred)
        .with_region(VpcRegion.value_of(region))
        .build()
    )


def main():
    parser = argparse.ArgumentParser(description="Build the ids_to_names triple string.")
    parser.add_argument("--vpc-id", default="", help="limit to one VPC (optional)")
    parser.add_argument("--region", default=os.environ.get("HW_REGION_NAME", "cn-north-4"))
    args = parser.parse_args()

    client = build_client(args.region)
    out = []

    try:
        if args.vpc_id:
            vpcs = [client.show_vpc(ShowVpcRequest(vpc_id=args.vpc_id)).vpc]
        else:
            vpcs = client.list_vpcs(ListVpcsRequest()).vpcs or []
    except exceptions.ClientRequestException as e:
        print("ERROR listing VPCs: %s %s" % (e.status_code, e.error_code), file=__import__("sys").stderr)
        raise

    for vpc in vpcs or []:
        out.append("vpc|%s|%s" % (vpc.id, name_from(getattr(vpc, "tags", None))))

    for vpc in vpcs or []:
        try:
            subnets = client.list_subnets(ListSubnetsRequest(vpc_id=vpc.id)).subnets or []
        except exceptions.ClientRequestException:
            continue
        for s in subnets:
            out.append("subnet|%s|%s" % (s.id, name_from(getattr(s, "tags", None))))

    print("|".join([o for o in out if o.split("|")[2] != ""]) + "|")


if __name__ == "__main__":
    main()
