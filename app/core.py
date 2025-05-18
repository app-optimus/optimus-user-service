import json
import logging

from functools import wraps
from http import HTTPStatus

from fastapi import FastAPI, Request

from app.enums import UserTypes
from app.services.user_details import UserDetails
from app.settings import MODULE_NAME, CUSTOM_HEADER_RPC_SECRET_KEY
from app.utils import _is_valid_uuid, standard_response_generator

logger = logging.getLogger(__name__)


def login_required(func):
    """
    Decorator to check if user is logged in

    If enviroment variable ENV:
    - local : Then user if fetched from redis or user service.
    - production : Then X-CG-User if required in headers.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: FastAPI = kwargs.get("request")
        logger.info("authentication.login_required")

        headers_dict = dict(request.headers)
        auth_token = request.headers.get("authenticationtoken", None)
        if not (auth_token and _is_valid_uuid(auth_token)):
            return standard_response_generator(
                success=False, message="authentication token is required", http_status=HTTPStatus.UNAUTHORIZED
            )
        _, _, _, user = await UserDetails(db=request.app.db, logger=request.app.logger).fetch_user_details(
            core_filters={"authentication_token = '%s'": auth_token}
        )
        if not user or not isinstance(user, dict):
            return standard_response_generator(
                success=False, message="invalid authentication token", http_status=HTTPStatus.UNAUTHORIZED
            )

        request.app.user = user

        return await func(*args, **kwargs)

    return wrapper


def verify_permission(submodules: list = [], exempt_methods: list = []):
    def innerfunc(func):
        @wraps(func)
        async def innerfunc1(*args, **kwargs):
            logger.info("cg_auth.verify_permission")
            request: Request = kwargs.get("request")
            # request.

            # required for cases where verify permission is used to allow only internal RPC calls
            user = request.app.user if hasattr(request.app, "user") else {}

            user_type = user.get("user_type")
            module_name = MODULE_NAME
            route = request.scope.get("route")
            endpoint_name = route.name

            method = request.method
            rpc_secret_key = CUSTOM_HEADER_RPC_SECRET_KEY
            service_permissions = user.get("permissions", {}).get(module_name, {})
            verified = False

            if rpc_secret_key and request.headers.get("RPC_SECRET_KEY") == rpc_secret_key:
                verified = True
            elif user_type == UserTypes.chief_admin:
                verified = True
            else:
                for submodule in submodules:
                    submodule_permissions = service_permissions.get(submodule, {})
                    if method in (
                        submodule_permissions.get("read", {}).get(endpoint_name, [])
                        + submodule_permissions.get("write", {}).get(endpoint_name, [])
                        + exempt_methods
                    ):
                        verified = True
                        break

            if not verified:
                return standard_response_generator(request, False, "Module access not permitted", HTTPStatus.FORBIDDEN)
            return await func(*args, **kwargs)

        return innerfunc1

    return innerfunc
