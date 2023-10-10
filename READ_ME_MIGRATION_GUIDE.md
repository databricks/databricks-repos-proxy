# Git Proxy Install & Update Guide
## Background
This update is required to maintain compatibility with various Git providers and support new git features such as sparse checkout and rebase merge. 
**We have deprecated versions below v0.1.0 as of September 30, 2023, and will be no longer be supported after this date.**
It's crucial to apply this update to continue using the git proxy and take advantage of the new features. 
Also, there are no architecture changes in this update, and as a result, no additional security review is required. 
This instruction is specifically intended for users who already have Git Proxy enabled and are looking to perform a zero downtime migration.

## What's Changed
Here are the Git Proxy improvements in v0.1.0:

1. Versioning: Added script versioning for user notification of future updates.
2. Business Logic Migration: Shifted business logic to the control plane, enabling server-side proxy logic upgrades.
3. Compression Fix: Corrected gzip compression logic.
4. Nginx 1.23 Compatibility: Ensured compatibility with nginx 1.23.
5. End-to-End Testing: Introduced comprehensive testing against major Git providers (GitLab, Azure DevOps, Bitbucket, GitHub).
6. Improved Logging & Health Endpoint: Added logging and health endpoint for simplified troubleshooting.
7. **Auto deployment & upgrade: Future Git Proxy script is automatically deployed and upgraded on the cluster.**
8. Allow customizing the settings, like SSL verification, port, with environment variables.

## Prerequisites
1. Have workspace admin permission
2. Read the proxy [documentation v0.1.0](https://github.com/databricks/databricks-repos-proxy/blob/v0.1.0/documentations/Git%20Server%20Proxy%20for%20Repos%20Documentation%20v0.1.0.pdf)

## Update Steps
1. Upload the new proxy script [enable_git_proxy_jupyter_v0.1.0.ipynb](https://github.com/databricks/databricks-repos-proxy/blob/v0.1.0/enable_git_proxy_jupyter_v0.1.0.ipynb) 
in this repository to your workspace.


https://github.com/databricks/databricks-repos-proxy/assets/5799524/ec9fbc2d-18c2-45ef-a5e8-5d488492053d


2. Run the enablement notebook, by clicking the "Run all" button.

3. Wait for approximately **5 minutes** for the cluster to start, you can check its status in "Compute", the cluster name is "Repos Git Proxy". You can find the proxy logs at `/databricks/git-proxy/git-proxy.log`


https://github.com/databricks/databricks-repos-proxy/assets/5799524/e613a64b-29ab-4038-9839-b8d1da932163


4. If you are upgrading from old Git Proxy, verify that there is no traffic going to the old proxy cluster. (refer to the documentation) 
Once you have confirmed that there is no traffic on the old proxy cluster, you can safely turn it off.

By following these steps, you should have successfully updated your git proxy to a new cluster.

## Remove Git Proxy
To remove Git Proxy, run the disable_git_proxy_jupyter.ipynb notebook and then delete the Git proxy cluster.

## Support

Use [debug notebook](https://github.com/databricks/databricks-repos-proxy/blob/v0.1.0/debug_git_proxy_jupyter_v0.1.0.ipynb) to troubleshoot the issue. 
If you have any questions or encounter any issues during the update process, please email help@databricks.com with the debug notebook output.


## FAQ:
1. Do I need to set up the init script previously provided by Databricks for the new git proxy cluster? No, Git proxy v0.1.0 does not require the use of an init script. **Applying the previous init script to Git proxy v0.1.0 will cause Git Proxy to malfunction.**
