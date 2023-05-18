# Git Proxy Update Guide
## Background
This update is required to maintain compatibility with various Git providers and support new git features such as sparse checkout and rebase merge. We have deprecated versions below v0.0.20 as of Aug 31, 2023, and they no longer function after this date. It's crucial to apply this update to continue using the git proxy and take advantage of the new features.

## What's Changed
Here are the Git Proxy improvements in v0.0.20:

1. Versioning: Added script versioning for user notification of future updates.
2. Business Logic Migration: Shifted business logic to the control plane, enabling server-side proxy logic upgrades.
3. Compression Fix: Corrected gzip compression logic.
4. Nginx 1.23 Compatibility: Ensured compatibility with nginx 1.23.
5. End-to-End Testing: Introduced comprehensive testing against major Git providers (GitLab, Azure DevOps, Bitbucket, GitHub).
6. Improved Logging & Health Endpoint: Added logging and health endpoint for simplified troubleshooting.

## Prerequisites
Choose a proxy cluster name, for example, git_proxy_2023_05_18. This must be different from your current proxy cluster name.

Read the proxy documentation at documentations/[Git Server Proxy for Repos Documentation v0.0.20.pdf].

## Update Steps
Upload the new proxy script enable_git_proxy_jupyter_v0.0.20.ipynb in this repository to your workspace.

Follow the notebook instructions to set up the new proxy cluster.

Wait for approximately **30 minutes** for the git traffic to transition from the old cluster to the new cluster. You can use the proxy log to verify the update process. Refer to the proxy documentation for details on how to access the log.

Verify that there is no traffic going to the old proxy cluster.

Once you have confirmed that there is no traffic on the old proxy cluster, you can safely turn it off.

By following these steps, you should have successfully updated your git proxy to a new cluster.

## Support
If you have any questions or encounter any issues during the update process, please contact your solution architect for assistance. They will be able to guide you through the process and help resolve any issues that may arise.