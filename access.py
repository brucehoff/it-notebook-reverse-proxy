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
from datetime import datetime

AMZN_OIDC_HEADER_NAME = 'x-amzn-oidc-data'
AMZN_ACCESS_TOKEN = 'x-amzn-oidc-accesstoken'

def headerparserhandler(req):
  start_time = datetime.now()
  req.log_error(f"Entering handler interpreter: {req.interpreter}")

  try:
    if not AMZN_OIDC_HEADER_NAME in req.headers_in:
        raise RuntimeError(f"Request lacks {AMZN_OIDC_HEADER_NAME} header.")
    jwt_str = req.headers_in[AMZN_OIDC_HEADER_NAME] # proxy.conf ensures this header exists
    payload = access_helpers.jwt_payload(jwt_str, req)
    req.log_error(f"userid: {payload['userid']}")

    if payload['userid'] == access_helpers.approved_user() and payload['exp'] > time.time():
      access_token = req.headers_in[AMZN_ACCESS_TOKEN]
      access_helpers.store_to_ssm(access_token)
      kh=access_helpers.get_aws_elb_public_key_thread_unsafe.cache_info().hits
      km=access_helpers.get_aws_elb_public_key_thread_unsafe.cache_info().misses
      uh=access_helpers.approved_user_thread_unsafe.cache_info().hits
      um=access_helpers.approved_user_thread_unsafe.cache_info().misses
      sh=access_helpers.store_to_ssm_thread_unsafe.cache_info().hits
      sm=access_helpers.store_to_ssm_thread_unsafe.cache_info().misses

      req.log_error(f"Elapsed time: {datetime.now()-start_time} cache hits: {kh},{uh},{sh}, cache misses: {km},{um},{sm}")
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
