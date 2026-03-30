"""MQTT connector for IoT/industrial data sources."""

import time
import json
import threading
from collections import deque

import paho.mqtt.client as mqtt


class MQTTError(Exception):
    """Custom exception for MQTT errors."""

    def __init__(self, message: str, broker: str = ""):
        self.message = message
        self.broker = broker
        super().__init__(f"{broker}: {message}")


class MQTTConnector:
    """MQTT client wrapper with message buffering and topic management.

    Usage:
        connector = MQTTConnector(broker="localhost", port=1883)
        connector.connect()
        connector.subscribe("sensors/#")
        messages = connector.get_messages(topic="sensors/temperature", limit=10)
        connector.disconnect()
    """

    def __init__(
        self,
        broker: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        client_id: str = "mcp-server",
        buffer_size: int = 1000,
        use_tls: bool = False,
    ):
        self.broker = broker
        self.port = port
        self.buffer_size = buffer_size
        self._messages: dict[str, deque] = {}
        self._lock = threading.Lock()
        self._connected = False

        self._client = mqtt.Client(
            client_id=client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        if username and password:
            self._client.username_pw_set(username, password)

        if use_tls:
            self._client.tls_set()

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._connected = True
        else:
            raise MQTTError(
                message=f"Connection failed with code: {reason_code}",
                broker=self.broker,
            )

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = msg.payload.decode("utf-8", errors="replace")

        message = {
            "topic": topic,
            "payload": payload,
            "timestamp": time.time(),
            "qos": msg.qos,
        }

        with self._lock:
            if topic not in self._messages:
                self._messages[topic] = deque(maxlen=self.buffer_size)
            self._messages[topic].append(message)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected = False

    def connect(self, timeout: int = 10) -> None:
        """Connect to the MQTT broker.

        Args:
            timeout: Connection timeout in seconds.

        Raises:
            MQTTError: If connection fails.
        """
        try:
            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()

            deadline = time.time() + timeout
            while not self._connected and time.time() < deadline:
                time.sleep(0.1)

            if not self._connected:
                raise MQTTError(
                    message=f"Connection timed out after {timeout}s",
                    broker=self.broker,
                )
        except OSError as e:
            raise MQTTError(message=str(e), broker=self.broker)

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def subscribe(self, topic: str, qos: int = 0) -> None:
        """Subscribe to a topic pattern.

        Args:
            topic: MQTT topic or wildcard pattern (e.g., "sensors/#").
            qos: Quality of service level (0, 1, or 2).
        """
        if not self._connected:
            raise MQTTError(message="Not connected", broker=self.broker)
        self._client.subscribe(topic, qos=qos)

    def publish(self, topic: str, payload: dict | str, qos: int = 0) -> None:
        """Publish a message to a topic.

        Args:
            topic: MQTT topic to publish to.
            payload: Message payload (dict will be JSON-encoded).
            qos: Quality of service level.
        """
        if not self._connected:
            raise MQTTError(message="Not connected", broker=self.broker)

        if isinstance(payload, dict):
            payload = json.dumps(payload)

        self._client.publish(topic, payload, qos=qos)

    def get_messages(
        self,
        topic: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get buffered messages, optionally filtered by topic.

        Args:
            topic: Filter by exact topic (None for all topics).
            limit: Maximum number of messages to return.

        Returns:
            List of message dicts (newest first).
        """
        with self._lock:
            if topic:
                messages = list(self._messages.get(topic, []))
            else:
                messages = []
                for topic_messages in self._messages.values():
                    messages.extend(topic_messages)

        messages.sort(key=lambda m: m["timestamp"], reverse=True)
        return messages[:limit]

    def get_topics(self) -> list[str]:
        """Get list of topics that have received messages."""
        with self._lock:
            return list(self._messages.keys())

    @property
    def is_connected(self) -> bool:
        return self._connected
