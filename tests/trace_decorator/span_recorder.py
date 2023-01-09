"""
SpanRecorder
"""
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor


class TestSpanRecorder(SpanProcessor):
    """
    Test Span Recorder
    """
    def __init__(self):
        self.last_span = None
        self.spans = []

    def on_end(self, span: "ReadableSpan") -> None:
        """

        :param span:
        """
        self.last_span = span
        self.spans.append(span)
