# Tests for access.py

from mod_python import apache
from unittest.mock import patch, Mock
import access
import time

class MockApacheRequest:
    headers_in={'x-amzn-oidc-data':'foo', 'x-amzn-oidc-accesstoken':'bar'}
    content_type=""
    status=0
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

@patch('access_helpers.jwt_payload', Mock(return_value={"userid": USERID, "exp":time.time()+60}))
@patch('access_helpers.approved_user', Mock(return_value=USERID))
@patch('access_helpers.store_to_ssm', Mock(return_value=None))
def test_access_ok():
    mock_req = MockApacheRequest()
    # method under test
    assert access.headerparserhandler(mock_req)==apache.OK


@patch('access_helpers.jwt_payload', Mock(return_value={"userid": DIFFERENT_USERID, "exp":time.time()+60}))
@patch('access_helpers.approved_user', Mock(return_value=USERID))
@patch('access_helpers.store_to_ssm', Mock(return_value=None))
def test_access_forbidden():
    mock_req = MockApacheRequest()
    # method under test
    assert access.headerparserhandler(mock_req)==apache.HTTP_FORBIDDEN
