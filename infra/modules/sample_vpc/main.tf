# Simplified sample VPC + subnets WITH Name tags, for the "sharing account"
# side of an end-to-end test. Kept minimal: VPC + 2 subnets with Name tags.
# No NAT/EIP/bandwidth are created.
#
# Enable from the root with:  create_sample_vpc = true

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

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "vpc_name" {
  type    = string
  default = "shared-demo"
}

resource "huaweicloud_vpc" "this" {
  name = "${var.vpc_name}-vpc"
  cidr = var.vpc_cidr
  tags = {
    Name = "${var.vpc_name}-vpc"
  }
}

resource "huaweicloud_vpc_subnet" "a" {
  name       = "${var.vpc_name}-subnet-a"
  vpc_id     = huaweicloud_vpc.this.id
  cidr       = cidrsubnet(var.vpc_cidr, 8, 0) # /24
  gateway_ip = cidrhost(cidrsubnet(var.vpc_cidr, 8, 0), 1)
  tags = {
    Name = "${var.vpc_name}-subnet-a"
  }
}

resource "huaweicloud_vpc_subnet" "b" {
  name       = "${var.vpc_name}-subnet-b"
  vpc_id     = huaweicloud_vpc.this.id
  cidr       = cidrsubnet(var.vpc_cidr, 8, 1) # /24
  gateway_ip = cidrhost(cidrsubnet(var.vpc_cidr, 8, 1), 1)
  tags = {
    Name = "${var.vpc_name}-subnet-b"
  }
}

output "vpc_id" {
  value = huaweicloud_vpc.this.id
}

output "subnet_ids" {
  value = [huaweicloud_vpc_subnet.a.id, huaweicloud_vpc_subnet.b.id]
}
