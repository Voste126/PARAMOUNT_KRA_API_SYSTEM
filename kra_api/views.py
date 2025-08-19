# kra_client/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.conf import settings

from .serializers import (
    TokenRequestSerializer,
    TokenResponseSerializer,
    ErrorResponseSerializer,
    PinByIDRequestSerializer,
    PinByPinRequestSerializer,
)

# utils are the helper functions you already have:
# - fetch_kra_token(app_name, force_refresh=False)
# - call_kra_endpoint(url, payload, app_name)
from .utils import fetch_kra_token, call_kra_endpoint

# Generic object schema for KRA responses (sandbox responses are JSON objects)
GENERIC_KRA_RESPONSE = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    description="KRA sandbox JSON response (shape may vary)."
)


class GetTokenView(APIView):
    """
    POST /api/kra/token/
    Request body: {"app":"app1"} -> returns {"access_token": "..."}
    """
    @swagger_auto_schema(
        operation_summary="Fetch or refresh sandbox token",
        request_body=TokenRequestSerializer,
        responses={
            200: openapi.Response(description="Access token", schema=TokenResponseSerializer),
            400: openapi.Response(description="Bad request", schema=ErrorResponseSerializer),
            500: openapi.Response(description="Upstream or server error", schema=ErrorResponseSerializer),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = TokenRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        app = serializer.validated_data["app"]
        try:
            # force refresh so user gets a fresh token when calling this endpoint
            token = fetch_kra_token(app, force_refresh=True)
            return Response({"access_token": token}, status=status.HTTP_200_OK)
        except Exception as e:
            # include upstream details in logs in production; return friendly error here
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PinByIDView(APIView):
    """
    POST /api/kra/pin-by-id/
    Proxy to KRA sandbox endpoint that accepts TaxpayerType & TaxpayerID.
    """
    @swagger_auto_schema(
        operation_summary="Lookup KRA PIN by TaxpayerType & TaxpayerID",
        request_body=PinByIDRequestSerializer,
        responses={
            200: openapi.Response(description="KRA sandbox JSON response", schema=GENERIC_KRA_RESPONSE),
            400: openapi.Response(description="Bad request", schema=ErrorResponseSerializer),
            401: openapi.Response(description="Unauthorized - token or credentials problem", schema=ErrorResponseSerializer),
            500: openapi.Response(description="Upstream or server error", schema=ErrorResponseSerializer),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = PinByIDRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        app = serializer.validated_data.get("app", "app1")
        payload = {
            "TaxpayerType": serializer.validated_data["TaxpayerType"],
            "TaxpayerID": serializer.validated_data["TaxpayerID"],
        }

        try:
            # settings.KRA_PIN_BY_ID_URL should be set in settings.py
            url = getattr(settings, "KRA_PIN_BY_ID_URL", None)
            if not url:
                return Response({"error": "KRA_PIN_BY_ID_URL not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            resp_json = call_kra_endpoint(url, payload, app)
            return Response(resp_json, status=status.HTTP_200_OK)
        except Exception as e:
            # If desired, inspect exception type to return 401 for auth issues.
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PinByPinView(APIView):
    """
    POST /api/kra/pin-by-pin/
    Proxy to KRA sandbox endpoint that accepts KRAPIN.
    """
    @swagger_auto_schema(
        operation_summary="Lookup KRA details by KRAPIN",
        request_body=PinByPinRequestSerializer,
        responses={
            200: openapi.Response(description="KRA sandbox JSON response", schema=GENERIC_KRA_RESPONSE),
            400: openapi.Response(description="Bad request", schema=ErrorResponseSerializer),
            401: openapi.Response(description="Unauthorized - token or credentials problem", schema=ErrorResponseSerializer),
            500: openapi.Response(description="Upstream or server error", schema=ErrorResponseSerializer),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = PinByPinRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        app = serializer.validated_data.get("app", "app1")
        payload = {"KRAPIN": serializer.validated_data["KRAPIN"]}

        try:
            url = getattr(settings, "KRA_PIN_BY_PIN_URL", None)
            if not url:
                return Response({"error": "KRA_PIN_BY_PIN_URL not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            resp_json = call_kra_endpoint(url, payload, app)
            return Response(resp_json, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
