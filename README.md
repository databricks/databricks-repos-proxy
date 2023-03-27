# [Private Preview] Databricks Proxy Server

[Documentation](https://docs.google.com/document/d/1OiozkdImZfDsH7fQR4ro3o92xSBbKwl8t9CyUUilgiw/edit)

# Usage

###  SSL
By default, the proxy server will require valid SSL certificate. You can disable this by setting the ENABLE_SSL_VERIFICATION environment variable to false.
Or provide custom TLS certificates by setting the CA_CERT_PATH environment variable to the path of the certificate.

# Troubleshooting
Health Endpoint `curl localhost:8000/databricks/health`

Logs `/databricks/db_repos_proxy/daemon.log`

# License
See the LICENSE.txt for more information.