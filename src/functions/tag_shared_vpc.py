# coding: utf-8
"""
FunctionGraph handler — 使用 FunctionGraph 委托临时凭据调用 TMS 打标签。

It runs with an *agency* (委托) so it uses temporary credentials
from the FunctionGraph context — no long-term AK/SK is stored.

Deploy it together with:
  - huaweicloud_identity_agency   (execution role, grants tms:resourceTags:create)
  - huaweicloud_lts_group/stream  (logs)
  - huaweicloud_fgs_function       (the function itself)

The function is invoked by a null_resource local-exec. If you prefer to run
the tagging directly on the operator machine instead of via FunctionGraph, use
src/scripts/tag_resources.py instead (the default path in infra/main.tf).

Event payload:
  {
    "RequestType": "Create" | "Update" | "Delete",
    "ResourceProperties": { "IdsToNamesList": "vpc|<id>|<name>|subnet|<id>|<name>|" }
  }
"""

import json

from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdktms.v1 import *
from huaweicloudsdktms.v1.region.tms_region import TmsRegion


def _parse(raw):
    parts = [p for p in raw.split("|") if p != ""]
    triples = []
    for i in range(0, len(parts), 3):
        rtype, rid, name = parts[i], parts[i + 1], parts[i + 2]
        if rtype.strip().lower() not in ("vpc", "subnet"):
            continue
        if not rid or not name:
            continue
        triples.append((rtype.strip().lower(), rid.strip(), name.strip()))
    return triples


def handler(event, context):
    request_type = event.get("RequestType", "Create")
    response = {"status": "SUCCESS"}

    # On Delete: tags are intentionally kept.
    if request_type == "Delete":
        return response

    props = event.get("ResourceProperties", {})
    raw = props.get("IdsToNamesList", "")
    triples = _parse(raw)
    if not triples:
        return response

    ak = context.getAccessKey()
    sk = context.getSecretKey()
    token = context.getSecurityKey()
    cred = GlobalCredentials(ak, sk, token)
    client = (
        TmsClient.new_builder()
        .with_credentials(cred)
        .with_region(TmsRegion.value_of(""))
        .build()
    )

    project_id = context.getProjectId() if hasattr(context, "getProjectId") else ""
    request = CreateResourceTagRequest()
    request.body = ReqCreateTag(
        tags=[CreateTagRequest(key="Name", value=t[2]) for t in triples],
        resources=[ResourceTagBody(resource_id=t[1], resource_type=t[0]) for t in triples],
        project_id=project_id,
    )
    try:
        client.create_resource_tag(request)
    except exceptions.ClientRequestException as e:
        print("WARN: TMS tagging error: %s %s %s" % (e.status_code, e.error_code, e.error_msg))
        # Tolerate per-resource failures (e.g. a subnet not shared here).
    return response
