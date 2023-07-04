"""
TestTraceDecorator
"""
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Span, NonRecordingSpan

from trace_decorator import instrument
from .span_recorder import TestSpanRecorder


class TestTraceDecorator:
    """TestTraceDecorator"""

    span_processor = TestSpanRecorder()

    @classmethod
    def setup_class(cls):
        """setup_class"""
        resource = Resource.create(attributes={SERVICE_NAME: "test"})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(cls.span_processor)
        trace.set_tracer_provider(provider)

    @instrument()
    def test_decorated_function_span(self):
        current_span: Span = trace.get_current_span()
        assert current_span.is_recording() is True
        assert current_span.name == self.test_decorated_function_span.__qualname__  # noqa

    def test_none_decorated_function_span(self):
        current_span: NonRecordingSpan = trace.get_current_span()  # noqa
        assert current_span.is_recording() is False

    @instrument(span_name="foo")
    def test_set_specific_name_for_span(self):
        current_span: Span = trace.get_current_span()
        assert current_span.is_recording() is True
        assert current_span.name is 'foo'  # noqa

    @instrument()
    def test_span_attributes_set_by_decorator(self):
        current_span: Span = trace.get_current_span()
        assert current_span.attributes[SpanAttributes.CODE_FUNCTION] is self.test_span_attributes_set_by_decorator.__qualname__ # noqa
        assert current_span.attributes[SpanAttributes.CODE_FILEPATH].endswith("/tests/trace_decorator/test_instrument.py") # noqa

    @instrument(inject_span=True)
    def test_span_attributes_inject_span(self, **kwargs):
        _span = kwargs.get("_span")
        _span.set_attribute("foo", "foo foo")
        _span.set_attribute("foo2", "foo2 foo2")
        current_span: Span = trace.get_current_span()
        assert current_span.is_recording() is True
        assert current_span.attributes["foo"] == "foo foo" # noqa
        assert current_span.attributes["foo2"] == "foo2 foo2" # noqa

    def test_exception_recorded_by_span(self):
        try:
            self.exception_raising_span()
        except:
            span = self.span_processor.last_span
            assert span.events
            error_event = span.events[0]
            assert error_event.attributes["exception.message"] is "foo"

    def test_exception_not_recorded_by_span(self):
        try:
            self.exception_raising_span_record_exception_false()
        except:
            span = self.span_processor.last_span
            assert not span.events

    @instrument()
    def exception_raising_span(self):
        raise Exception("foo")

    @instrument(record_exception=False)
    def exception_raising_span_record_exception_false(self):
        raise Exception("foo")
