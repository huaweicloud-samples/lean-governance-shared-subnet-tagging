terraform {
  required_version = ">= 1.0"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.70"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}
