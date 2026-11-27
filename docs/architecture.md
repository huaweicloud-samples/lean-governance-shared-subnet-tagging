# 共享 VPC / 子网名称标签实践（华为云）

## 1. 背景与解决的问题

在通过 **资源访问管理（RAM）** 将 VPC 子网跨账号共享的场景中，使用方（成员账号）能看到被共享的子网，但默认无法像资源所有者那样直观地识别这些子网的用途（例如哪个是公网子网、哪个是私网子网）。

本实践提供一套基于 Terraform 的自动化方案：在使用方账号中，将一份「资源 ID → 名称」的清单批量写入 **Name 标签**，使共享 VPC / 子网在使用方控制台中清晰可辨、便于检索与运维。

## 2. 总体架构

```mermaid
flowchart LR
subgraph 共享账号["共享账号（资源所有者）"]
VPC[(VPC + 子网，带 Name 标签)]
GEN[generate_id_name_list.py<br/>导出 type|id|name 清单]
VPC --> GEN
end

subgraph 使用账号["使用方账号（消费共享资源）"]
TF[Terraform: null_resource<br/>+ local-exec]
PY[tag_resources.py<br/>调用 TMS batch_create_tags]
TMS[(标签管理服务 TMS)]
RES[(共享 VPC / 子网<br/>被打上 Name 标签)]
TF --> PY --> TMS --> RES
end

GEN -.粘贴清单.-> TF
```

要点：

- **共享账号**只需提供一份资源清单（由 `src/scripts/generate_id_name_list.py` 一键生成）。
- **使用方账号**通过 Terraform `null_resource` + `local-exec` 在 `apply` 时执行 `tag_resources.py`，调用 **标签管理服务（TMS）** 的 `batch_create_tags` 接口，为清单中的每个 VPC / 子网打上 `Name` 标签。
- 标签在 `terraform destroy` 后**保留**（与使用方账号对该资源的识别需求一致）。

## 3. 涉及云服务

| 服务 | 用途 |
|------|------|
| 虚拟私有云 VPC / 子网 | 被共享、被打标签的目标资源 |
| 资源访问管理 RAM | 跨账号共享子网（`vpc:subnet`） |
| 标签管理服务 TMS | 统一批量打标签（本方案核心 API） |
| （可选）统一身份认证 IAM | 若采用 FunctionGraph 方案，需委托（agency）授予标签权限 |

## 4. 两种执行形态

| 形态 | 说明 | 适用场景 |
|------|------|----------|
| **直接执行（默认）** | `null_resource` + `local-exec` 调用本机 Python 脚本，凭据来自环境变量 | 运维人员在本地 / CI 中以使用方账号凭据执行 `terraform apply` |
| **函数计算（可选）** | 将打标签逻辑封装为 FunctionGraph 函数，由委托（agency）临时凭据驱动；对应 `src/functions/tag_shared_vpc.py` | 希望完全无服务器化、由资源栈自助完成打标签的团队 |

> 两种形态实现的业务语义完全一致：输入一份 ID→名称 清单，为每个资源打上 `Name` 标签。

## 5. 为什么用 TMS 而不是 VPC 资源标签接口

TMS `batch_create_tags` 是跨服务的统一标签入口，一次调用即可对多个 VPC / 子网批量打标签，且返回 `failed_resources` 便于逐个容忍失败（例如某个子网并未共享到本账号）。这与「尽可能一次性完成、对个别失败不阻断整体」的运维诉求吻合。
