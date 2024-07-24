# notebook-reverse-proxy
Docker container with Apache reverse proxy for Service Catalog notebook product

This is a component of the Service Catalog notebook product.
The provsioned product sits behind an AWS ALB which authenticates
the user, adds an access token as a header, and forwards the traffic
to the instance, under the URL:

```
https:<host-name>/<ec2-instance-id>
```

It's the job of this reverse proxy to:
- validate the access token;
- make sure the access token is for the user assigned to the EC2 instance;
- store the access token in SSM Parameter Store for later use;
- forward the traffic to the notebook


### To run a Jupyter notebook with this reverse proxy:

```
export EC2_INSTANCE_ID=...
export NOTEBOOK_CONTAINER_NAME=jupyter
export NETWORK_NAME=proxy-net

docker network create --driver bridge ${NETWORK_NAME}

docker run -d -p 443:443 --name reverse-proxy \
--network ${NETWORK_NAME} \
--restart unless-stopped \
-e EC2_INSTANCE_ID=${EC2_INSTANCE_ID} \
-e NOTEBOOK_HOST=${NOTEBOOK_CONTAINER_NAME} \
-e AWS_REGION=us-east-1 \
-e SERVICE_CATALOG_PREFIX=service-catalog/synapse/cred \
-e SSM_PARAMETER_SUFFIX=oidc-accesstoken \
ghcr.io/sage-bionetworks/notebook-reverse-proxy-jupyter:latest

```

Then run the notebook on the same network. For example:

```
# this is just an example user name, though it's the one Service Catalog uses today:
export HOME=/home/ssm-user

# The following should be customized, e.g., with an up-to-date version
export DOCKER_IMAGE=quay.io/jupyter/base-notebook:python-3.11

mkdir $HOME/workdir
chmod 777 $HOME/workdir

docker run -d --name ${NOTEBOOK_CONTAINER_NAME} \
--restart unless-stopped \
-e DOCKER_STACKS_JUPYTER_CMD=notebook \
-v $HOME/workdir:/home/jovyan/workdir \
--network ${NETWORK_NAME} ${DOCKER_IMAGE} \
start-notebook.py --IdentityProvider.token='' --NotebookApp.base_url=/${EC2_INSTANCE_ID} \
--notebook-dir=/home/jovyan/workdir

```

### To run an RStudio notebook with this reverse proxy:


```
export EC2_INSTANCE_ID=...
export NOTEBOOK_CONTAINER_NAME=rstudio
export NETWORK_NAME=proxy-net

docker network create --driver bridge ${NETWORK_NAME}

docker run -d -p 443:443 --name reverse-proxy \
--network ${NETWORK_NAME} \
--restart unless-stopped \
-e EC2_INSTANCE_ID=${EC2_INSTANCE_ID} \
-e NOTEBOOK_HOST=${NOTEBOOK_CONTAINER_NAME} \
-e AWS_REGION=us-east-1 \
-e SERVICE_CATALOG_PREFIX=service-catalog/synapse/cred \
-e SSM_PARAMETER_SUFFIX=oidc-accesstoken \
ghcr.io/sage-bionetworks/notebook-reverse-proxy-rstudio:latest

```

Then run the notebook on the same network. For example:

```
# this is just an example user name, though it's the one Service Catalog uses today:
export HOME=/home/ssm-user

# The following should be customized, e.g., with an up-to-date version
export DOCKER_IMAGE=rocker/rstudio:4.3.2

mkdir $HOME/workdir
chmod 777 $HOME/workdir


docker run -d --name ${NOTEBOOK_CONTAINER_NAME} \
--restart unless-stopped \
--network ${NETWORK_NAME} \
-e DISABLE_AUTH=true \
-v /home/ssm-user/workdir:/home/rstudio \
${DOCKER_IMAGE}

```


## Security

Trivy is run on each built container, to scan for known vulnerabilities.
Containers will not be published to `ghcr.io` if any CRITICAL or HIGH
vulnerabilites are found.  Trivy is also run daily to check for new
vulnerabilities in existing images.  So periodic review of new findings
is needed:  Go to the Security tab in GitHub, select Code Scanning at left,
and then select Branch > Main to check for new findings.  To suppress
findings which are not "true positives", either:

- Enter the CVE in `.trivyignore`, or

- Enter the file to skip while scanning in the `trivy.yml` workflow.

In either case, add a comment to explain why the finding is suppressd.
