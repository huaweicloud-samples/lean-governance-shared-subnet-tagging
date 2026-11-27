provider "huaweicloud" {
  region = var.region
  # AK/SK are read from the environment (HW_ACCESS_KEY / HW_SECRET_KEY).
  # They are NEVER written here (no hard-coded credentials).
}
