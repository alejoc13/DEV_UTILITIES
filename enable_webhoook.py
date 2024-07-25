import json

def get_data():
    print("mamastrukis")
def handler(event, context):


    print("Received event: " + json.dumps(event, indent=2))
    operation = event['httpMethod']


    if operation == 'GET':
    # GET is the normal webhook firing on save,
    # so we just fetch the SmartSheet anbd save as parquet in S3
        return (get_data())
    elif operation == 'POST':
    
    # POST is the test from SmartSheet to see if the function 
    # is ready and able to handle the webhook.
    # This is what makes it all work
        if 'Smartsheet-Hook-Challenge' in event['headers']:
            return {
                'statusCode': 200,
                'headers': {
                    'Smartsheet-Hook-Response':
                        event['headers']['Smartsheet-Hook-Challenge'],
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST'
                }
            }
        else:
            return (get_data())
    elif operation == 'OPTIONS':
        return {'statusCode': 200}
    else:
        raise ValueError('Unsupported method "{}"'.format(operation))