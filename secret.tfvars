# copy this file to secrets.tfvars and add your own secrets
# never commit the actual secrets.tfvars file

jenkins_secrets = {
  "AWS_ACCESS_KEY" = "AKIAYZUBFFI2ZC7HU42Q"
  "AWS_SECRET_KEY" = "J0i7TLexAOmRYOKjK+4bekLk5qrEo/2rPNvY6PjR"
}


eks_monitoring_secret = {
  "wp_sql_password" : "admin",
  "grafana_password" : "admin"
}