# -*- coding: utf-8 -*-
from calendar import timegm
from datetime import datetime, timedelta

import jwt
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework_jwt.compat import (
    get_username_field, PasswordField, Serializer
)
from rest_framework_jwt.settings import api_settings

from shuup_api_permission.models import APIAccess

User = get_user_model()
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class JSONWebTokenSerializer(Serializer):
    """
    Serializer class used to validate API key, API secret, username and password.

    'username' is identified by the custom UserModel.USERNAME_FIELD.

    Returns a JSON Web Token that can be used to authenticate later calls.
    """
    api_key = serializers.CharField(write_only=True)
    api_secret = serializers.CharField(write_only=True)
    password = PasswordField(write_only=True, required=False)

    def __init__(self, *args, **kwargs):
        """
        Dynamically add the USERNAME_FIELD to self.fields.
        """
        super(JSONWebTokenSerializer, self).__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField(required=False)

    @property
    def username_field(self):
        return get_username_field()

    def validate(self, attrs):
        api_key = attrs['api_key']
        api_secret = attrs['api_secret']

        try:
            api_access = APIAccess.objects.get(key=api_key, secret=api_secret)
        except APIAccess.DoesNotExist:
            raise serializers.ValidationError(_("Invalid API key or secret."))

        username = attrs.get(self.username_field)
        user = AnonymousUser()

        if username:
            credentials = {
                self.username_field: username,
                'password': attrs.get('password')
            }

            if all(credentials.values()):
                user = authenticate(**credentials)
                if user:
                    if not user.is_active:
                        raise serializers.ValidationError(_('User account is disabled.'))
                else:
                    raise serializers.ValidationError(_('Unable to log in with provided credentials.'))
            else:
                msg = _('Must include "{username_field}" and "password".')
                msg = msg.format(username_field=self.username_field)
                raise serializers.ValidationError(msg)

        payload = jwt_payload_handler(user, api_access=api_access, shop=self.context["request"].shop)

        return {
            'token': jwt_encode_handler(payload),
            'user': user
        }


class VerificationBaseSerializer(Serializer):
    """
    Abstract serializer used for verifying and refreshing JWTs.
    """
    token = serializers.CharField()

    def validate(self, attrs):
        raise NotImplementedError('Please define a validate method.')

    def _check_payload(self, token):
        # Check payload valid (based off of JSONWebTokenAuthentication,
        # may want to refactor)
        try:
            payload = jwt_decode_handler(token)
        except jwt.ExpiredSignature:
            raise serializers.ValidationError(_('Signature has expired.'))
        except jwt.DecodeError:
            raise serializers.ValidationError(_('Error decoding signature.'))

        return payload

    def _check_user(self, payload):
        username = jwt_get_username_from_payload(payload)

        if not username:
            return AnonymousUser()

        # Make sure user exists
        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User doesn't exist."))

        if not user.is_active:
            raise serializers.ValidationError(_('User account is disabled.'))

        return user


class VerifyJSONWebTokenSerializer(VerificationBaseSerializer):
    """
    Check the veracity of an access token.
    """

    def validate(self, attrs):
        token = attrs['token']

        payload = self._check_payload(token=token)
        user = self._check_user(payload=payload)

        return {
            'token': token,
            'user': user
        }


class RefreshJSONWebTokenSerializer(VerificationBaseSerializer):
    """
    Refresh an access token.
    """

    def validate(self, attrs):
        token = attrs['token']

        payload = self._check_payload(token=token)
        user = self._check_user(payload=payload)
        # Get and check 'orig_iat'
        orig_iat = payload.get('orig_iat')

        try:
            api_access = APIAccess.objects.get(key=payload["api_key"])
        except APIAccess.DoesNotExist:
            raise serializers.ValidationError(_("Invalid API key."))

        if orig_iat:
            # Verify expiration
            refresh_limit = api_settings.JWT_REFRESH_EXPIRATION_DELTA

            if isinstance(refresh_limit, timedelta):
                refresh_limit = (refresh_limit.days * 24 * 3600 +
                                 refresh_limit.seconds)

            expiration_timestamp = orig_iat + int(refresh_limit)
            now_timestamp = timegm(datetime.utcnow().utctimetuple())

            if now_timestamp > expiration_timestamp:
                raise serializers.ValidationError(_('Refresh has expired.'))
        else:
            raise serializers.ValidationError(_('orig_iat field is required.'))

        new_payload = jwt_payload_handler(user, api_access=api_access, shop=self.context["request"].shop)
        new_payload['orig_iat'] = orig_iat

        return {
            'token': jwt_encode_handler(new_payload),
            'user': user
        }
