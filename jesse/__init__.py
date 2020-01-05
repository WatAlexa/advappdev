import asyncio
import json
import os
import warnings
from typing import Optional
import click
import pkg_resources
from fastapi import BackgroundTasks, Query, Header
from starlette.websockets import WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from jesse.services import auth as authenticator
from jesse.services.redis import async_redis, async_publish, sync_publish
from jesse.services.web import fastapi_app, BacktestRequestJson, ImportCandlesRequestJson, CancelRequestJson, \
    LoginRequestJson, ConfigRequestJson, LoginJesseTradeRequestJson, NewStrategyRequestJson, FeedbackRequestJson, \
    ReportExceptionRequestJson, OptimizationRequestJson
import uvicorn
from asyncio import Queue
import jesse.helpers as jh
import time

# to silent stupid pandas warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# variable to know if the live trade plugin is installed
HAS_LIVE_TRADE_PLUGIN = True
try:
    import jesse_live
except ModuleNotFoundError:
    HAS_LIVE_TRADE_PLUGIN = False


def validate_cwd() -> None:
    """
    make sure we're in a Jesse project
    """
    if not jh.is_jesse_project():
        print(
            jh.color(
                'Current directory is not a Jesse project. You must run commands from the root of a Jesse project. Read this page for more info: https://docs.jesse.trade/docs/getting-started/#create-a-new-jesse-project',
                'red'
            )
        )
        os._exit(1)


# print(os.path.dirname(jesse))
JESSE_DIR = os.path.dirname(os.path.realpath(__file__))


# load homepage
@fastapi_app.get("/")
async def index():
    return FileResponse(f"{JESSE_DIR}/static/index.html")


@fastapi_app.post("/terminate-all")
async def terminate_all(authorization: Optional[str] = Header(None)):
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    from jesse.services.multiprocessing import process_manager

    process_manager.flush()
    return JSONResponse({'message': 'terminating all tasks...'})


@fastapi_app.post("/shutdown")
async def shutdown(background_tasks: BackgroundTasks, authorization: Optional[str] = Header(None)):
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    background_tasks.add_task(jh.terminate_app)
    return JSONResponse({'message': 'Shutting down...'})


@fastapi_app.post("/auth")
def auth(json_request: LoginRequestJson):
    return authenticator.password_to_token(json_request.password)


@fastapi_app.post("/make-strategy")
def make_strategy(json_request: NewStrategyRequestJson, authorization: Optional[str] = Header(None)) -> JSONResponse:
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    from jesse.services import strategy_maker
    return strategy_maker.generate(json_request.name)


@fastapi_app.post("/feedback")
def feedback(json_request: FeedbackRequestJson, authorization: Optional[str] = Header(None)) -> JSONResponse:
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    from jesse.services import jesse_trade
    return jesse_trade.feedback(json_request.description, json_request.email)


@fastapi_app.post("/report-exception")
def report_exception(json_request: ReportExceptionRequestJson, authorization: Optional[str] = Header(None)) -> JSONResponse:
    if not authenticator.is_valid_token(authorization):
        r