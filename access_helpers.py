#!/usr/bin/env python3

##
## Expects these environment variables:
## SYNAPSE_TOKEN_AWS_SSM_PARAMETER_NAME
## KMS_KEY_ALIAS
## AWS_REGION
## EC2_INSTANCE_ID
##

import jwt
import requests
import base64
import json
import boto3
import cachetools.func
import os

SSM_PARAMETER_NAME = os.environ.get('SYNAPSE_TOKEN_AWS_SSM_PARAMETER_NAME')
SSM_KMS_KEY_ALIAS = os.environ.get('KMS_KEY_ALIAS')
AWS_REGION = os.environ.get('AWS_REGION')
EC2_INSTANCE_ID = os.environ.get('EC2_INSTANCE_ID')
CACHE_TTL_SECONDS = 3600 # one hour

def get_approved_user_from_ec2_instance_tags(tags):
  for tag in tags:
    if tag["Key"] == 'Protected/AccessApprovedCaller':
      approved_caller = tag["Value"]

  return approved_caller.split(':')[1] #return userid portion of tag



@cachetools.func.ttl_cache(maxsize=1, ttl=CACHE_TTL_SECONDS)
def approved_user():
  ec2 = boto3.resource('ec2',AWS_REGION)
  vm = ec2.Instance(EC2_INSTANCE_ID)
  return get_approved_user_from_ec2_instance_tags(vm.tags)

# taking advantage of cache to avoid re-putting the same access token to
# SSM Parameter Store.
@cachetools.func.ttl_cache(maxsize=1, ttl=CACHE_TTL_SECONDS)
def store_to_ssm(access_token):
  if not (SSM_PARAMETER_NAME):
    # just exit early if the parameter name to store in SSM is not found
    return
  ssm_client = boto3.client('ssm', AWS_REGION)
  kms_client = boto3.client('kms', AWS_REGION)
  key_id = kms_client.describe_key(KeyId=SSM_KMS_KEY_ALIAS)['KeyMetadata']['KeyId']

  ssm_client.put_parameter(
    Name=SSM_PARAMETER_NAME,
    Type='SecureString',
    Value=access_token,
    KeyId=key_id,
    Overwrite=True
  )

def jwt_payload(encoded_jwt, req=None, validate_time_leeway_seconds=0):
  # The x-amzn-oid-data header is a base64-encoded JWT signed by the ALB
  # validating the signature of the JWT means the payload is authentic
  # per http://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html
  # Step 1: Get the key id from JWT headers (the kid field)
  jwt_headers = encoded_jwt.split('.')[0]

  decoded_jwt_headers = base64.b64decode(jwt_headers).decode("utf-8")
  decoded_json = json.loads(decoded_jwt_headers)
  kid = decoded_json['kid']
  if req is not None:
    req.log_error(f"kid: {kid}")

  # Step 2: Get the public key from regional endpoint
  pub_key = get_aws_elb_public_key(kid)

  # Step 3: Get the payload
  return jwt.decode(encoded_jwt, pub_key, leeway=validate_time_leeway_seconds, algorithms=['ES256'])

@cachetools.func.ttl_cache(maxsize=1, ttl=CACHE_TTL_SECONDS)
def get_aws_elb_public_key(key_id):
  url = f'https://public-keys.auth.elb.{AWS_REGION}.amazonaws.com/{key_id}'
  return requests.get(url).text
