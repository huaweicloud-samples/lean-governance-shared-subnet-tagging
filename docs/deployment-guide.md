# 部署指导书（华为云）

本指导书说明如何在「使用方账号」中，将共享 VPC / 子网的 `Name` 标签批量补齐。

## 1. 前置条件

- 已开通华为云账号，并具备目标区域的 **TMS 标签创建权限**（`tms:resourceTags:create`）及 VPC 只读权限。
- 已安装 **Terraform >= 1.0**（本仓库在 1.9.x 验证）。
- 已安装 **Python 3.9+**，并安装标签服务 SDK（该 Python 必须是 `terraform apply` 时 `local-exec` 调用的那个 `python`）：
```bash
pip install -r ../src/requirements.txt # 推荐：锁定依赖版本
# 或手动：pip install huaweicloudsdkcore huaweicloudsdktms
```
若使用「共享账号生成清单」脚本，还需：
```bash
pip install huaweicloudsdkvpc
```
- 在使用方账号的 Shell 中导出凭据（**绝不写入任何文件**，见安全红线）：
```bash
export HW_ACCESS_KEY="<你的AK>"
export HW_SECRET_KEY="<你的SK>"
export HW_REGION_NAME="cn-north-4"
export HW_PROJECT_ID="<你的项目ID>"
```
- 若机器上存在多个 Python 解释器，可在 `terraform.tfvars` 用 `python_exe` 变量显式指定**已装 SDK** 的那个解释器的绝对路径，避免 `local-exec` 调错 Python：
```hcl
python_exe = "C:/Path/To/Python/with/sdk/python.exe"
```

## 2. 准备资源清单

**方式 A — 在共享账号一键生成**（推荐）：
```bash
cd src/scripts
python generate_id_name_list.py --vpc-id <共享VPC的ID>
# 输出形如：vpc|<vpc-id>|<Name>|subnet|<subnet-id>|<Name>|
```

**方式 B — 手动构造**：
格式为 `type|id|name` 三元组，以 `|` 连接：
```
vpc|<vpc-id>|My Shared VPC|subnet|<subnet-id>|Shared Private Subnet A|
```
> 注意：TMS 需要 `resource_type`，因此每条必须显式写出 `vpc` 或 `subnet`。

## 3. 配置变量

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# 编辑 terraform.tfvars，填入 region / project_id / ids_to_names
```

## 4. 初始化与校验

```bash
terraform init
terraform validate # 应输出 Success! The configuration is valid.
```

## 5. 部署（打标签）

```bash
terraform apply
```

`apply` 过程中，`null_resource` 的 `local-exec` 会执行 `tag_resources.py`，调用 TMS 批量打标签。
输出示例：
```
OK: applied Name tag to 3 resource(s).
```

> 若个别资源返回 `WARN: could not tag ...`，通常是该子网未实际共享到本账号，属预期内的可容忍失败。

## 6. 验证

在华为云控制台「使用方账号」的 VPC / 子网列表，确认对应资源已显示 `Name` 标签；或用 CLI 查询资源标签核对。

> ⚠️ **重要**：VPC/子网的列表类 API（`list_vpcs`/`list_subnets`）**不一定回显**经 TMS 打上的标签。请以 **TMS `show_resource_tag`** 或控制台「资源标签」视图为准。本仓库的 `src/scripts/discover_resources.py` 已改为直接查询 TMS，能正确显示真实 Name 标签，用它来核对最稳妥。

## 7. 清理

本方案的**核心打标签动作不创建任何运行资源**，仅通过 API 完成标签写入。
- 若仅使用了核心打标签模块：`terraform destroy` 不会删除任何云资源（只移除本地状态），Name 标签**保留**在使用方账号。
- 若启用了 `create_sample_vpc` / `create_share` 等可选辅助模块，执行 `terraform destroy` 会释放相应 VPC / 共享。

## 8. 可选：端到端自测

如需在本账号内完整演练「建 VPC → 共享 → 打标签」，在 `terraform.tfvars` 中设置：
```hcl
create_sample_vpc = true
create_share = true
ram_principals = ["<目标账号或OU的ID>"]
```
> 注意：`create_share = true` 时，目标账号需在 RAM 控制台接受共享邀请后，打标签才会生效。
