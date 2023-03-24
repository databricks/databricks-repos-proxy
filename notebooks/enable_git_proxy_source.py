# Databricks notebook source
# MAGIC %md
# MAGIC # Enable Git Proxy for private Git server connectivity in Repos

# COMMAND ----------

# MAGIC %md
# MAGIC ### Overview
# MAGIC This private preview feature is available on AWS and Azure.
# MAGIC 
# MAGIC **Note**: an *admin* must run this notebook to enable the feature.
# MAGIC 
# MAGIC "Run all" this notebook to set up a cluster that proxies requests to your private Git server. Running this notebook does the following things:
# MAGIC 
# MAGIC 0. Writes a shell script to DBFS (`dbfs:/databricks/db_repos_proxy/db_repos_proxy_init.sh`) that is used as a [cluster-scoped init script](https://docs.databricks.com/clusters/init-scripts.html#example-cluster-scoped-init-scripts).
# MAGIC 0. Creates a [single node cluster](https://docs.databricks.com/clusters/single-node.html) named `dp_git_proxy` that runs the init script on start-up. **Important**: all users in the workspace will be granted "attach to" permissions to the cluster.
# MAGIC 0. Enables a feature flag that controls whether Git requests in Repos are proxied via the cluster.
# MAGIC 
# MAGIC You may need to wait several minutes after running this notebook for the cluster to reach a "RUNNING" state. It can also take up to 30 minutes for the feature flag configuration to take effect.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Cluster Init Script to DBFS

# COMMAND ----------

