# Git Proxy Migration Guide
## Background
This migration is necessary to maintain compatibility with various Git providers and support new git features such as sparse checkout and rebase merge. We will deprecate versions below v0.0.20 by Aug 31, 2023, and they will no longer function after this date. It's crucial to perform this migration to continue using the git proxy and take advantage of the new features.

## Prerequisites
Choose a proxy cluster name, for example, `git_proxy_2022_05_11`. This must be different from your current proxy cluster name.

Read the proxy documentation at `documentations/[Git Server Proxy for Repos Documentation v0.0.20.pdf`.

## Migration Steps
Upload the new proxy script `enable_git_proxy_jupyter_v0.0.20.ipynb` in this repository to your workspace.

Follow the notebook instructions to set up the new proxy cluster.

Wait for approximately 30 minutes for the git traffic to migrate from the old cluster to the new cluster. You can use the proxy log to verify the migration process. Refer to the proxy documentation for details on how to access the log.

Verify that there is no traffic going to the old proxy cluster.

Once you have confirmed that there is no traffic on the old proxy cluster, you can safely turn it off.

By following these steps, you should have successfully migrated your git proxy to a new cluster.

## Support
If you have any questions or encounter any issues during the migration process, please contact your solution architect for assistance. They will be able to guide you through the process and help resolve any issues that may arise.
