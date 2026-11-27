# coding: utf-8
"""
Apply a "Name" tag to a list of VPC / subnet resources by ID.

It receives a pipe-separated list of
"<type>|<id>|<name>" triples and stamps the "Name" tag onto each resource
using the Tag Management Service (TMS) batch_create_tags API.

Why a script and not a Terraform resource?
  Huawei Cloud will not let you *create* a VPC/subnet with a
  fixed, externally-assigned ID. A shared VPC/subnet already exists in the
  sharing account with its real ID, so the only way to tag it from the
  consuming account is an imperative call, implemented here via TMS.

Credentials are read from the environment (never hard-coded):
  HW_ACCESS_KEY   - access key
  HW_SECRET_KEY   - secret key
  HW_REGION_NAME  - e.g. cn-north-4
  HW_PROJECT_ID   - project id (required because vpc/subnet are region-level)

Usage:
  python tag_resources.py --ids-to-names "vpc|<id>|<name>|subnet|<id>|<name>|"

The input format is `type|id|name` triples: TMS batch_create_tags requires a
resource_type, so an explicit type token (vpc | subnet) is the first element
of every triple.
"""

import os
import sys
import argparse

from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdktms.v1 import *
from huaweicloudsdktms.v1.region.tms_region import TmsRegion


def parse_ids_to_names(raw):
    """Parse "type|id|name|type|id|name|..." into a list of (type, id, name).

    Trailing pipe (as produced by the helper generator) is tolerated.
    """
    parts = [p for p in raw.split("|") if p != ""]
    if len(parts) % 3 != 0:
        raise ValueError(
            "ids_to_names must contain triples of type|id|name; "
            "got %d tokens from: %r" % (len(parts), raw)
        )
    triples = []
    for i in range(0, len(parts), 3):
        rtype, rid, name = parts[i], parts[i + 1], parts[i + 2]
        rtype = rtype.strip().lower()
        if rtype not in ("vpc", "subnet"):
            raise ValueError("unsupported resource type %r (expected vpc|subnet)" % rtype)
        if not rid or not name:
            continue
        triples.append((rtype, rid.strip(), name.strip()))
    return triples


def build_client(region):
    ak = os.environ.get("HW_ACCESS_KEY")
    sk = os.environ.get("HW_SECRET_KEY")
    if not ak or not sk:
        raise RuntimeError(
            "HW_ACCESS_KEY / HW_SECRET_KEY must be set in the environment "
            "(credentials are never hard-coded)."
        )
    region = (region or "cn-north-4").lower()
    cred = GlobalCredentials(ak, sk)
    return (
        TmsClient.new_builder()
        .with_credentials(cred)
        # TMS is a global service; its single endpoint is tms.myhuaweicloud.com,
        # reached via the cn-north-4 region constant.
        .with_region(TmsRegion.value_of(region))
        .build()
    )


def tag(triples, project_id):
    client = build_client(os.environ.get("HW_REGION_NAME", "cn-north-4"))
    # TMS batch_create_tags applies ONE tag set to every resource in the batch,
    # so a single call cannot give different "Name" values to different
    # resources (that would duplicate the "Name" key -> TMS.2001). Call once
    # per resource, each with its own Name.
    ok = 0
    for (rtype, rid, name) in triples:
        request = CreateResourceTagRequest()
        request.body = ReqCreateTag(
            tags=[CreateTagRequest(key="Name", value=name)],
            resources=[ResourceTagBody(resource_id=rid, resource_type=rtype)],
            project_id=project_id,
        )
        try:
            response = client.create_resource_tag(request)
        except exceptions.ClientRequestException as e:
            print("ERROR: TMS batch_create_tags failed for %s: %s %s %s"
                  % (rid, e.status_code, e.error_code, e.error_msg), file=sys.stderr)
            sys.exit(1)

        failed = getattr(response, "failed_resources", None) or []
        if failed:
            for f in failed:
                print("WARN: could not tag %s (%s): %s %s"
                      % (getattr(f, "resource_id", rid),
                         getattr(f, "resource_type", rtype),
                         getattr(f, "error_code", ""),
                         getattr(f, "error_msg", "")), file=sys.stderr)
            # Tolerated on purpose: a subnet may not be shared into this account.
            continue
        ok += 1
        print("OK: applied Name=%r to %s %s" % (name, rtype, rid))
    print("Done: applied Name tag to %d/%d resource(s)." % (ok, len(triples)))


def main():
    parser = argparse.ArgumentParser(description="Tag shared VPC/subnets with a Name tag.")
    parser.add_argument("--ids-to-names", default=os.environ.get("IDS_TO_NAMES", ""),
                        help="pipe-separated type|id|name triples (or set IDS_TO_NAMES env)")
    parser.add_argument("--project-id", default=os.environ.get("HW_PROJECT_ID", ""),
                        help="Huawei Cloud project id (region-level resources require it)")
    args = parser.parse_args()

    if not args.ids_to_names:
        raise RuntimeError("ids_to_names is required (--ids-to-names or IDS_TO_NAMES env).")
    if not args.project_id:
        raise RuntimeError("HW_PROJECT_ID (or --project-id) is required for region-level resources.")

    triples = parse_ids_to_names(args.ids_to_names)
    if not triples:
        print("Nothing to tag (empty list).")
        return
    tag(triples, args.project_id)


if __name__ == "__main__":
    main()