db_repos_proxy_init = """
#!/bin/bash
set -x

#--------------------------------------------------
# Install Python
mkdir /databricks/db_repos_proxy
cat >  /databricks/db_repos_proxy/db_repos_proxy.py <<EOF
import json
import logging
import os
import tempfile
from distutils.util import strtobool
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import urllib3
from urllib3 import PoolManager
from urllib3.request import RequestMethods


# Configuration
class ProxyConfig:
    VERSION = "0.0.18"
    PORT = os.environ.get("PROXY_PORT", 8000)
    LOG_FILE_PATH = os.environ.get(
        "LOG_FILE_PATH", tempfile.NamedTemporaryFile(delete=False).name
    )
    ENABLE_SSL_VERIFICATION = bool(
        strtobool(os.environ.get("ENABLE_SSL_VERIFICATION", "True"))
    )
    ENABLE_LOGGING = bool(strtobool(os.environ.get("ENABLE_DB_REPOS_PROXY", "False")))
    CA_CERT_PATH = os.environ.get("CA_CERT_PATH", "")


# Make LOG_FILE_PATH directory if it doesn't exist
Path(ProxyConfig.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler(ProxyConfig.LOG_FILE_PATH),
        logging.StreamHandler(),
    ],
)


# Internal Utils
def log_message(message):
    logger.info(f"Version: {ProxyConfig.VERSION} {message}")


def log_headers(message: str = "", headers: dict = {}):
    _HEADER_DENY_LIST = set("authorizations")
    header_strs = []
    for k, v in headers.items():
        if k.lower() not in _HEADER_DENY_LIST:
            header_strs.append(f"{k}: {v}")
    header_str = " ".join(header_strs)
    logger.info(
        f"Version: {ProxyConfig.VERSION} Message: {message} Headers: {header_str}",
    )


# Proxy Utils
def set_headers(headers: dict, handler: BaseHTTPRequestHandler):
    for k, v in headers.items():
        handler.send_header(k, v)
    handler.end_headers()


def set_status_code(code: int, handler: BaseHTTPRequestHandler):
    handler.send_response(code)


def set_json_body(data: dict, handler: BaseHTTPRequestHandler):
    handler.wfile.write(json.dumps(data).encode())


def set_binary_body(data: bin, handler: BaseHTTPRequestHandler):
    handler.wfile.write(data)


# Databricks Header Logic

# Disable chunking
def disable_chunking_headers(headers):
    for k, v in headers.items():
        if k.lower() == "transfer-encoding":
            headers[k] = "identity"
        if k.lower() == "connection":
            headers[k] = "close"
    return headers


def copy_request_headers(headers, allowed_list=[]):
    lowercase_allowed_list = [x.lower() for x in allowed_list]
    copied_headers = {}
    for header_key, header_value in headers.items():
        if header_key.lower() in lowercase_allowed_list:
            copied_headers[header_key] = header_value
    return disable_chunking_headers(copied_headers)


def copy_response_headers(headers):
    copied_headers = {}
    for header_key, header_value in headers.items():
        copied_headers[header_key] = header_value
    return disable_chunking_headers(copied_headers)


DB_VERSION_HEADER_KEY = "X-Databricks-Proxy-Server-Version"
DB_FORWARD_HEADER_PREFIX = "x-databricks-forward-header-"
DB_FORWARD_HEADER_KEYS = "x-databricks-allowed-headers"

DELIMITER = ","


def copy_header_proxy_for_destination(headers):
    allowed_header_keys = []
    if DB_FORWARD_HEADER_KEYS in headers:
        allowed_header_value = headers[DB_FORWARD_HEADER_KEYS]
        for allowed_header_key in allowed_header_value.split(DELIMITER):
            allowed_header_keys.append(allowed_header_key)
    response_headers = copy_request_headers(headers, allowed_list=allowed_header_keys)

    new_headers = {}
    for header_key in headers.keys():
        if header_key.lower().startswith(DB_FORWARD_HEADER_PREFIX):
            new_header_key = header_key[len(DB_FORWARD_HEADER_PREFIX):]
            if len(new_header_key):
                new_headers[new_header_key] = headers[header_key]

    # Forward headers always supersede strip headers
    response_headers.update(new_headers)

    for org_key in headers.keys():
        if org_key not in response_headers:
            log_message("Stripped header: {}".format(org_key))
    return response_headers


# Forward response from destination to control plane
def forward_proxy_response(handler: BaseHTTPRequestHandler, response: RequestMethods):
    set_status_code(code=response.status, handler=handler)
    response_headers = copy_response_headers(response.headers)
    response_headers[DB_VERSION_HEADER_KEY] = ProxyConfig.VERSION
    set_headers(headers=response_headers, handler=handler)
    log_headers(message="Forward headers", headers=handler.headers)
    set_binary_body(data=response.data, handler=handler)


# Handlers

HEALTH_PATH = "/databricks/health"


def do_health(handler: BaseHTTPRequestHandler):
    set_status_code(200, handler)
    headers = {
        "Content-type": "application/json",
    }
    set_headers(headers=headers, handler=handler)
    data = {
        "status": "ok",
        "version": ProxyConfig.VERSION,
    }
    set_json_body(data=data, handler=handler)


def get_path_to_handler():
    path_to_handler = {
        HEALTH_PATH: do_health,
    }
    return path_to_handler


def get_route_handler(path: str, path_to_handler: dict):
    for route, handler in path_to_handler.items():
        if path.startswith(route):
            return handler
    return None


def do_proxy_get(handler: BaseHTTPRequestHandler, pool_manager: PoolManager):
    request_headers = copy_header_proxy_for_destination(headers=handler.headers)
    # Proxy to Destination
    log_headers(
        message=f"Outgoing GET {handler.destination_url} headers",
        headers=request_headers,
    )
    response = pool_manager.request(
        method="GET",
        url=handler.destination_url,
        headers=request_headers,
        decode_content=False,
    )

    # Proxy to Control Plane
    forward_proxy_response(handler=handler, response=response)


def do_proxy_post(handler: BaseHTTPRequestHandler, pool_manager: PoolManager):
    content_len = int(handler.headers.get("Content-Length", 0))
    post_body = handler.rfile.read(content_len)
    request_headers = copy_header_proxy_for_destination(headers=handler.headers)

    log_headers(
        message=f"Outgoing POST {handler.destination_url} headers",
        headers=request_headers,
    )
    response = pool_manager.request(
        method="POST",
        url=handler.destination_url,
        headers=request_headers,
        body=post_body,
        decode_content=False,
    )

    # Proxy to Control Plane
    forward_proxy_response(handler=handler, response=response)


def get_pool_manager():
    _pool_manager_config = {}
    if ProxyConfig.ENABLE_SSL_VERIFICATION is False:
        _pool_manager_config["cert_reqs"] = "CERT_NONE"
    elif ProxyConfig.CA_CERT_PATH:
        _pool_manager_config["ca_certs"] = ProxyConfig.CA_CERT_PATH
    return urllib3.PoolManager(**_pool_manager_config)


http = get_pool_manager()


class ProxyRequestHandler(BaseHTTPRequestHandler):
    @property
    def destination_url(self):
        return "https:/{}".format(self.path)

    def do_GET(self):
        log_message(f"do_GET: {self.destination_url}")
        log_headers(message="Incoming GET headers", headers=self.headers)
        matched_handler = get_route_handler(
            path=self.path,
            path_to_handler=get_path_to_handler(),
        )
        if matched_handler:
            return matched_handler(self)
        do_proxy_get(handler=self, pool_manager=http)

    def do_POST(self):
        log_message(f"do_POST: {self.destination_url}")
        log_headers(message="Incoming POST headers", headers=self.headers)
        do_proxy_post(handler=self, pool_manager=http)

    def do_HEAD(self):
        log_message(f"do_HEAD: {self.destination_url}")
        raise Exception(f"HEAD not supported {self.destination_url}")


def main():
    server_address = ("", ProxyConfig.PORT)
    log_message(
        f"Data-plane proxy server version {ProxyConfig.VERSION} binding to {server_address} ..."
    )
    log_message(f"ProxyConfig {ProxyConfig.__dict__}")
    httpd = HTTPServer(server_address, ProxyRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
EOF
#--------------------------------------------------
# Setup Systemd
cat > /etc/systemd/system/db_repos_proxy.service <<EOF
[Service]
Type=simple
Environment=ENABLE_SSL_VERIFICATION=true CA_CERT_PATH=''
ExecStart=/databricks/python3/bin/python3 -u /databricks/db_repos_proxy/db_repos_proxy.py
StandardInput=null
StandardOutput=file:/databricks/db_repos_proxy/daemon.log
StandardError=file:/databricks/db_repos_proxy/daemon.log
Restart=always
RestartSec=1

[Unit]
Description=Git Proxy Service

[Install]
WantedBy=multi-user.target
EOF
#--------------------------------------------------

systemctl daemon-reload
systemctl enable db_repos_proxy.service
systemctl start db_repos_proxy.service
"""  # db_repos_proxy_init_end

