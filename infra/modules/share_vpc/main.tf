# Share the sample subnets with other accounts / an OU via RAM
# (资源访问管理). Enable from the root with:
#   create_sample_vpc = true
#   create_share      = true
#   ram_principals    = ["<account-id-or-ou-id>", ...]

terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.70"
    }
  }
}

variable "region" {
  type    = string
  default = "cn-north-4"
}

variable "share_name" {
  type    = string
}

variable "principals" {
  type    = list(string)
  default = []
}

variable "subnet_ids" {
  type    = list(string)
}

# Base URN up to (and excluding) the resource id, e.g. "vpc:cn-north-4:<pid>:subnet:"
variable "subnet_urn_base" {
  type    = string
}

resource "huaweicloud_ram_resource_share" "this" {
  name          = var.share_name
  description   = "Shared subnets for member-account identification (Name tags)."
  principals    = var.principals
  resource_urns = [for id in var.subnet_ids : "${var.subnet_urn_base}${id}"]
}

output "resource_share_id" {
  value = huaweicloud_ram_resource_share.this.id
}
