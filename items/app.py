# Modified by smalvy, 2026 — adapted for portfolio-project-1
import json
import uuid
import boto3
import os

dynamodb = None
table = None

def get_table():
    global dynamodb, table
    
    if table is None:
        dynamodb = boto3.resource("dynamodb", endpoint_url = os.environ.get("DYNAMODB_ENDPOINT") or None)
        table = dynamodb.Table(os.environ["TABLE_NAME"])
    
    return table


def lambda_handler(event, context):
    """
    Handles GET /items and POST /items requests from API Gateway.
    Reads and writes items to DynamoDB.
    """
    httpMethod = event["httpMethod"]
    statusCode = 0
    bodyMessage = ""
    
    try:
        if(httpMethod == "GET"):
            table = get_table()
            items = table.scan()

            statusCode = 200
            bodyMessage = json.dumps(items["Items"])
        
        elif(httpMethod == "POST"):
            if not event.get("body"):
                statusCode = 400
                bodyMessage = json.dumps({"error": "Request body is required"})
            
            else:
                table = get_table()
                deserializeEventBody = json.loads(event["body"])
                id = uuid.uuid4()
                item = {}

                item["id"] = id.hex
                item = item | deserializeEventBody

                table.put_item(Item = item)
                
                statusCode = 201
                bodyMessage = item
        
        else:
            statusCode = 405
            bodyMessage = "Method not allowed"

    except Exception as e:
        statusCode = 500
        bodyMessage = json.dumps({"error": str(e)})
    
    return {
            "statusCode": statusCode,
            "body": bodyMessage
        }
