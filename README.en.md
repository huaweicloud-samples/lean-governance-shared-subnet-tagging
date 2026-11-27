# lean-governance-shared-subnet-tagging

![License](https://img.shields.io/badge/License-MIT--0-blue.svg)
![Huawei Cloud](https://img.shields.io/badge/Huawei%20Cloud-华为云-red.svg)
![Terraform](https://img.shields.io/badge/IaC-Terraform%20%2B%20huaweicloud-7B42BC.svg)
![Build](https://img.shields.io/badge/validate-Success-brightgreen.svg)

## 1. Overview

### Introduction

After VPC subnets are shared across accounts through **Resource Access Management (RAM)**, the consumer account cannot easily identify the purpose of those subnets by default. This practice provides a Terraform-based automation solution: in the consumer account, a "resource ID → name" list is batch-written into **Name tags**, so shared VPC / subnets are clearly identifiable in the console and easy to search and operate.

Target audience: operations and platform teams that use RAM to share VPC / subnets and want to fill in Name tags uniformly in the consumer account.

---

## 2. Table of Contents

- [1. Overview](#1-overview)
- [2. Table of Contents](#2-table-of-contents)
- [3. Architecture Diagram](#3-architecture-diagram)
- [4. Highlights](#4-highlights)
- [5. Cloud Services Used](#5-cloud-services-used)
- [6. Prerequisites](#6-prerequisites)
- [7. Quick Start](#7-quick-start)
- [8. Step-by-Step Deployment](#8-step-by-step-deployment)
- [9. Usage / Verification](#9-usage--verification)
- [10. Cleanup](#10-cleanup)
- [11. Detailed Explanation](#11-detailed-explanation)
- [12. Dependencies](#12-dependencies)
- [13. FAQ / Troubleshooting](#13-faq--troubleshooting)
- [14. Contributing](#14-contributing)
- [15. License](#15-license)
- [16. Contact / Maintainers](#16-contact--maintainers)

---

## 3. Architecture Diagram

```mermaid
flowchart LR
subgraph Owner["Shared account (resource owner)"]
VPC[(VPC + subnets with Name tags)]
GEN[generate_id_name_list.py<br/>exports type|id|name list]
VPC --> GEN
end
subgraph Consumer["Consumer account (uses shared resources)"]
TF[Terraform: null_resource + local-exec]
PY[tag_resources.py → TMS batch_create_tags]
RES[(Shared VPC / subnets<br/>tagged with Name)]
TF --> PY --> RES
end
GEN -.paste list.-> TF
```

---

## 4. Highlights

- **No runtime resources**: the core tagging action creates no cloud resources; it only calls the Tag Management Service API.
- **One-click completion**: the consumer account only needs to paste a list and run `terraform apply`.
- **Failure tolerant**: if an individual subnet is not actually shared to this account, the overall run is not affected.
- **Two forms**: lightweight by default (local script); optional serverless form (FunctionGraph).

---

## 5. Cloud Services Used

- VPC (Virtual Private Cloud)
- RAM (Resource Access Management)
- TMS (Tag Management Service)
- FunctionGraph (optional)

---

## 6. Prerequisites

- A Huawei Cloud account with **TMS tag creation permission** (`tms:resourceTags:create`) in the target region and read-only VPC permission.
- Terraform >= 1.0 (verified with 1.9.x in this repository).
- Python 3.9+, with the following installed:
```bash
pip install huaweicloudsdkcore huaweicloudsdktms
# If you use the list generation script in the shared account, also install:
pip install huaweicloudsdkvpc
```
- Export the credentials in the consumer account shell (**never write them to a file**):
```bash
export HW_ACCESS_KEY="<your-access-key>" HW_SECRET_KEY="<your-secret-key>"
export HW_REGION_NAME="cn-north-4" HW_PROJECT_ID="<your-project-id>"
```

---

## 7. Quick Start

```bash
# 1) Prepare the list in the consumer account (option A: generate it with one command in the shared account and paste it; or construct it manually)
# Format: vpc|<id>|<Name>|subnet|<id>|<Name>|

# 2) Configure variables
cd infra && cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and fill in region / project_id / ids_to_names

# 3) Initialize and validate
terraform init && terraform validate

# 4) Deploy (apply tags)
terraform apply
```

---

## 8. Step-by-Step Deployment

1. **Generate the list** (shared account): `python ../src/scripts/generate_id_name_list.py --vpc-id <vpc-id>`, then copy the output.
2. **Configure variables**: fill `ids_to_names` (a triplet string) and `project_id` in `infra/terraform.tfvars`.
3. **Initialize**: `terraform init` (installs the huaweicloud and null providers).
4. **Validate**: `terraform validate` → `Success! The configuration is valid.`
5. **Deploy**: `terraform apply` → outputs `OK: applied Name tag to N resource(s).`
6. **Verify**: confirm in the console that the Name tags are displayed.

---

## 9. Usage / Verification

### Usage and Verification

Minimal example (pass variables directly, no tfvars needed):
```bash
terraform apply \
-var="project_id=<your-project-id>" \
-var='ids_to_names=vpc|<vpc-id>|My Shared VPC|subnet|<subnet-id>|Shared Private Subnet A|'
```

Verification: log in to the consumer account console → VPC / subnet list, confirm that the corresponding resources show the `Name` tag; or call the tag query API to check.

After deployment, follow these steps to verify that the business functionality works before considering the delivery complete.

---

## 10. Cleanup

- The core tagging module **creates no runtime resources**; `terraform destroy` does not delete cloud resources and the Name tags remain.
- If `create_sample_vpc` / `create_share` are enabled, run `terraform destroy` to release the corresponding VPC / RAM share.

---

## 11. Detailed Explanation

- **Input protocol**: Huawei Cloud TMS requires `resource_type`, so each entry is a `type|id|name` triplet (`type` ∈ `vpc`/`subnet`).
- **Two execution forms**: the default `null_resource + local-exec` calls a local script; the optional serverless FunctionGraph form is in `src/functions/tag_shared_vpc.py`.
- **Tag persistence**: `destroy` does not remove Name tags, which matches the consumer's need to identify resources.

---

## 12. Dependencies

- Huawei Cloud Terraform Provider (`huaweicloud/huaweicloud`)
- Huawei Cloud Python SDKs: `huaweicloudsdkcore`, `huaweicloudsdktms`, `huaweicloudsdkvpc`

---

## 13. FAQ / Troubleshooting

### FAQ

- **Q: TMS reports a failure when tagging a resource?** A: Usually that subnet is not actually shared to this account; this is an expected, tolerable failure (the script outputs WARN and continues).
- **Q: Can it be fully serverless with FunctionGraph?** A: Yes; refer to `src/functions/tag_shared_vpc.py` and the architecture adaptation document.
- **Q: Does it continuously create runtime resources?** A: No; the core action is an API call and creates no runtime resources.

---

## 14. Contributing

Issues and PRs are welcome. Please follow the existing directory structure and code style in the repository.

---

## 15. License

This practice is licensed under **MIT No Attribution**; see the [`LICENSE`](LICENSE) file in the repository root.

This project is released under the **MIT-0** License. See [LICENSE](LICENSE).

---

## 16. Contact / Maintainers
| Item | Content |
|---|---|
| **Creator** | [dgc-git](https://github.com/dgc-git) |
| **Maintainer** | [dgc-git](https://github.com/dgc-git) |
| **Contact** | GitHub Issues / PR (see [Section 14](#14-contributing)) |
