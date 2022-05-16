import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .pxLogManager import pxLogging


# client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])


class pxSlack(pxLogging):
    def __init__(self):
        token = os.environ["MASKT_SLACK_TOKEN"]
        self.client = WebClient(token=token)

    def post_message(self, channel, text, task, dry_run):
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                            "type": "plain_text",
                            "text": f"{task}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": [{
                        "type": "mrkdwn",
                        "text": f"{text}"
                    }]
                }
            ]
            if dry_run:
                section = {
                    "type": "section",
                    "fields": [
                            {
                                "type": "mrkdwn",
                                "text": ":hand:*DryRun*:hand:"
                            }
                    ]
                }
                blocks.insert(2, section)
            response = self.client.chat_postMessage(
                channel=channel, text="placeholder", blocks=blocks)
            # assert response["message"]["text"] == text
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            # assert e.response["ok"] is False
            # assert e.response["error"]  # str like 'invalid_auth',
            # 'channel_not_found'
            self.logger.error(e)
