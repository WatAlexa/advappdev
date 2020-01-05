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
        return authenticator.unauthorized_response()

    from jesse.services import jesse_trade
    return jesse_trade.report_exception(
        json_request.description,
        json_request.traceback,
        json_request.mode,
        json_request.attach_logs,
        json_request.session_id,
        json_request.email,
        has_live=HAS_LIVE_TRADE_PLUGIN
    )


@fastapi_app.post("/get-config")
def get_config(json_request: ConfigRequestJson, authorization: Optional[str] = Header(None)):
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    from jesse.modes.data_provider import get_config as gc

    return JSONResponse({
        'data': gc(json_request.current_config, has_live=HAS_LIVE_TRADE_PLUGIN)
    }, status_code=200)


@fastapi_app.post("/update-config")
def update_config(json_request: ConfigRequestJson, authorization: Optional[str] = Header(None)):
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    from jesse.modes.data_provider import update_config as uc

    uc(json_request.current_config)

    return JSONResponse({'message': 'Updated configurations successfully'}, status_code=200)


@fastapi_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    from jesse.services.multiprocessing import process_manager
    from jesse.services.env import ENV_VALUES

    if not authenticator.is_valid_token(token):
        return

    await websocket.accept()

    queue = Queue()
    ch, = await async_redis.psubscribe(f"{ENV_VALUES['APP_PORT']}:channel:*")

    async def echo(q):
        while True:
            msg = await q.get()
            msg = json.loads(msg)
            msg['id'] = process_manager.get_client_id(msg['id'])
            await websocket.send_json(
                msg
            )

    async def reader(channel, q):
        async for ch, message in channel.iter():
            # modify id and set the one that the font-end knows
            await q.put(message)

    asyncio.get_running_loop().create_task(reader(ch, queue))
    asyncio.get_running_loop().create_task(echo(queue))

    try:
        while True:
            # just so WebSocketDisconnect would be raised on connection close
            await websocket.receive_text()
    except WebSocketDisconnect:
        await async_redis.punsubscribe(f"{ENV_VALUES['APP_PORT']}:channel:*")
        print('Websocket disconnected')


# create a Click group
@click.group()
@click.version_option(pkg_resources.get_distribution("jesse").version)
def cli() -> None:
    pass


@cli.command()
@click.option(
    '--strict/--no-strict', default=True,
    help='Default is the strict mode which will raise an exception if the values for license is not set.'
)
def install_live(strict: bool) -> None:
    from jesse.services.installer import install
    install(HAS_LIVE_TRADE_PLUGIN, strict)


@cli.command()
def run() -> None:
    validate_cwd()

    # run all the db migrations
    from jesse.services.migrator import run as run_migrations
    import peewee
    try:
        run_migrations()
    except peewee.OperationalError:
        sleep_seconds = 10
        print(f"Database wasn't ready. Sleep for {sleep_seconds} seconds and try again.")
        time.sleep(sleep_seconds)
        run_migrations()

    # read port from .env file, if not found, use default
    from jesse.services.env import ENV_VALUES
    if 'APP_PORT' in ENV_VALUES:
        port = int(ENV_VALUES['APP_PORT'])
    else:
        port = 9000

    # run the main application
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port, log_level="info")


@fastapi_app.post('/general-info')
def general_info(authorization: Optional[str] = Header(None)) -> JSONResponse:
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    from jesse.services.general_info import get_general_info

    try:
        data = get_general_info(has_live=HAS_LIVE_TRADE_PLUGIN)
    except Exception as e:
        return JSONResponse({
            'error': str(e)
        }, status_code=500)

    return JSONResponse(
        data,
        status_code=200
    )


@fastapi_app.post('/import-candles')
def import_candles(request_json: ImportCandlesRequestJson, authorization: Optional[str] = Header(None)) -> JSONResponse:
    from jesse.services.multiprocessing import process_manager

    validate_cwd()

    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    from jesse.modes import import_candles_mode

    process_manager.add_task(
        import_candles_mode.run, 'candles-' + str(request_json.id), request_json.exchange, request_json.symbol,
        request_json.start_date
    )

    return JSONResponse({'message': 'Started importing candles...'}, status_code=202)


@fastapi_app.delete("/import-candles")
def cancel_import_candles(request_json: CancelRequestJson, authorizati