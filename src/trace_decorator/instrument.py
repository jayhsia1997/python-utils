"""
telemetry tracer
"""
import asyncio
from functools import wraps
from typing import Callable

from opentelemetry import trace
from opentelemetry.sdk.trace import Tracer
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Span


def instrument(
    *,
    span_name: str = None,
    record_exception: bool = True,
    existing_tracer: Tracer = None,
    inject_span: bool = False
) -> Callable:
    """
    A decorator to instrument a class or function with an OTEL tracing span.
    Usage Example::
        class Foo:

            @instrument()
            def sync_func(self, *args, **kwargs):
                ...

            @instrument()
            async def async_func(self, *args, **kwargs):
                ...

            @instrument(inject_span=True)
            def func_with_inject_span(self, xxx, _span: Span):
                # _span.set_attribute() or _span.set_attributes()
                ...

    :param span_name:
    :param record_exception:
    :param existing_tracer:
    :param inject_span:
    :return:
    """
    def decorator(func):
        """

        :param func:
        :return:
        """
        tracer = existing_tracer or trace.get_tracer(func.__module__)
        name = span_name or func.__qualname__

        def _set_semantic_attributes(span: Span, raw_func: Callable):
            span.set_attribute(SpanAttributes.CODE_NAMESPACE, str(raw_func.__module__))  # noqa
            span.set_attribute(SpanAttributes.CODE_FUNCTION, str(raw_func.__qualname__))  # noqa
            span.set_attribute(SpanAttributes.CODE_FILEPATH, str(raw_func.__code__.co_filename))  # noqa
            span.set_attribute(SpanAttributes.CODE_LINENO, str(raw_func.__code__.co_firstlineno))  # noqa

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """

            :param args:
            :param kwargs:
            :return:
            """
            with tracer.start_as_current_span(
                name=name,
                record_exception=record_exception
            ) as span:  # type: Span
                _set_semantic_attributes(span=span, raw_func=func)
                if inject_span:
                    result = func(*args, **kwargs, _span=span)
                else:
                    result = func(*args, **kwargs)
            return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """

            :param args:
            :param kwargs:
            :return:
            """
            with tracer.start_as_current_span(
                name=name,
                record_exception=record_exception
            ) as span:  # type: Span
                _set_semantic_attributes(span=span, raw_func=func)
                if inject_span:
                    result = await func(*args, **kwargs, _span=span)
                else:
                    result = await func(*args, **kwargs)
            return result

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return wrapper

    return decorator
