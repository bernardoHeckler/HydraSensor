import os

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


class PubSubClient:
    def __init__(self, user_id="rfid-service"):
        subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY", "sub-c-7830b8bc-9ccc-4f70-b89d-0a22951b20a8")
        publish_key = os.getenv("PUBNUB_PUBLISH_KEY", "pub-c-e06d1980-4af2-4db4-abbb-a06d85a71eb5")
        channel = os.getenv("PUBNUB_CHANNEL", "meu_canal")

        if "YOUR_" in subscribe_key or "YOUR_" in publish_key:
            raise RuntimeError(
                "Configure PUBNUB_SUBSCRIBE_KEY e PUBNUB_PUBLISH_KEY antes de iniciar a API."
            )

        config = PNConfiguration()
        config.subscribe_key = subscribe_key
        config.publish_key = publish_key
        config.user_id = user_id

        self.channel = channel
        self.client = PubNub(config)

    def publish(self, message):
        envelope = {
            "source": "app.py",
            "channel": self.channel,
            "data": message,
        }
        self.client.publish().channel(self.channel).message(envelope).sync()
