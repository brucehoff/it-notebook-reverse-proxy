# Tests for access.py

from mod_python import apache
from unittest.mock import patch, Mock
import access
import time
from collections import namedtuple

class MockApacheRequest:
    headers_in={'x-amzn-oidc-data':'foo', 'x-amzn-oidc-accesstoken':'bar'}
    content_type=""
    status=0
    interpreter='some-interpreter'
    def write(this, content):
        pass
    def log_error(this, message):
        pass

USERID = "123456"
DIFFERENT_USERID = "987654"

def test_access_missing_header():
    mock_req = MockApacheRequest()
    mock_req.headers_in = {}
    # method under test
    assert access.headerparserhandler(mock_req)==apache.DONE

CacheInfo = namedtuple('CacheInfo', ['hits','misses'])

@patch('access_helpers.jwt_payload', Mock(return_value={"userid": USERID, "exp":time.time()+60}))
@patch('access_helpers.approved_user', Mock(return_value=USERID))
@patch('access_helpers.store_to_ssm', Mock(return_value=None))
@patch('access_helpers.get_aws_elb_public_key_thread_unsafe.cache_info', Mock(return_value=CacheInfo(0,1)))
@patch('access_helpers.approved_user_thread_unsafe.cache_info', Mock(return_value=CacheInfo(0,1)))
@patch('access_helpers.store_to_ssm_thread_unsafe.cache_info', Mock(return_value=CacheInfo(0,1)))
@patch('access_helpers.validate_access_token', Mock(return_value=None))
def test_access_ok():
    mock_req = MockApacheRequest()
    # method under test
    assert access.headerparserhandler(mock_req)==apache.OK


@patch('access_helpers.jwt_payload', Mock(return_value={"userid": DIFFERENT_USERID, "exp":time.time()+60}))
@patch('access_helpers.approved_user', Mock(return_value=USERID))
@patch('access_helpers.store_to_ssm', Mock(return_value=None))
@patch('access_helpers.validate_access_token', Mock(return_value=None))
def test_access_forbidden():
    mock_req = MockApacheRequest()
    # method under test
    assert access.headerparserhandler(mock_req)==apache.HTTP_FORBIDDEN

@patch('access_helpers.jwt_payload', Mock(return_value={"userid": USERID, "exp":time.time()+60}))
@patch('access_helpers.approved_user', Mock(return_value=USERID))
@patch('access_helpers.store_to_ssm', Mock(return_value=None))
@patch('access_helpers.get_aws_elb_public_key_thread_unsafe.cache_info', Mock(return_value=CacheInfo(0,1)))
@patch('access_helpers.approved_user_thread_unsafe.cache_info', Mock(return_value=CacheInfo(0,1)))
@patch('access_helpers.store_to_ssm_thread_unsafe.cache_info', Mock(return_value=CacheInfo(0,1)))
@patch('access_helpers.validate_access_token', Mock(side_effect=Exception("invalid token")))
def test_access_invalid_access_token():
    mock_req = MockApacheRequest()
    # method under test
    assert access.headerparserhandler(mock_req)==apache.DONE
    assert mock_req.status=apache.HTTP_UNAUTHORIZES
