import grpc
from datetime import datetime

from app.grpc.generated import market_pb2, market_pb2_grpc
from app.application.queries.get_ohlcv import GetOHLCVQuery, GetOHLCVHandler
from app.application.queries.get_last_price import GetLastPriceQuery, GetLastPriceHandler
from app.domain.exceptions import TickerNotFoundError, InvalidIntervalError


class MarketServicer(market_pb2_grpc.MarketServiceServicer):

    def __init__(
        self,
        get_ohlcv_handler:      GetOHLCVHandler,
        get_last_price_handler: GetLastPriceHandler,
    ) -> None:
        self._get_ohlcv      = get_ohlcv_handler
        self._get_last_price = get_last_price_handler

    async def GetOHLCV(
        self,
        request: market_pb2.OHLCVRequest,
        context: grpc.aio.ServicerContext,
    ) -> market_pb2.OHLCVResponse:
        try:
            result = await self._get_ohlcv.handle(GetOHLCVQuery(
                ticker=request.ticker,
                from_dt=datetime.fromisoformat(request.from_dt),
                to_dt=datetime.fromisoformat(request.to_dt),
                interval=request.interval,
            ))

            bars = [
                market_pb2.PriceBar(
                    time=bar.time.isoformat(),
                    ticker=bar.ticker,
                    open=str(bar.open) if bar.open else "",
                    high=str(bar.high) if bar.high else "",
                    low=str(bar.low)   if bar.low  else "",
                    close=str(bar.close),
                    volume=bar.volume or 0,
                )
                for bar in result.bars
            ]

            return market_pb2.OHLCVResponse(
                ticker=result.ticker,
                interval=result.interval,
                bars=bars,
            )

        except TickerNotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))

        except InvalidIntervalError as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

        except Exception as e:
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetLastPrice(
        self,
        request: market_pb2.LastPriceRequest,
        context: grpc.aio.ServicerContext,
    ) -> market_pb2.LastPriceResponse:
        try:
            price = await self._get_last_price.handle(
                GetLastPriceQuery(ticker=request.ticker)
            )
            return market_pb2.LastPriceResponse(
                ticker=request.ticker.upper(),
                price=str(price),
            )

        except TickerNotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))

        except Exception as e:
            await context.abort(grpc.StatusCode.INTERNAL, str(e))