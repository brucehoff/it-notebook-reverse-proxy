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
import base64, json

AMZN_OIDC_HEADER_NAME = 'x-amzn-oidc-data'
AMZN_ACCESS_TOKEN = 'x-amzn-oidc-accesstoken'


# Get the Base64 decoded payload of a JWT
# Note: This is for debugging.
def get_payload_from_jwt(encoded_jwt):
    base64_encoded_payload = encoded_jwt.split('.')[1]
    payload = json.loads(base64.b64decode(f"{base64_encoded_payload}=="))
    try:
        expired_at_epoch = payload['exp']
        expired_at_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expired_at_epoch))
    except:
        expired_at_readable=na
    return f"exp: {expired_at_readable} payload: {payload}"


def headerparserhandler(req):
  start_time = datetime.now()
  req.log_error(f"Entering handler interpreter: {req.interpreter}")

  try:
    if not AMZN_OIDC_HEADER_NAME in req.headers_in:
      raise RuntimeError(f"Request lacks {AMZN_OIDC_HEADER_NAME} header.")
    jwt_str = req.headers_in[AMZN_OIDC_HEADER_NAME]
    payload = access_helpers.jwt_payload(jwt_str, req)
    req.log_error(f"userid: {payload['userid']}")

    if payload['userid'] != access_helpers.approved_user():
      # the userid claim does not match the userid tag
      return apache.HTTP_FORBIDDEN

    if payload['exp'] < time.time():
      # trigger reauthentication
      return apache.HTTP_UNAUTHORIZED

    access_token = req.headers_in[AMZN_ACCESS_TOKEN]

    # log the payloads of both jwts
    req.log_error(f"{AMZN_OIDC_HEADER_NAME}: {get_payload_from_jwt(jwt_str)}")
    req.log_error(f"{AMZN_ACCESS_TOKEN}: {get_payload_from_jwt(access_token)}")

    # if the access token is not valid then trigger reauthentication
    try:
      access_helpers.validate_access_token(access_token)
    except:
      return apache.HTTP_UNAUTHORIZED

    access_helpers.store_to_ssm(access_token)

    kh=access_helpers.get_aws_elb_public_key_thread_unsafe.cache_info().hits
    km=access_helpers.get_aws_elb_public_key_thread_unsafe.cache_info().misses
    uh=access_helpers.approved_user_thread_unsafe.cache_info().hits
    um=access_helpers.approved_user_thread_unsafe.cache_info().misses
    sh=access_helpers.store_to_ssm_thread_unsafe.cache_info().hits
    sm=access_helpers.store_to_ssm_thread_unsafe.cache_info().misses

    req.log_error(f"Elapsed time: {datetime.now()-start_time} cache hits: {kh},{uh},{sh}, cache misses: {km},{um},{sm}")
    return apache.OK
  except Exception as e:
    # Something's gone wrong.  Try to return a useful message.
    if len(e.args)>0:
      req.content_type = "text/plain"
      req.write(f"{e.args[0]}\n")
      req.status = apache.HTTP_UNAUTHORIZED
    return apache.DONE
