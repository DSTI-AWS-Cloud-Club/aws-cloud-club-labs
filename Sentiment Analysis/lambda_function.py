import json
import boto3
import time
import uuid
from decimal import Decimal

comprehend = boto3.client('comprehend', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SentimentAnalysisHistory')

def lambda_handler(event, context):
    try:
        # Parse input
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        text = body.get('text', '')
        
        if not text:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No text provided'})
            }
        
        # Call Comprehend
        response = comprehend.detect_sentiment(
            Text=text,
            LanguageCode='en'
        )
        
        # Format response (keep as floats for API response)
        result = {
            'sentiment': response['Sentiment'],
            'confidence': max(response['SentimentScore'].values()),
            'scores': response['SentimentScore']
        }
        
        # Convert floats to Decimals for DynamoDB
        scores_decimal = {
            k: Decimal(str(v)) for k, v in response['SentimentScore'].items()
        }
        
        # Save to DynamoDB
        table.put_item(
            Item={
                'id': str(uuid.uuid4()),
                'timestamp': int(time.time()),
                'request_text': text,
                'sentiment': result['sentiment'],
                'confidence': Decimal(str(result['confidence'])),
                'scores': scores_decimal
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }