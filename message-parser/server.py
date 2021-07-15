import logging
from concurrent.futures import ThreadPoolExecutor

import grpc

from message_parser_pb2 import ParserResponse
from message_parser_pb2_grpc import MessageParserServicer, add_MessageParserServicer_to_server


import sushy
import json
from sushy import auth
from sushy.resources import base
from sushy.resources.registry import message_registry

# disable InsecureRequestWarning: Unverified HTTPS request is being made to host
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Enable logging at DEBUG level
LOG = logging.getLogger('sushy')
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())


class MessageParserServicer(MessageParserServicer):

    def __init__(self):
        basic_auth = auth.BasicAuth(username='root', password='calvin')
        self.sushy_root = sushy.Sushy('https://10.46.61.142/redfish/v1',
                auth=basic_auth, verify=False)
        # Get the Redfish version
        print(self.sushy_root.redfish_version)
        self.registries = self.sushy_root.lazy_registries
        # preload the registries
        self.registries.registries        
    
    def Parse(self, request, context):
        logging.info('request message_id: %s', request.message_id)
        logging.info('request %d message_args', len(request.message_args))
        for a in request.message_args:
            logging.info('found message arg %s', a)

        m = base.MessageListField('Message')
        m.message_id = request.message_id
        m.message_args = request.message_args

        message_registry.parse_message(self.registries, m)
        resp = ParserResponse(message=m.message, severity=m.severity, resolution=m.resolution)
        logging.info('response message: %s', resp.message)
        logging.info('response severity: %s', resp.severity)
        logging.info('response resolution: %s', resp.resolution)
        return resp


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    server = grpc.server(ThreadPoolExecutor())
    add_MessageParserServicer_to_server(MessageParserServicer(), server)
    port = 9999
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logging.info('server ready on port %r', port)
    server.wait_for_termination()

