# lean-governance-shared-subnet-tagging · 共享 VPC / 子网名称标签实践（华为云）

![License](https://img.shields.io/badge/License-MIT--0-blue.svg)
![Huawei Cloud](https://img.shields.io/badge/Huawei%20Cloud-华为云-red.svg)
![Terraform](https://img.shields.io/badge/IaC-Terraform%20%2B%20huaweicloud-7B42BC.svg)
![Build](https://img.shields.io/badge/validate-Success-brightgreen.svg)

## 1. 简介 / Overview

### 简介


通过 **资源访问管理（RAM）** 将 VPC 子网跨账号共享后，使用方账号默认难以直观识别这些子网的用途。本实践提供一套基于 Terraform 的自动化方案：在使用方账号中，把一份「资源 ID → 名称」清单批量写入 **Name 标签**，让共享 VPC / 子网在控制台中清晰可辨、便于检索与运维。

适用对象：使用 RAM 共享 VPC / 子网、希望在使用方账号统一补齐名称标签的运维与平台团队。

---

## 2. 目录

- [1. 简介 / Overview](#1-简介--overview)
- [2. 目录](#2-目录)
- [3. 架构图](#3-架构图)
- [4. 方案亮点](#4-方案亮点)
- [5. 涉及云服务](#5-涉及云服务)
- [6. 前置条件](#6-前置条件)
- [7. 快速开始](#7-快速开始)
- [8. 分步部署](#8-分步部署)
- [9. 使用方法 / 验证](#9-使用方法--验证)
- [10. 清理资源](#10-清理资源)
- [11. 详细说明](#11-详细说明)
- [12. 依赖](#12-依赖)
- [13. FAQ / 故障排除](#13-faq--故障排除)
- [14. 贡献指南](#14-贡献指南)
- [15. 许可证](#15-许可证)
- [16. 联系方式 / 维护者](#16-联系方式--维护者)

---

## 3. 架构图

```mermaid
flowchart LR
subgraph 共享账号["共享账号（资源所有者）"]
VPC[(VPC + 子网，带 Name 标签)]
GEN[generate_id_name_list.py<br/>导出 type|id|name 清单]
VPC --> GEN
end
subgraph 使用账号["使用方账号（消费共享资源）"]
TF[Terraform: null_resource + local-exec]
PY[tag_resources.py → TMS batch_create_tags]
RES[(共享 VPC / 子网<br/>被打上 Name 标签)]
TF --> PY --> RES
end
GEN -.粘贴清单.-> TF
```

---

## 4. 方案亮点

- **无运行资源**：核心打标签动作不创建任何云资源，仅为标签服务 API 调用。
- **一键补齐**：使用方账号只需粘贴一份清单并执行 `terraform apply`。
- **可容忍失败**：个别子网未实际共享到本账号时，不影响整体。
- **两种形态**：默认轻量（本机脚本）；可选无服务器（FunctionGraph）。

---

## 5. 涉及云服务

- VPC（虚拟私有云）
- RAM（资源访问管理）
- TMS（标签管理服务）
- FunctionGraph（函数工作流，可选）

---

## 6. 前置条件

- 华为云账号，具备目标区域 **TMS 标签创建权限**（`tms:resourceTags:create`）及 VPC 只读权限。
- Terraform >= 1.0（本仓库在 1.9.x 验证）。
- Python 3.9+，并安装：
```bash
pip install huaweicloudsdkcore huaweicloudsdktms
# 若用共享账号生成清单脚本，另需：
pip install huaweicloudsdkvpc
```
- 在使用方 Shell 导出凭据（**绝不写入文件**）：
```bash
export HW_ACCESS_KEY="<你的AK>" HW_SECRET_KEY="<你的SK>"
export HW_REGION_NAME="cn-north-4" HW_PROJECT_ID="<你的项目ID>"
```

---

## 7. 快速开始

```bash
# 1) 在使用方账号准备清单（方式 A：共享账号一键生成后粘贴；或手动构造）
# 格式：vpc|<id>|<Name>|subnet|<id>|<Name>|

# 2) 配置变量
cd infra && cp terraform.tfvars.example terraform.tfvars
# 编辑 terraform.tfvars 填入 region / project_id / ids_to_names

# 3) 初始化与校验
terraform init && terraform validate

# 4) 部署（打标签）
terraform apply
```

---

## 8. 分步部署

1. **生成清单**（共享账号）：`python ../src/scripts/generate_id_name_list.py --vpc-id <vpc-id>`，复制输出。
2. **配置变量**：在 `infra/terraform.tfvars` 填入 `ids_to_names`（三元组字符串）、`project_id`。
3. **初始化**：`terraform init`（安装 huaweicloud 与 null provider）。
4. **校验**：`terraform validate` → `Success! The configuration is valid.`
5. **部署**：`terraform apply` → 输出 `OK: applied Name tag to N resource(s).`
6. **验证**：在控制台确认 Name 标签已显示。

---

## 9. 使用方法 / 验证

### 使用方法与验证


最简示例（直接传参，免去 tfvars）：
```bash
terraform apply \
-var="project_id=<项目ID>" \
-var='ids_to_names=vpc|<vpc-id>|My Shared VPC|subnet|<subnet-id>|Shared Private Subnet A|'
```

验证：登录使用方账号控制台 → VPC / 子网列表，确认对应资源显示 `Name` 标签；或调用标签查询接口核对。

部署完成后请按本节步骤自行验证，确认业务功能可用，方可视为交付完成。

---

## 10. 清理资源

- 核心打标签模块**不创建任何运行资源**，`terraform destroy` 不会删除云资源，Name 标签保留。
- 若启用了 `create_sample_vpc` / `create_share`，执行 `terraform destroy` 释放对应 VPC / RAM 共享。

---

## 11. 详细说明

- **输入协议**：华为云 TMS 要求 `resource_type`，故每条为 `type|id|name` 三元组（`type` ∈ `vpc`/`subnet`）。
- **两种执行形态**：默认 `null_resource + local-exec` 调用本机脚本；可选 FunctionGraph 无服务器形态见 `src/functions/tag_shared_vpc.py`。
- **标签持久性**：`destroy` 不移除 Name 标签，与使用方对资源的识别需求一致。

---

## 12. 依赖

- 华为云 Terraform Provider（`huaweicloud/huaweicloud`）
- 华为云 Python SDK：`huaweicloudsdkcore`、`huaweicloudsdktms`、`huaweicloudsdkvpc`

---

## 13. FAQ / 故障排除

### FAQ


- **Q：TMS 报某个资源打标签失败？** A：通常是该子网未实际共享到本账号，属预期可容忍失败（脚本输出 WARN 并继续）。
- **Q：能用 FunctionGraph 完全无服务器化吗？** A：可以，参考 `src/functions/tag_shared_vpc.py` 与架构适配文档。
- **Q：会持续产生运行资源吗？** A：不会，核心动作为 API 调用，无运行资源。

---

## 14. 贡献指南

欢迎提交 Issue 与 PR。请遵循仓库内现有目录结构与代码风格。

---

## 15. 许可证

本实践采用 **MIT No Attribution** 许可证，详见仓库根目录 [`LICENSE`](LICENSE) 文件。


本项目以 **MIT-0** 许可证发布。详见 [LICENSE](LICENSE)。

---

## 16. 联系方式 / 维护者
| 项 | 内容 |
|---|---|
| **创建者** | [dgc-git](https://github.com/dgc-git) |
| **维护者** | [dgc-git](https://github.com/dgc-git) |
| **联系方式** | GitHub Issues / PR（见[第 14 节](#14-贡献指南)） |
