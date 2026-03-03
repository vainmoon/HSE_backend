from fastapi import Request


def get_model(request: Request):
    return request.app.state.model

def get_kafka_client(request: Request):
    return request.app.state.kafka_client