location = "/databricks/db_repos_proxy/db_repos_proxy_init.sh"
dbutils.fs.mkdirs("dbfs:/databricks/db_repos_proxy/")
dbutils.fs.put(location, db_repos_proxy_init, True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create the proxy cluster

# COMMAND ----------

dbutils.widgets.text("cluster-name", "", "Git Proxy Cluster Name")

# COMMAND ----------

import requests

admin_token = (
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
)
databricks_instance = (
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
)

headers = {"Authorization": f"Bearer {admin_token}"}

# Clusters
CLUSTERS_LIST_ENDPOINT = "/api/2.0/clusters/list"
CLUSTERS_CREATE_ENDPOINT = "/api/2.0/clusters/create"
CLUSTERS_LIST_NODE_TYPES_ENDPOINT = "/api/2.0/clusters/list-node-types"

# Permissions
UPDATE_PERMISSIONS_ENDPOINT = "/api/2.0/permissions/clusters"

# Workspace Conf
WORKSPACE_CONF_ENDPOINT = "/api/2.0/workspace-conf"

# get name to use for cluster
cluster_name = "dp_git_proxy"  # default name
widget_value = dbutils.widgets.get("cluster-name")
workspace_conf_value = requests.get(
    databricks_instance + WORKSPACE_CONF_ENDPOINT + "?keys=gitProxyClusterName",
    headers=headers,
).json()["gitProxyClusterName"]
print(f"widget value: {widget_value}")
print(f"workspace conf value: {workspace_conf_value}")

if widget_value:
    cluster_name = widget_value
elif workspace_conf_value:
    cluster_name = workspace_conf_value
print(f"Using cluster name {cluster_name}")

# COMMAND ----------

create_cluster_data = {
    "cluster_name": cluster_name,
    "spark_version": "12.2.x-scala2.12",
    "num_workers": 0,
    "autotermination_minutes": 0,
    "spark_conf": {
        "spark.databricks.cluster.profile": "singleNode",
        "spark.master": "local[*]",
    },
    "custom_tags": {"ResourceClass": "SingleNode"},
    "init_scripts": {
        "dbfs": {
            "destination": "dbfs:/databricks/db_repos_proxy/db_repos_proxy_init.sh"
        }
    },
}
# get list of node types to determine whether this workspace is on AWS or Azure
clusters_node_types = requests.get(
    databricks_instance + CLUSTERS_LIST_NODE_TYPES_ENDPOINT, headers=headers
).json()["node_types"]
node_type_ids = [type["node_type_id"] for type in clusters_node_types]
aws_node_type_id = "m5.large"
azure_node_type_id = "Standard_DS3_v2"
if aws_node_type_id in node_type_ids:
    create_cluster_data = {
        **create_cluster_data,
        "node_type_id": aws_node_type_id,
        "aws_attributes": {"ebs_volume_count": "1", "ebs_volume_size": "32"},
    }
elif azure_node_type_id in node_type_ids:
    create_cluster_data = {**create_cluster_data, "node_type_id": azure_node_type_id}
else:
    raise ValueError(
        f"Node types {aws_node_type_id} or {azure_node_type_id} do not exist. Make sure you are on AWS or Azure, or contact support."
    )

# Note: this only returns up to 100 terminated all-purpose clusters in the past 30 days
clusters_list_response = requests.get(
    databricks_instance + CLUSTERS_LIST_ENDPOINT, headers=headers
).json()
clusters_list = clusters_list_response["clusters"]
clusters_names = [
    cluster["cluster_name"] for cluster in clusters_list_response["clusters"]
]
print(f"List of existing clusters: {clusters_names}")

if cluster_name in clusters_names:
    raise ValueError(
        f"Cluster called {cluster_name} already exists. Please delete this cluster and re-run this notebook"
    )
else:
    # Create a new cluster named cluster_name that will proxy requests to the private Git server
    print(f"Create cluster POST request data: {create_cluster_data}")
    clusters_create_response = requests.post(
        databricks_instance + CLUSTERS_CREATE_ENDPOINT,
        headers=headers,
        json=create_cluster_data,
    ).json()
    print(f"Create cluster response: {clusters_create_response}")
    cluster_id = clusters_create_response["cluster_id"]
    print(f"Created new cluster with id {cluster_id}")
    update_permissions_data = {
        "access_control_list": [
            {"group_name": "users", "permission_level": "CAN_ATTACH_TO"}
        ]
    }
    update_permissions_response = requests.patch(
        databricks_instance + UPDATE_PERMISSIONS_ENDPOINT + f"/{cluster_id}",
        headers=headers,
        json=update_permissions_data,
    ).json()
    print(f"Update permissions response: {update_permissions_response}")
    print(f"Gave all users ATTACH TO permissions to cluster {cluster_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Flip the feature flag!
# MAGIC This flips the feature flag to route Git requests to the cluster. The change should take into effect within an hour.

# COMMAND ----------

patch_enable_git_proxy_data = {"enableGitProxy": "true"}
patch_git_proxy_cluster_name_data = {"gitProxyClusterName": cluster_name}
requests.patch(
    databricks_instance + WORKSPACE_CONF_ENDPOINT,
    headers=headers,
    json=patch_enable_git_proxy_data,
)
requests.patch(
    databricks_instance + WORKSPACE_CONF_ENDPOINT,
    headers=headers,
    json=patch_git_proxy_cluster_name_data,
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Check that flag has been set
# MAGIC If the command below returns with `{"enableGitProxy":"true"}`, you should be all set. Also, if you configured a custom cluster name using the widget, check that the cluster name in the response matches the name you specified.

# COMMAND ----------

get_flag_response = requests.get(
    databricks_instance + WORKSPACE_CONF_ENDPOINT + "?keys=enableGitProxy",
    headers=headers,
).json()
get_cluster_name_response = requests.get(
    databricks_instance + WORKSPACE_CONF_ENDPOINT + "?keys=gitProxyClusterName",
    headers=headers,
).json()
print(f"Get enableGitProxy response: {get_flag_response}")
print(f"Get gitProxyClusterName response: {get_cluster_name_response}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation steps
# MAGIC Attach this notebook to the **Git proxy cluster** that was just created and follow the instructions below.

# COMMAND ----------

# MAGIC %sh
# MAGIC systemctl status db_repos_proxy.service
# MAGIC journalctl -u db_repos_proxy.service
# MAGIC cat /databricks/db_repos_proxy/daemon.log

# COMMAND ----------

# MAGIC %sh
# MAGIC python --version

# COMMAND ----------

# MAGIC %sh
# MAGIC curl localhost:8000/databricks/health

# COMMAND ----------


