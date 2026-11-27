variable "region" {
  description = "Huawei Cloud region, e.g. cn-north-4"
  type        = string
  default     = "cn-north-4"
}

variable "project_id" {
  description = "Huawei Cloud project id. Required because vpc/subnet are region-level resources and TMS batch_create_tags needs it."
  type        = string
  # No default: must be supplied via tfvars / environment (HW_PROJECT_ID).
}

# Python interpreter used by the null_resource local-exec to run the tagging
# helper. Defaults to "python" (resolved from PATH), but can be overridden with
# an absolute path to a Python that has huaweicloudsdkcore + huaweicloudsdktms
# installed (avoids ambiguity when several Pythons exist on the machine).
variable "python_exe" {
  description = "Python interpreter for the tagging local-exec. Must have huaweicloudsdkcore and huaweicloudsdktms installed."
  type        = string
  default     = "python"
}

# Core input: the list of resources to tag.
# TMS batch_create_tags requires a resource_type, so each entry is a triple:
#   "vpc|<vpc-id>|<Name>|subnet|<subnet-id>|<Name>|"
# Generate it in the sharing account with src/scripts/generate_id_name_list.py
variable "ids_to_names" {
  description = "Pipe-separated type|id|name triples of the shared VPC/subnets to Name-tag in this (consuming) account."
  type        = string
  default     = ""
}

# ---- Optional helpers (default OFF; a plain apply creates no cloud resources) ----

variable "create_sample_vpc" {
  description = "Create a sample VPC + subnets (with Name tags) to share. Helper for end-to-end testing only."
  type        = bool
  default     = false
}

variable "create_share" {
  description = "Share the sample subnets with other accounts/OU via RAM. Requires create_sample_vpc=true."
  type        = bool
  default     = false
}

variable "ram_principals" {
  description = "List of principals (account ids or organization/OU ids) to share the subnets with."
  type        = list(string)
  default     = []
}

variable "sample_vpc_cidr" {
  description = "CIDR for the sample VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "sample_vpc_name" {
  description = "Name tag prefix for the sample VPC and its subnets."
  type        = string
  default     = "shared-demo"
}
