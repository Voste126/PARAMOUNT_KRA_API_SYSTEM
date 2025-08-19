from rest_framework import serializers

class TokenRequestSerializer(serializers.Serializer):
    """
    Request body for fetching/refreshing a sandbox token.
    Field 'app' selects which sandbox app credentials to use (app1 or app2).
    """
    app = serializers.ChoiceField(choices=["app1", "app2"], default="app1")


class TokenResponseSerializer(serializers.Serializer):
    """
    Successful token response.
    """
    access_token = serializers.CharField(help_text="OAuth2 bearer/access token")


class ErrorResponseSerializer(serializers.Serializer):
    """
    Simple error response shape used across endpoints.
    """
    error = serializers.CharField()


class PinByIDRequestSerializer(serializers.Serializer):
    """
    Request body for checking PIN by TaxpayerType + TaxpayerID
    Matches payloads from your sandbox Postman collection.
    """
    app = serializers.ChoiceField(choices=["app1", "app2"], default="app1", required=False)
    TaxpayerType = serializers.CharField(max_length=10, help_text="Country code or taxpayer type, e.g. 'KE'")
    TaxpayerID = serializers.CharField(max_length=64, help_text="Taxpayer identifier (e.g. National ID number)")


class PinByPinRequestSerializer(serializers.Serializer):
    """
    Request body for checking by KRAPIN.
    """
    app = serializers.ChoiceField(choices=["app1", "app2"], default="app1", required=False)
    KRAPIN = serializers.CharField(max_length=64, help_text="KRA PIN e.g. A000000000Z")
