# Tests for access_helpers.py

import jwt
import sys
import access_helpers
from unittest.mock import patch

PUB_KEY="-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEZT30G1CWZUTKLi2G9z6vvb7nFhNb\nNHwGykNYqy9FnTPErnnu9sCKue4or6Z2CAIJNn6DDbyosy2gdi2uqa3XQw==\n-----END PUBLIC KEY-----\n"

@patch('access_helpers.get_aws_elb_public_key')
def test_jwt_payload(mock_get_public_key):
   # note this is a valid but expired token
   encoded_jwt="eyJ0eXAiOiJKV1QiLCJraWQiOiJiYmQ3NTY0Mi03Y2VkLTQxNTItOTA4NC00Njc2N2E2ZTdjOWQiLCJhbGciOiJFUzI1NiIsImlzcyI6Imh0dHBzOi8vcmVwby1wcm9kLnByb2Quc2FnZWJhc2Uub3JnL2F1dGgvdjEiLCJjbGllbnQiOiIxMDAwNTMiLCJzaWduZXIiOiJhcm46YXdzOmVsYXN0aWNsb2FkYmFsYW5jaW5nOnVzLWVhc3QtMToyMzcxNzk2NzM4MDY6bG9hZGJhbGFuY2VyL2FwcC9hbGItbi1BcHBsaS0xQUtWNVo3Skw0OFBILzc5MTgxMGQ5MjgwNzRkM2YiLCJleHAiOjE3MDE5Njk3MTJ9.eyJzdWIiOiJpdTJoMXRjYkl4N2ZsLWlJY0pkRlhBIiwidXNlcmlkIjoiMjczOTYwIiwiZXhwIjoxNzAxOTY5NzEyLCJpc3MiOiJodHRwczovL3JlcG8tcHJvZC5wcm9kLnNhZ2ViYXNlLm9yZy9hdXRoL3YxIn0=.ldjznu0wAwJmdFFRAlp1lm5HPAHsQYoLb6MY9Yfa6ZOPbUzBi17dSa7FvRlUgP9FCFxvjuC7_WmQ9CfgJOyR9A=="
   mock_get_public_key.return_value=PUB_KEY

   # since the token is expired we add 1000 year "leeway" to let jwt validate it

   # method under test
   payload = access_helpers.jwt_payload(encoded_jwt, req=None, validate_time_leeway_seconds=31536000000)

   assert payload['userid']=='273960'

def test_get_approved_user_from_ec2_instance_tags():
   tags = [{"Key":"foo", "Value":"bar"}, {"Key":"Protected/AccessApprovedCaller", "Value":"AROATOOICTTHKNSFVWL5U:273960"}]
   assert access_helpers.get_approved_user_from_ec2_instance_tags(tags) == "273960"
