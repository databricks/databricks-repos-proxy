# v0.0.20 has been deprecated 
Please use [https://github.com/databricks/databricks-repos-proxy/tree/v0.1.0
](https://github.com/databricks/databricks-repos-proxy/blob/v0.1.0/READ_ME_MIGRATION_GUIDE.md)


~~# Git Proxy Update Guide~~
~~## Background~~
~~This update is required to maintain compatibility with various Git providers and support new git features such as sparse checkout and rebase merge. We have deprecated versions below v0.0.20 as of Aug 31, 2023, and they no longer function after this date. It's crucial to apply this update to continue using the git proxy and take advantage of the new features. Also, there are no architecture changes in this update, and as a result, no additional security review is required. This instruction is specifically intended for users who already have Git Proxy enabled and are looking to perform a zero downtime migration.~~

~~## What's Changed~~
~~Here are the Git Proxy improvements in v0.0.20:~~

~~1. Versioning: Added script versioning for user notification of future updates.~~
~~2. Business Logic Migration: Shifted business logic to the control plane, enabling server-side proxy logic upgrades.~~
~~3. Compression Fix: Corrected gzip compression logic.~~
~~4. Nginx 1.23 Compatibility: Ensured compatibility with nginx 1.23.~~
~~5. End-to-End Testing: Introduced comprehensive testing against major Git providers (GitLab, Azure DevOps, Bitbucket, GitHub).~~
~~6. Improved Logging & Health Endpoint: Added logging and health endpoint for simplified troubleshooting.~~

~~## Prerequisites~~
~~Read the proxy documentation at [documentations/[Git Server Proxy for Repos Documentation v0.0.20.pdf]](https://github.com/databricks/databricks-repos-proxy/blob/v0.0.20/documentations/Git%20Server%20Proxy%20for%20Repos%20Documentation%20v0.0.20.pdf). *IMPORTANT* If you have self signed SSL please read "Secure connection could not be established because of ssl problems". In such cases, modifications to the enablement script will be necessary.~~
~~1. Have workspace admin permission~~
~~2. Choose a new proxy cluster name, for example, git_proxy_2023_05_18. This must be different from your current proxy cluster name.~~
~~3. Read the proxy documentation at documentations/[Git Server Proxy for Repos Documentation v0.0.20.pdf].~~

~~## Update Steps~~
~~1. Upload the new proxy script [enable_git_proxy_jupyter_v0.0.20.ipynb](https://github.com/databricks/databricks-repos-proxy/blob/v0.0.20/enable_git_proxy_jupyter_v0.0.20.ipynb) in this repository to your workspace.~~

~~2. Run the enablement notebook. **Please make sure to thoroughly read the documentation provided before proceeding to set up the new proxy cluster. It is highly recommended that you carefully review and try to comprehend the content of each notebook cell before executing any commands. It's important to note that as part of the enablement process, you will need to switch the connected cluster.**~~

~~3. Wait for approximately **30 minutes** for the git traffic to transition from the old cluster to the new cluster. You can use the proxy log to verify the update process. Refer to the proxy documentation for details on how to access the log.~~

~~4. Verify that there is no traffic going to the old proxy cluster. (refer to the documentation)~~

~~5. Once you have confirmed that there is no traffic on the old proxy cluster, you can safely turn it off.~~

~~By following these steps, you should have successfully updated your git proxy to a new cluster.~~

~~## Support~~
~~If you have any questions or encounter any issues during the update process, please email help@databricks.com.~~
