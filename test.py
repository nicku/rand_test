#!/usr/bin/env python3

import boto3
import json
from os import environ

IMAGE_COUNT = int(environ['IMAGE_COUNT'])
RAM_SHARE = environ['RAM_SHARE']


def extract_new_image_arn(message) -> (bool, str):

    if len(message['Records']) > 1:
        print('something wrong')
        return False, 'na'

    data = json.loads(message['Records'][0]['Sns']['Message'])

    return True, data['arn']


def disassociate_latest_image(ram_client, images: dict):

    latest = tuple()

    for arn, time in images.items():
        if not latest:
            latest = (arn, time)
        else:
            if time < latest[1]:
                latest = (arn, time)

    print(f'Disassociating latest image {arn}')

    ram_client.disassociate_resource_share(
        resourceShareArn=RAM_SHARE,
        resourceArns=[
            latest[0],
        ]
    )


def get_current_images(ram_client) -> dict:

    response = ram_client.list_resources(
        resourceOwner='SELF',
        resourceShareArns=[
            RAM_SHARE,
        ]
    )

    image_list = dict()

    for resource in response['resources']:
        image_list[resource['arn']] = resource['creationTime']

    return image_list


def associate_new_resource(ram_client, arn: str):
    print(f'Associating arn with resource share {arn}')
    ram_client.associate_resource_share(
        resourceShareArn=RAM_SHARE,
        resourceArns=[
            arn,
        ]
    )


def lambda_handler(event, context):

    status, new_image_arn = extract_new_image_arn(event)
    print(new_image_arn)
    if status is False:
        return "Failed to read image data"

    # Get current image shares
    ram_client = boto3.client('ram', region_name='eu-west-1')

    image_list = get_current_images(ram_client)
    print(image_list.keys())
    if len(image_list) > IMAGE_COUNT:
        disassociate_latest_image(ram_client, image_list)

    if new_image_arn not in image_list.keys():
        associate_new_resource(ram_client, new_image_arn)
