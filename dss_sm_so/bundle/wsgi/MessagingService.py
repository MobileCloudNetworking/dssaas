'''''''''
# Messaging service management class
'''''''''
import json
import time
import logging
import pika

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(threadName)s \t %(levelname)s %(asctime)s: \t%(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

LOG = config_logger()

class MessagingService(object):
    def __init__(self, configModule, epMQ = 'localhost', portMQ = '0' ,userMQ = 'test', passMQ = 'test'):
        self.swComponent = 'SO-Messaging'

        self.portMQ = int(portMQ)
        self.epMQ = epMQ
        self.userMQ = userMQ
        self.passMQ = passMQ
        self.so_config = configModule

        self.exchange_name = 'so-messages'
        self.exchange_type = 'direct'
        self.so_queue_name = 'so_queue'
        self.so_queue_routing_key = 'ack_so'

        self.wait_time = 300 # Seconds

        self.credentials = pika.PlainCredentials(self.userMQ, self.passMQ)
        self.connection = None
        self.channel = None

        self.consume_error = 'START CONSUMPTION ERROR'
        self.reconnect_error = 'RECONNECTION ERROR'
        self.connect_error = 'CONNECTION ERROR'
        self.declare_queue_error = 'QUEUE DECLARATION ERROR'
        self.declare_passive_queue_error = 'PASSIVE QUEUE DECLARATION ERROR'
        self.bind_queue_error = 'BIND QUEUE DECLARATION ERROR'
        self.publish_message_error = 'PUBLISH MESSAGE ERROR'
        self.stop_consume_error = 'STOP CONSUMPTION ERROR'

        LOG.debug(self.swComponent + ' ' + "Messaging service initiated ................")

    def connect_to_mq(self):
        try:
            self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.epMQ,
                        port=self.portMQ,
                        credentials=self.credentials))
            #self.connection.add_timeout(self.wait_time, self.stop_listening)
            self.channel = self.connection.channel()

            self.channel.exchange_declare(exchange=self.exchange_name,
                                     type=self.exchange_type)

            self.declare_queue(self.so_queue_name)
            self.bind_queue(self.so_queue_name, self.exchange_name, self.so_queue_routing_key)
            return True
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + str(e))
            raise Exception(self.connect_error)

    def close_connection(self):
        if self.connection is not None:
            self.connection.close()

    def reconnect(self):
        try:
            self.connect_to_mq()
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + str(e))
            raise Exception(self.reconnect_error)

    # Declares a new message queue
    def declare_queue(self, queue_name, durable=True):
        try:
            self.channel.queue_declare(queue=queue_name, durable=durable)
            return 1
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + str(e))
            raise Exception(self.declare_queue_error)

    # Declares a message queue in passive mode to check if queue exists or not
    def queue_exists(self, queue_name):
        try:
            self.channel.queue_declare(queue=queue_name, passive=True)
            return 1
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + str(e))
            return 0
            #raise Exception(self.declare_passive_queue_error)

    # Binds a message queue to and exchange
    def bind_queue(self, queue_name, exchange_name, routing_key=''):
        try:
            self.channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
            return 1
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + str(e))
            raise Exception(self.bind_queue_error)

    # Publishes a message to exchange
    def basic_publish(self, data, routing_key='', delivery_mode=2):
        try:
            self.channel.basic_publish(exchange=self.exchange_name,
                          body=data,
                          routing_key=routing_key,
                          properties=pika.BasicProperties(
                             delivery_mode = delivery_mode, # 2 makes message persistent
                          ))
            return 1
        except Exception as e:
            LOG.debug(self.swComponent + str(e))
            raise Exception(self.publish_message_error)

    def msg_received(self, ch, method, properties, body):
        # TODO: Check if its config ok message
        self.so_config.notify_msg_receive(body)

    def stop_listening(self):
        try:
            LOG.debug(self.swComponent + ' ' + str(self.wait_time) + ' seconds of waiting, Timeout reached')
            self.channel.stop_consuming()
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + str(e))
            raise Exception(self.stop_consume_error)

    # Fetches one message from Service Orchestrator queue
    def basic_consume(self, queue_name):
        try:
            self.channel.basic_consume(self.msg_received,
                                  queue=queue_name,
                                  no_ack=True)
            self.channel.start_consuming()
        except Exception as e:
            LOG.debug(self.swComponent + ' ' + str(e))
            raise Exception(self.stop_consume_error)

if __name__ == "__main__":
    testcls = MessagingService(None, epMQ='160.85.4.26')
    if testcls.connect_to_mq() is True:
        testcls.basic_publish("Hello my class", testcls.so_queue_routing_key)
        time.sleep(0.1)
        testcls.basic_consume(testcls.so_queue_name)
        testcls.close_connection()