#!/usr/bin/env python3

##
## Expects these environment variables:
## SYNAPSE_TOKEN_AWS_SSM_PARAMETER_NAME
## KMS_KEY_ALIAS
## AWS_REGION
## EC2_INSTANCE_ID
##

import time
import access_helpers
from mod_python import apache

AMZN_OIDC_HEADER_NAME = 'x-amzn-oidc-data'
AMZN_ACCESS_TOKEN = 'x-amzn-oidc-accesstoken'

def headerparserhandler(req):
  req.log_error("Entering handler")

  try:
    if not AMZN_OIDC_HEADER_NAME in req.headers_in:
        raise RuntimeError(f"Request lacks {AMZN_OIDC_HEADER_NAME} header.")
    jwt_str = req.headers_in[AMZN_OIDC_HEADER_NAME] # proxy.conf ensures this header exists
    payload = access_helpers.jwt_payload(jwt_str, req)
    req.log_error(f"userid: {payload['userid']}")

    if payload['userid'] == access_helpers.approved_user() and payload['exp'] > time.time():
      access_token = req.headers_in[AMZN_ACCESS_TOKEN]
      access_helpers.store_to_ssm(access_token)
      req.log_error("Saved access token to ssm.")
      return apache.OK
    else:
      # the userid claim does not match the userid tag or the JWT is expired
      return apache.HTTP_FORBIDDEN
  except Exception as e:
    # if the JWT is missing or payload is invalid
    if len(e.args)>0:
      req.content_type = "text/plain"
      req.write(f"{e.args[0]}\n")
      req.status = apache.HTTP_UNAUTHORIZED
    return apache.DONE
