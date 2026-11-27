# coding: utf-8
"""
Discover every VPC / subnet visible to the *current* account (the consuming
account, when run with its credentials) and print them so you can pick the
shared resources that still lack a "Name" tag.

This is a read-only helper. It intentionally lists resources WITH and WITHOUT
a Name tag (unlike generate_id_name_list.py, which only emits resources that
already carry a Name). Use it to decide what to feed into `ids_to_names`.

Credentials from environment (never hard-coded):
  HW_ACCESS_KEY / HW_SECRET_KEY / HW_REGION_NAME / HW_PROJECT_ID

Usage:
  python discover_resources.py
  python discover_resources.py --emit        # also print an ids_to_names string
                                        # (only for rows you then edit)
"""
import os
import sys
import argparse

from huaweicloudsdkcore.auth.credentials import BasicCredentials, GlobalCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkvpc.v2 import *
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion
from huaweicloudsdktms.v1 import TmsClient, ShowResourceTagRequest
from huaweicloudsdktms.v1.region.tms_region import TmsRegion


def name_from(tags):
    if not tags:
        return ""
    for t in tags:
        if getattr(t, "key", None) == "Name":
            return getattr(t, "value", "") or ""
    return ""


def build_vpc_client(region, project_id):
    ak = os.environ.get("HW_ACCESS_KEY")
    sk = os.environ.get("HW_SECRET_KEY")
    if not ak or not sk:
        raise RuntimeError("HW_ACCESS_KEY / HW_SECRET_KEY must be set in the environment.")
    cred = BasicCredentials(ak, sk, project_id or "")
    return (
        VpcClient.new_builder()
        .with_credentials(cred)
        .with_region(VpcRegion.value_of(region))
        .build()
    )


def build_tms_client(region):
    ak = os.environ.get("HW_ACCESS_KEY")
    sk = os.environ.get("HW_SECRET_KEY")
    cred = GlobalCredentials(ak, sk)
    return (
        TmsClient.new_builder()
        .with_credentials(cred)
        .with_region(TmsRegion.value_of(region))
        .build()
    )


def tms_name(tms_client, project_id, rtype, rid):
    """Authoritative Name tag from TMS (the VPC list API does NOT surface
    TMS-applied tags, so we query TMS directly)."""
    try:
        r = tms_client.show_resource_tag(
            ShowResourceTagRequest(resource_id=rid, resource_type=rtype, project_id=project_id)
        )
        return name_from(getattr(r, "tags", None))
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="List all VPCs/subnets in the account.")
    parser.add_argument("--region", default=os.environ.get("HW_REGION_NAME", "cn-north-4"))
    parser.add_argument("--project-id", default=os.environ.get("HW_PROJECT_ID", ""))
    parser.add_argument("--emit", action="store_true", help="also print an ids_to_names string")
    args = parser.parse_args()

    vpc_client = build_vpc_client(args.region, args.project_id)
    tms_client = build_tms_client(args.region)
    rows = []  # (type, id, name, cidr, vpc_id)

    try:
        vpcs = vpc_client.list_vpcs(ListVpcsRequest()).vpcs or []
    except exceptions.ClientRequestException as e:
        print("ERROR listing VPCs: %s %s %s" % (e.status_code, e.error_code, e.error_msg),
              file=sys.stderr)
        sys.exit(1)

    for vpc in vpcs or []:
        name = tms_name(tms_client, args.project_id, "vpc", vpc.id) or name_from(getattr(vpc, "tags", None))
        rows.append(("vpc", vpc.id, name, getattr(vpc, "cidr", ""), ""))
        try:
            subnets = vpc_client.list_subnets(ListSubnetsRequest(vpc_id=vpc.id)).subnets or []
        except exceptions.ClientRequestException:
            continue
        for s in subnets:
            sname = tms_name(tms_client, args.project_id, "subnet", s.id) or name_from(getattr(s, "tags", None))
            rows.append(("subnet", s.id, sname, getattr(s, "cidr", ""), vpc.id))

    if not rows:
        print("No VPC/subnet found in this account/region.")
        return

    print("%-7s %-22s %-24s %-18s %s" % ("TYPE", "ID", "NAME(TMS)", "CIDR", "VPC_ID"))
    print("-" * 100)
    for r in rows:
        print("%-7s %-22s %-24s %-18s %s" % (r[0], r[1], r[2] or "<无Name>", r[3], r[4]))

    if args.emit:
        emitted = ["%s|%s|%s" % (r[0], r[1], r[2] or "Unnamed") for r in rows]
        print("\n# ids_to_names (edit names as needed):")
        print("|".join(emitted) + "|")


if __name__ == "__main__":
    main()
