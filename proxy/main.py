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
    VERSION = "0.0.19"
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
    header_strs = []
    for k, v in headers.items():
        if "authorization" not in k.lower():
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
