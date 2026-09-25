output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}
output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}
output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.frontend.domain_name
}
output "frontend_url" {
  value = var.enable_custom_domain ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
output "custom_domain" {
  value = var.enable_custom_domain ? var.domain_name : null
}
output "acm_validation_records" {
  value = var.enable_custom_domain && var.acm_certificate_arn == "" ? [for dvo in aws_acm_certificate.frontend[0].domain_validation_options : {
    name  = dvo.resource_record_name
    type  = dvo.resource_record_type
    value = dvo.resource_record_value
  }] : []
}
