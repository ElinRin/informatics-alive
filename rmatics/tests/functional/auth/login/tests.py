import json
import mock
from hamcrest import (
    assert_that,
    equal_to,
    has_entries,
    calling,
    raises,
)

from rmatics.model import db
from rmatics.model.user import User
from rmatics.testutils import TestCase
from rmatics.utils.functions import attrs_to_dict


class TestAPI__auth_login(TestCase):
    def setUp(self):
        super(TestAPI__auth_login, self).setUp()

        self.username = 'some username'
        self.password = 'testtest'
        self.password_md5 = '05a671c66aefea124cc08b76ea6d30bb'

        self.user = User(
            username=self.username,
            password_md5=self.password_md5,
            firstname='some firstname',
            lastname='some lastname'
        )
        db.session.add(self.user)
        db.session.flush()

    def send_request(self,
                     username=None,
                     password=None,
                     moodle_user_id=None,
                     moodle_session=None,
                     ):
        response = self.client.post(
            '/auth/login',
            data=json.dumps({
                'username': username or self.username,
                'password': password or self.password,
            }),
        )
        return response

    def check_request(self,
                      username=None,
                      password=None,
                      moodle_user_id=None,
                      moodle_session=None,
                      status_code=200,
                      message=None,
                      ):
        response = self.send_request(
            username=username,
            password=password,
            moodle_user_id=moodle_user_id,
            moodle_session=moodle_session,
        )

        if status_code != 200:
            assert_that(
                response.json,
                has_entries({
                    'code': status_code,
                    'message': message,
                })
            )
            return

        # В ответе должна быть информация о пользователе
        assert_that(
            response.json,
            has_entries(**attrs_to_dict(self.user, 'id', 'firstname', 'lastname'))
        )

        # В сессии должен быть id пользователя
        with self.client.session_transaction() as session:
            assert_that(
                session,
                has_entries({
                    'user_id': self.user.id,
                })
            )

    def test_simple(self):
        self.check_request()
        
    def test_login_twice(self):
        self.send_request()
        self.check_request()

    def test_login_as_another_user(self):
        self.set_session({'user_id': self.user.id + 1})
        self.check_request()

    def test_wrong_user(self):
        self.check_request(
            username='bad username',
            status_code=403,
            message='Wrong username or password',
        )

    def test_wrong_password(self):
        self.check_request(
            password='wrong password',
            status_code=403,
            message='Wrong username or password',
        )
