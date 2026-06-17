# Modified by smalvy, 2026 — adapted for portfolio-project-1
import os

import boto3
import pytest
import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestApiGateway:

    @pytest.fixture()
    def api_gateway_url(self):
        """ Get the API Gateway URL from Cloudformation Stack outputs """
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")

        if stack_name is None:
            raise ValueError('Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack')
        
        session = boto3.Session(profile_name = os.environ.get("AWS_PROFILE"))
        client = session.client("cloudformation", endpoint_url = os.environ.get("CLOUDFORMATION_ENDPOINT"))

        try:
            response = client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name} \n" f'Please make sure a stack with the name "{stack_name}" exists'
            ) from e

        stacks = response["Stacks"]
        stack_outputs = stacks[0]["Outputs"]
        api_outputs = [output for output in stack_outputs if output["OutputKey"] == "ItemsApi"]

        if not api_outputs:
            raise KeyError(f"ItemsApi not found in stack {stack_name}")

        return api_outputs[0]["OutputValue"]  # Extract url from stack outputs

    
    def test_post_item(self, api_gateway_url):
        payload = {"name": "test item", "description": "test"}
        
        response = requests.post(api_gateway_url, json = payload)

        assert response.status_code == 201
        assert "id" in response.json()

    
    def test_get_items(self, api_gateway_url):
        response = requests.get(api_gateway_url)

        assert response.status_code == 200
        assert type(response.json()) == list


    def test_post_item_missing_body(self, api_gateway_url):
        response = requests.post(api_gateway_url)

        assert response.status_code == 400
