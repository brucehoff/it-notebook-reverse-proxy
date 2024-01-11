#!/bin/bash

# Container startup requires the following environment variables:
# EC2_INSTANCE_ID - ID of the EC2 instance on which the container is running ("i-xxxxxxxxxx")
# AWS_REGION - AWS Region in which the EC2 instance is running (e.g., "us-east-1")
# SERVICE_CATALOG_PREFIX - prefix to use for service catalog synapse cred' name in SSM Parameter store
# SSM_PARAMETER_SUFFIX - suffix for the SSM Parameter name
# NOTEBOOK_HOST - name of the host running the notebook, as seen on the Docker network

# Inject EC2_INSTANCE_ID into proxy.conf:
sed -i "s/EC2_INSTANCE_ID/$EC2_INSTANCE_ID/g" /etc/apache2/sites-available/proxy.conf
# Inject remote host name into proxy.conf
sed -i "s/NOTEBOOK_HOST/$NOTEBOOK_HOST/g" /etc/apache2/sites-available/proxy.conf

# access.py needs these environment variables in Apache
echo "export EC2_INSTANCE_ID=$EC2_INSTANCE_ID" >> /etc/apache2/envvars
echo "export AWS_REGION=$AWS_REGION" >> /etc/apache2/envvars

# This script is used to set up environment variables that the Apache reverse proxy will use
# to store Synapse user token into SSM Parameter Store
INSTANCE_ID_KEY="$SERVICE_CATALOG_PREFIX/$EC2_INSTANCE_ID"
SYNAPSE_TOKEN_AWS_SSM_PARAMETER_NAME="/$INSTANCE_ID_KEY/$SSM_PARAMETER_SUFFIX"
KMS_KEY_ALIAS="alias/$INSTANCE_ID_KEY"
# set environment variable for Apache
echo "export SYNAPSE_TOKEN_AWS_SSM_PARAMETER_NAME=$SYNAPSE_TOKEN_AWS_SSM_PARAMETER_NAME" >> /etc/apache2/envvars
echo "export KMS_KEY_ALIAS=$KMS_KEY_ALIAS" >> /etc/apache2/envvars

# Start the first process
apachectl -D FOREGROUND
