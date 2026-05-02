import grpc
from grpc import aio

from app.grpc.generated import market_pb2_grpc
from app.grpc.servicer import MarketServicer


async def create_grpc_server(servicer: MarketServicer) -> aio.Server:
    server = aio.server()
    market_pb2_grpc.add_MarketServiceServicer_to_server(servicer, server)
    server.add_insecure_port("[::]:50051")
    return server