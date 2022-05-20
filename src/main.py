import websocket
import rel
import urllib.parse
import json
import sys
from datetime import datetime
from datetime import timedelta
import yaml
from slack import WebClient
from slack.errors import SlackApiError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


with open(r'settings.yml') as file:
    settings = yaml.load(file, Loader=yaml.FullLoader)
    logger.debug(settings)

client = WebClient(token=settings["slack"]["token"])

def slack(message, username, channel, ts=None):
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message,
            username=username,
            thread_ts=ts,
            icon_emoji=":rotating_light:")
        return response
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        logger.error(f"Got an error: {e.response['error']}")

def grafana_link(selector, ts):
    from_ts = "{}".format(round(1_000*datetime.timestamp(datetime.fromtimestamp(ts) - timedelta(seconds=150))))
    to_ts = "{}".format(round(1_000*datetime.timestamp(datetime.fromtimestamp(ts) + timedelta(seconds=150))))
    grafana_left = { "datasource": "Loki", "queries": [{"refId":"A", "expr": source["selector"]}], "range": { "from": from_ts, "to": to_ts }}
    logger.debug(grafana_left)
    grafana_json = json.dumps(grafana_left, separators=(',', ':'))
    logger.debug(grafana_json)
    grafana_left_str = urllib.parse.quote(grafana_json, safe='/:,.')
    logger.debug(grafana_left_str)
    result = "{url}&left={left}".format(url=settings["grafana"]["url"], left=grafana_left_str)
    logger.debug(" {}".format(result))
    return result

def on_message(ws, message, source):
    res = json.loads(message)
    username = source["name"]
    streams = res["streams"]
    for stream in streams:
        meta = stream["stream"]
        values = stream["values"]
        for value in values:
            link = grafana_link(source["selector"], int(value[0])/(1_000_000_000))
            message = "*{log}* • <{link}|:male-technologist:>\n{meta}".format(meta=dict(sorted(meta.items())), link=link, log=value[1])
            slack(message, username, source["channel"])
            logger.info(message)


def on_error(ws, error):
    logger.error(error)
    exit(1)


def on_close(ws, close_status_code, close_msg):
    logger.info("### closed ###")


def on_open(ws):
    logger.info("Opened connection")


if __name__ == "__main__":
    logger.debug("Starting...")
    # websocket.enableTrace(True)
    ts = datetime.timestamp(datetime.now() - timedelta(seconds=300))
    for source in settings["loki"]["sources"]:
        url =  "{url}/loki/api/v1/tail?query={query}&start={start}".format(
                url=settings["loki"]["url"], query=urllib.parse.quote(source["selector"]), start=ts
            )
        ws = websocket.WebSocketApp(url,
            on_open=on_open,
            on_message=lambda w,m : on_message(w,m, source),
            on_error=on_error,
            on_close=on_close,
        )

        ws.run_forever(dispatcher=rel)  # Set dispatcher to automatic reconnection
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
