from __future__ import print_function

from base64 import b64decode

import boto3
import cfnresponse
import logging
import os
import traceback
from datadog import initialize, api
from cfn_datadog import TimeBoard

# Decrypt code should run once and variables stored outside of the function
# handler so that these are decrypted once per container
api_key = boto3.client('kms').decrypt(CiphertextBlob=b64decode(os.environ['api_key']))['Plaintext']
application_key = boto3.client('kms').decrypt(CiphertextBlob=b64decode(os.environ['application_key']))['Plaintext']


# TODO Dry this code: remove duplicate code
def handler(event, context):
    """

    """
    logger = logging.getLogger("datadog")
    logger.setLevel(os.environ.get("LOG_LEVEL", logging.DEBUG))
    logging.debug("Log level set to: %s", os.environ.get("LOG_LEVEL", logging.DEBUG))
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    def createTimeboard(properties):
        response = api.Timeboard.create(**properties)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, physical_resource_id=str(response['id']))
        logger.info("Created a %s Timeboard", type)
        logger.debug("Response object: %s", response)

    def delete(id):
        if id == 'FAILURE':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, physical_resource_id='FAILURE')
            return
        response = api.Timeboard.delete(id)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, physical_resource_id=str(response['deleted_monitor_id']))
        logger.info("Deleted monitor: %s", id)
        logger.debug("Response object: %s", response)

    def update(id, properties):
        logger.debug("Old properties: %s", event['OldResourceProperties'])
        logger.debug("New properties: %s", properties)
        response = api.Timeboard.update(id, **properties)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, physical_resource_id=str(response['id']))
        logger.info("Updated monitor: %s", id)
        logger.debug("Response object: %s", response)

    try:

        initialize(app_key=application_key, api_key=api_key)

        logger.debug("event: %s", event)
        event['ResourceProperties']["query"] = event['ResourceProperties']["query"].lower()
        if event['RequestType'] == 'Delete':
            delete(event['PhysicalResourceId'])
        elif event['RequestType'] == 'Create':
            createTimeboard(event['ResourceProperties'])
        elif event['RequestType'] == 'Update':
            update(event['PhysicalResourceId'], event["ResourceProperties"])
        else:
            raise TypeError("Invalid CF event RequestType")

    except Exception as ex:
        logger.error("Exception %s", ex)
        logger.debug("Traceback: %s", traceback.format_exc())
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS)
            return
        cfnresponse.send(event, context, cfnresponse.FAILED, physical_resource_id="FAILURE")
        raise ex
