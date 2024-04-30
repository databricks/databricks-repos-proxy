# PrivateLink to Git Proxy Migration Guide


## Background
This guide assists in migrating private Git-enabled workspaces from PrivateLink (PL) to Git Proxy. Git Proxy, available as a General Availability (GA) solution since Q1 2024, is now the recommended method for private Git connectivity on Databricks. Consequently, we are phasing out PrivateLink, which is another private Git solution currently in private preview and will not be further developed.


## Migration Timeline
Immediate Action (Effective from 06/01/2024): No new PL connection will be created.

Within 90 Days (by 09/01/2024): No additional workspaces will be allowed on existing PL connection.




## Prerequisites
1. Have workspace admin permission
2. Read the proxy [documentation](https://github.com/databricks/databricks-repos-proxy/blob/main/documentations/Git%20Server%20Proxy%20for%20Repos%20Documentation.pdf)




## Migration Steps
1. Upload the new proxy enablement [notebook](https://github.com/databricks/databricks-repos-proxy/blob/main/enable_git_proxy_jupyter.ipynb)
in this repository to your workspace.




https://github.com/databricks/databricks-repos-proxy/assets/5799524/ec9fbc2d-18c2-45ef-a5e8-5d488492053d




2. Run the enablement notebook, by clicking the "Run all" button.


3. Wait for approximately **5 minutes** for the cluster to start, you can check its status in "Compute", the cluster name is "Repos Git Proxy".




https://github.com/databricks/databricks-repos-proxy/assets/5799524/e613a64b-29ab-4038-9839-b8d1da932163


4. Verify Proxy Traffic: Confirm that traffic is being correctly routed through the Git Proxy cluster by reviewing the proxy logs located at /databricks/git-proxy/git-proxy.log and running the debug notebook.


5. Check AWS Load Balancer Traffic: Ensure that no traffic is being directed to your AWS load balancer previously configured for PrivateLink.


6. Remove PrivateLink Connection: After confirming successful redirection of all traffic to the Git Proxy cluster and allowing a few weeks for stabilization, you may safely remove the PrivateLink connection.


## [Optional] Remove Git Proxy
To remove Git Proxy, run the disable_git_proxy_jupyter.ipynb notebook and then delete the Git proxy cluster.


## Support


Use [debug notebook](https://github.com/databricks/databricks-repos-proxy/blob/main/debug_git_proxy_jupyter.ipynb) to troubleshoot the issue.
If you have any questions or encounter any issues during the update process, please email help@databricks.com with the debug notebook output.
