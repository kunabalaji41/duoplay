variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_allowed_cidr_blocks" {
  type    = list(string)
  default = ["10.0.0.0/16"]
}

module "rds" {
  source              = "../../modules/rds"
  environment         = "prod"
  db_password         = var.db_password
  allowed_cidr_blocks = var.db_allowed_cidr_blocks
}

resource "aws_security_group_rule" "postgres_private" {
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = var.db_allowed_cidr_blocks
  security_group_id = "sg-prod-db"
}

