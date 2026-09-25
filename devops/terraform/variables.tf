variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}
variable "environment" {
  type    = string
  default = "production"
}
variable "project_name" {
  type    = string
  default = "vstep"
}
variable "frontend_bucket_name" {
  description = "Optional globally unique S3 bucket name; defaults to project/environment/account/region."
  type        = string
  default     = ""
}
variable "domain_name" {
  description = "Optional custom frontend hostname, e.g. app.example.com."
  type        = string
  default     = ""
}
variable "enable_custom_domain" {
  type    = bool
  default = false
}
variable "route53_zone_id" {
  description = "Optional hosted zone; permits automatic certificate DNS validation."
  type        = string
  default     = ""
}
variable "create_route53_record" {
  description = "Create an alias to CloudFront in the supplied hosted zone."
  type        = bool
  default     = false
}
variable "acm_certificate_arn" {
  description = "Optional already validated ACM certificate ARN in us-east-1."
  type        = string
  default     = ""
}
variable "cloudfront_price_class" {
  type    = string
  default = "PriceClass_100"
  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "Use PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}
variable "enable_cloudfront_logging" {
  type    = bool
  default = false
}
variable "tags" {
  type    = map(string)
  default = {}
}
