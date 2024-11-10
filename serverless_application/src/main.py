import boto3
import json
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add console handler to logger
logger.addHandler(console_handler)


def get_dynamodb_client():
    try:
        logger.info("Initializing DynamoDB client")
        dynamodb = boto3.client('dynamodb')
        logger.debug("DynamoDB client initialized successfully")
        return dynamodb
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB client: {str(e)}")
        raise


def get_dynamodb_resource(table):
    try:
        logger.info(f"Initializing DynamoDB resource for table: {table}")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table)
        logger.debug(f"Successfully connected to table: {table.table_name}")
        return table
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB resource for table {table}: {str(e)}")
        raise


def get_records(dynamodb_table):
    try:
        logger.info(f"Fetching records from table: {dynamodb_table.table_name}")
        response = dynamodb_table.scan()
        records = response.get('Items', [])
        logger.info(f"Successfully retrieved {len(records)} records")
        logger.debug(f"Records: {json.dumps(records, default=str)}")
        return json.dumps(records)
    except Exception as e:
        logger.error(f"Error fetching records: {str(e)}")
        raise


def put_record(dynamodb_table, item):
    try:
        logger.info(f"Putting record into table: {dynamodb_table.table_name}")
        logger.info(f"Item to put: {json.dumps(item, default=str)}")
        response = dynamodb_table.put_item(Item=item)
        logger.info("Successfully put record")
        return json.dumps(response)
    except Exception as e:
        logger.error(f"Error putting record: {str(e)}")
        raise


def update_record(dynamodb_table, key, update_expression, expression_values):
    try:
        logger.info(f"Updating record in table: {dynamodb_table.table_name}")
        logger.debug(f"Update parameters - Key: {key}, Expression: {update_expression}, Values: {expression_values}")
        response = dynamodb_table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        logger.info("Successfully updated record")
        return response
    except Exception as e:
        logger.error(f"Error updating record: {str(e)}")
        raise


def delete_record(dynamodb_table, key):
    try:
        logger.info(f"Deleting record from table: {dynamodb_table.table_name}")
        logger.debug(f"Delete key: {key}")
        response = dynamodb_table.delete_item(Key=key)
        logger.info("Successfully deleted record")
        return response
    except Exception as e:
        logger.error(f"Error deleting record: {str(e)}")
        raise


# Example of environment-based logging configuration
def configure_logging():
    """Configure logging based on environment"""
    env = os.getenv('ENVIRONMENT', 'dev').lower()

    # Set log level based on environment
    if env == 'prod':
        logger.setLevel(logging.WARNING)
    elif env == 'dev':
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.INFO)

    # Add log format for AWS CloudWatch
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s %(aws_request_id)s %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    for handler in logger.handlers:
        handler.setFormatter(formatter)





# Example usage with context
def get_table_info(table_name):
    logger.info("Starting table info retrieval", extra={
        'table_name': table_name,
        'operation': 'get_table_info'
    })
    try:
        table = get_dynamodb_resource(table_name)
        return {
            'table_name': table.table_name,
            'item_count': table.item_count
        }
    except Exception as e:
        logger.exception("Failed to get table info", extra={
            'table_name': table_name,
            'error': str(e)
        })
        raise


def get_record(dynamodb_table, key):
    try:
        logger.info(f"Fetching record from table: {dynamodb_table.table_name}")
        logger.debug(f"Fetch key: {key}")
        response = dynamodb_table.get_item(Key=key)
        record = response.get('Item')
        logger.info("Successfully fetched record")
        logger.debug(f"Record: {json.dumps(record, default=str)}")
        return json.dumps(record)
    except Exception as e:
        logger.error(f"Error fetching record: {str(e)}")


def handler(event, context):
    logger.info(f"Received event : {event}")
    dynamodb_table = get_dynamodb_resource(os.environ['TABLE_NAME'])
    if event['httpMethod'] == 'GET':
        if event['resource'] == '/users':
            return {
                'statusCode': 200,
                'body': get_records(dynamodb_table)
            }
        elif event['resource'] == '/user/{user_id}':
            return {
                'statusCode': 200,
                'body': get_record(dynamodb_table, {'id': event['pathParameters']['user_id']})
            }
    if event['httpMethod'] == 'POST':
        if event['resource'] == '/user':
            return {
                'statusCode': 200,
                'body': put_record(dynamodb_table, json.loads(event['body']))
            }



if __name__ == '__main__':
    os.environ['TABLE_NAME'] = 'SampleTable'
    event={
        'httpMethod': 'POST', 'resource': '/user', 'body': {'id': '10', 'name': 'Jnana Sai Jitendra Reddy Kalli'}
    }
    handler(event,{})
    response = put_record(get_dynamodb_resource(os.environ['TABLE_NAME']),
                          {'id': '1945', 'name': 'Jnana Sai Jitendra Reddy Kalli'})
    # print(response)
    response = get_record(get_dynamodb_resource(os.environ['TABLE_NAME']), {'id': '0579'})
    print(response)
