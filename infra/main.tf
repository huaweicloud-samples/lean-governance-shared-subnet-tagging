# =============================================================================
# Core: tag shared VPC / subnets with a "Name" tag in the consuming account.
#
# 在使用方账号中为通过 RAM 共享来的 VPC / 子网批量打 Name 标签，
# 便于在控制台与 API 中清晰识别共享资源。
#
# Why null_resource + local-exec instead of a Terraform VPC/subnet resource?
#   You cannot *create* a VPC/subnet with a fixed, externally-assigned ID, and
#   a shared resource already exists in the sharing account. The only way to
#   tag it from the consumer account is an imperative API call. The
#   null_resource local-exec is Terraform's standard idiom for "run this at
#   apply time". Tags persist on `terraform destroy` (no destroy provisioner).
#
# No running resources are created — only TMS API calls.
# =============================================================================

resource "null_resource" "tag_shared_resources" {
  count = var.ids_to_names != "" ? 1 : 0

  # Re-run the tagging whenever the list or target project/region changes.
  triggers = {
    ids_to_names = var.ids_to_names
    project_id   = var.project_id
    region       = var.region
  }

  provisioner "local-exec" {
    # Windows cmd /C quoting pitfalls:
    #  - root module path.module resolves relative, so use an absolute repo-root
    #    path via dirname(abspath(path.module)) with FORWARD slashes (Python on
    #    Windows accepts them) and do NOT wrap the path in quotes.
    #  - ids_to_names contains "|" (a cmd pipe metacharacter). Passing it as a
    #    command-line argument fights cmd's quoting/escaping, so instead we push
    #    it through the provisioner `environment` block as IDS_TO_NAMES — Terraform
    #    sets it as a real process env var (no cmd parsing), and the script reads
    #    it from there. HW_ACCESS_KEY / HW_SECRET_KEY are inherited from the
    #    surrounding shell and are never hard-coded here.
    command = "${var.python_exe} ${dirname(abspath(path.module))}/src/scripts/tag_resources.py"

    environment = {
      HW_REGION_NAME = var.region
      HW_PROJECT_ID  = var.project_id
      IDS_TO_NAMES   = var.ids_to_names
    }
  }
}

# ---- Optional helpers (default OFF) -----------------------------------------
module "sample_vpc" {
  count  = var.create_sample_vpc ? 1 : 0
  source = "./modules/sample_vpc"

  region           = var.region
  vpc_cidr         = var.sample_vpc_cidr
  vpc_name         = var.sample_vpc_name
}

module "share_vpc" {
  count  = (var.create_sample_vpc && var.create_share) ? 1 : 0
  source = "./modules/share_vpc"

  region          = var.region
  share_name      = "${var.sample_vpc_name}-subnets"
  principals      = var.ram_principals
  subnet_ids      = module.sample_vpc[0].subnet_ids
  subnet_urn_base = "vpc:${var.region}:${var.project_id}:subnet:"
}
