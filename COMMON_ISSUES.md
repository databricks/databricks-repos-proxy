# Managed Git Proxy v0.1.0 Troubleshooting Guide

If you encounter issues with Managed Git Proxy, this guide will help you identify and resolve common problems.

## Prerequisite 
- Ensure that you are using the latest Git Proxy v0.1.0 (as of 08/04/2023). For instructions on updating, please refer to https://github.com/databricks/databricks-repos-proxy/blob/v0.1.0/READ_ME_MIGRATION_GUIDE.md for instruction
- Familiarize yourself with the Git Proxy by reading https://github.com/databricks/databricks-repos-proxy/blob/v0.1.0/documentations/Git%20Server%20Proxy%20for%20Repos%20Documentation%20v0.1.0.pdf

## Failure Modes and Solutions

### 1. Control Plane Failed to Connect to Data Plane Cluster

**Possible causes and solutions:**

- **SSL Certificate Misconfiguration**:
  - *Symptom*: `Couldn't connect to server, reason: The requested URL returned error: 502`
  - *Solution*: Verify by turning off SSL verification and see if the clone works. 
  - *TODO*: Provide further instructions or a link to guide users on how to turn off SSL verification.

- **Proxy Cluster Not Running**:
  - *Symptom*: `Couldn't connect to server, reason: The requested URL returned error: 502`
  - *Solution*: Check the cluster page to see if the proxy cluster is running.

- **Feature Flag Misconfiguration**:
  - *Symptom*: `Couldn't connect to server, reason: The requested URL returned error: 502`
  - *Solution*: Rerun the enablement script and try again.

- **Managed Proxy Code Issues**:
  - *Symptom*: `Couldn't connect to server, reason: The requested URL returned error: 502`
  - *Solution*: Attach to the proxy cluster and run the following command to check the logs:
    ```sh
    cat /databricks/git-proxy/git-proxy.log
    ```



### 2. Managed Git Proxy Failed to connect with Private Git Server

**Possible causes and solutions:**

- **Issue with Managed Git Proxy**:
  - *Symptom*: TODO: add examples
  - *Solution*: Attach to the proxy cluster and run the following command to check the logs:
  ```sh
  cat /databricks/git-proxy/git-proxy.log
  ```

- **Internal Git Server Misconfiguration**:
  - *Symptom*: Unable to clone repositories. TODO: add examples
  - *Solution*: Try to clone a public repo. We recommend GitHub's Databricks Repos Proxy. (i.e. https://github.com/databricks/databricks-repos-proxy/tree/v0.1.0) 

  
- **Credentials Misconfiguration**:
  - *Symptom*: Unable to clone repositories. TODO: add examples
  - *Solution*: Try to clone a public repo.




## How to Escalate
If the above solutions don't resolve your issue, please escalate by providing the following information:

Document the output from the troubleshooting steps.
- Provide us with the internal Git URL used.
- Provide us with the time the attempt was made.
- Provide us with the error messages and Git proxy logs.
- (If possible) Give us written permission to access the workspace.



