import requests
from django.conf import settings
from django.core.cache import cache

def fetch_kra_token(app_name, force_refresh=False):
    """
    Get a KRA OAuth token for the specified app, using cache if available.
    Matches exactly with Postman collection structure.
    """
    cache_key = f"kra_token_{app_name}"
    
    # Return cached token unless force_refresh
    if not force_refresh:
        token = cache.get(cache_key)
        if token:
            return token

    # Get app credentials
    app_config = settings.KRA_APPS.get(app_name)
    if not app_config:
        raise Exception(f"Invalid app selection: {app_name}")

    try:
        # Following Postman collection exactly
        params = {
            'grant_type': 'client_credentials'
        }
        
        response = requests.get(  # Note: Using GET as per Postman collection
            app_config["token_url"],
            params=params,
            auth=(app_config["consumer_key"], app_config["consumer_secret"]),
            verify=False  # For sandbox only
        )

        if not response.ok:
            raise Exception(f"Token request failed: {response.text}")

        try:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                # If not in JSON format, try using response text directly
                access_token = response.text.strip()
            
            # Cache token (expires in 1 hour)
            cache.set(cache_key, access_token, timeout=3600)
            return access_token
                
        except Exception as e:
            print(f"Error processing token response: {str(e)}")
            print(f"Response text: {response.text}")
            raise Exception(f"Failed to get access token: {str(e)}")

    except requests.RequestException as e:
        raise Exception(f"Token request failed: {str(e)}")


def call_kra_endpoint(url, payload, app_name, max_retries=5, timeout=60):
    """
    Call a KRA API endpoint with proper authentication.
    Matches Postman collection structure.
    """
    token = fetch_kra_token(app_name)
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        print(f"\nMaking request to: {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")
        
        # Initialize retry counter
        retries = 0
        while retries < max_retries:
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    verify=False,  # For sandbox only
                    timeout=timeout  # Add timeout parameter
                )
                
                print(f"\nResponse Status: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"Response Body: {response.text}")
                
                if response.status_code == 401:
                    # If unauthorized, try with fresh token
                    print("Got 401, refreshing token...")
                    token = fetch_kra_token(app_name, force_refresh=True)
                    headers['Authorization'] = f'Bearer {token}'
                    continue
                    
                if response.status_code == 504:
                    # If gateway timeout, retry
                    print(f"Got 504 Gateway Timeout, retry {retries + 1}/{max_retries}")
                    retries += 1
                    if retries < max_retries:
                        continue
                        
                break  # Break if we get a non-401/504 response
                
            except requests.Timeout:
                print(f"Request timed out, retry {retries + 1}/{max_retries}")
                retries += 1
                if retries >= max_retries:
                    raise Exception("Maximum retries reached, request timed out")
        
        if not response.ok:
            error_details = f"\n        {{\n          \"errorResponse\": {{\n"
            error_details += f"            \"requestId\": \"{response.headers.get('x-request-id', 'unknown')}\",\n"
            error_details += f"            \"code\": \"{response.status_code}\",\n"
            error_details += f"            \"message\": \"{response.text}\",\n"
            error_details += f"            \"timestamp\": \"{response.headers.get('date', 'unknown')}\"\n"
            error_details += "          }\n        }"
            raise Exception(error_details)
            
        return response.json()
        
    except requests.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
