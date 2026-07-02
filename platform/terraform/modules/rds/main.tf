variable "environment" {
  type = string
}

variable "db_password" {
  type        = string
  description = "Master DB password, injected from a secret manager (never hardcoded)."
  sensitive   = true
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "Private CIDRs (e.g. VPC/app subnets) permitted to reach the DB."
  default     = []
}

resource "aws_db_instance" "duopoly" {
  identifier              = "duopoly-${var.environment}"
  engine                  = "postgres"
  instance_class          = "db.r6g.large"
  allocated_storage       = 200
  publicly_accessible     = false
  backup_retention_period = 14
  skip_final_snapshot     = false
  final_snapshot_identifier = "duopoly-${var.environment}-final"
  deletion_protection     = true
  storage_encrypted       = true
  username                = "duopoly"
  password                = var.db_password
}


