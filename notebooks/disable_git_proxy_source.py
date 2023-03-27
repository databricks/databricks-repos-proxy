# Databricks notebook source
# MAGIC %md
# MAGIC ## Disable the feature
# MAGIC **Note you must be an admin to update the feature flag**
# MAGIC
# MAGIC Running the cell below sets the feature flag to false. You should also terminate the Git proxy cluster manually by going to the "Compute" page.

# COMMAND ----------

import requests

admin_token = (
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
)
databricks_instance = (
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
)

headers = {"Authorization": f"Bearer {admin_token}"}
WORKSPACE_CONF_ENDPOINT = "/api/2.0/workspace-conf"
patch_enable_git_proxy_data = {"enableGitProxy": "false"}
patch_response = requests.patch(
    databricks_instance + WORKSPACE_CONF_ENDPOINT,
    headers=headers,
    json=patch_enable_git_proxy_data,
)
print(f"patch_response: {patch_response}, {patch_response.text}")
get_flag_response = requests.get(
    databricks_instance + WORKSPACE_CONF_ENDPOINT + "?keys=enableGitProxy",
    headers=headers,
)
print(
    f"This value of enableGitProxy should be false -- Get enableGitProxy response: {get_flag_response}, {get_flag_response.text}"
)

# COMMAND ----------
