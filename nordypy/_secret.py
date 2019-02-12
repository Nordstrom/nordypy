# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample code, visit the AWS docs:   
# https://aws.amazon.com/developers/getting-started/python/

'''
Grabs secret from AWS Secret Manager. Script modified from the one automatically generated 
when AWS secret is set up.
'''
import boto3
import base64
from botocore.exceptions import ClientError
import json
from ._s3 import _s3_create_session


def _get_secret(secret_name, region_name="us-west-2", environment=None, profile_name=None):
    '''
    Function that grabs secret from AWS Secret Manager and returns a dict.
    Parameters
    -------------
    secret_name : str
        Name of your secret in AWS Secret Manager
    region_name : str
        Region the secret is stored in.
    environment : str [optional]
        'aws' or 'local' depending on whether the script is running locally or in AWS
    profile_name : str [optional]
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'
    '''
    # Create a Secrets Manager client
    session = _s3_create_session(region_name=region_name,
                                 environment=environment,
                                 profile_name=profile_name)
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        print(e)
        secret = 'Failed'
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            
    return json.loads(secret)
