"""
Http client
"""
import asyncio
import json
import logging
import sys
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union, overload, AsyncIterator

import httpx
from httpx._types import FileTypes  # noqa

request_logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M:%S"
    )
)
request_logger.addHandler(handler)
request_logger.setLevel(logging.DEBUG)


@dataclass
class HttpDefaults:
    """HttpDefaults"""
    base_url: str = None
    verbose: bool = None
    timeout: int = 30
    retry_interval: int = 5


@dataclass
class HttpOptions:
    """HttpOptions"""
    # pylint: disable=too-many-instance-attributes
    url: str = None
    verbose: bool = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    retry_interval: Optional[int] = None
    query: Optional[dict] = None
    content: Optional[Union[str, bytes]] = None
    form: Optional[dict] = None
    json: Optional[dict] = None
    files: Optional[dict] = None
    headers: Optional[dict] = None
    cookies: Optional[dict] = None
    redirects: bool = True
    verify: bool = True


# pylint: disable=missing-function-docstring
class HttpResponse:
    """HttpResponse"""

    def __init__(self, response: httpx.Response):
        self._response = response
        self.status_code = response.status_code
        self._json_result = None

    def _ensure_json_result(self):
        if self._json_result is None:
            self._json_result = self._response.json()
        if self._json_result is None:
            self._json_result = {}

    @property
    def headers(self):
        """headers"""
        return self._response.headers

    @property
    def content(self):
        """content"""
        return self._response.content

    @property
    def cookies(self):
        """cookies"""
        return self._response.cookies

    @property
    def text(self):
        """text"""
        return self._response.text

    @property
    def url(self):
        """url"""
        return self._response.url

    @property
    def encoding(self):
        """encoding"""
        return self._response.encoding

    @property
    def is_redirect(self):
        """is_redirect"""
        return self._response.is_redirect

    @property
    def is_error(self):
        """is_error"""
        return self._response.is_error

    def raise_for_status(self):
        """raise_for_status"""
        return self._response.raise_for_status()

    def iter_bytes(self):
        """iter_bytes"""
        return self._response.iter_bytes()

    def close(self):
        """close"""
        return self._response.close()

    def read(self):
        """read"""
        return self._response.read()

    def json(self) -> dict:
        """json"""
        return self._response.json()

    def elapsed(self):
        """elapsed"""
        return self._response.elapsed

    async def aread(self):
        """aread"""
        return await self._response.aread()

    async def aiter_bytes(
        self,
        chunk_size: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        """

        :param chunk_size:
        :return:
        """
        return self._response.aiter_bytes(chunk_size=chunk_size)


# pylint: disable=too-many-public-methods
class HttpSession:
    """HttpSession"""

    def __init__(self, url: str, defaults: HttpDefaults = None, options: HttpOptions = None):
        self._options = options or HttpOptions()
        self._options.url = url
        self._client: Optional[httpx.AsyncClient] = None
        self._from_session: bool = False
        self.defaults: HttpDefaults = defaults
        self._st = time.time()

    def _set_options_dict_value(self, key: str, name: str, value: Any):
        if not getattr(self._options, key):
            setattr(self._options, key, {})
        getattr(self._options, key)[name] = value

    async def _ensure_client_build(self):
        if self._client:
            return True
        self._client = httpx.AsyncClient(
            timeout=self._options.timeout or self.defaults.timeout,
            verify=self._options.verify
        )
        await self._client.__aenter__()
        return False

    async def __aenter__(self):
        await self._ensure_client_build()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def options(self):
        """options"""
        return self._options

    def verbose(self, verbose: bool):
        """verbose"""
        self._options.verbose = verbose
        return self

    def retry(self, max_retries: int, retry_interval: int = 3):
        """retry"""
        self._options.max_retries = max_retries
        self._options.retry_interval = retry_interval
        return self

    def timeout(self, timeout: int):
        """timeout"""
        self._options.timeout = timeout
        return self

    def redirects(self, allow: bool):
        """redirects"""
        self._options.redirects = allow
        return self

    def add_header(self, name: str, value: Any):
        """add_header"""
        if not name or value is None:
            return self
        self._set_options_dict_value('headers', name, value)
        return self

    def add_headers(self, headers: Dict[str, str]):
        """add_headers"""
        if not headers:
            return self
        for key, value in headers.items():
            self._set_options_dict_value('headers', key, value)
        return self

    def add_cookie(self, name: str, value: Any):
        """add_cookie"""
        if not name or value is None:
            return self
        self._set_options_dict_value('cookies', name, value)
        return self

    @overload
    def add_query(self, data: dict) -> 'HttpSession':
        """add_query"""
        pass

    @overload
    def add_query(self, name: str, value: Any) -> 'HttpSession':
        """add_query"""
        pass

    def add_query(self, name: Union[dict, str], value: Any = None) -> 'HttpSession':
        """add_query"""
        return self._add_item('query', name, value)

    @overload
    def add_content(self, content: Union[str, bytes]) -> 'HttpSession':
        """add_content"""
        pass

    def add_content(self, content: Union[str, bytes]) -> 'HttpSession':
        """add_content"""
        if not content:
            return self
        self._options.content = content
        return self

    @overload
    def add_form(self, data: dict) -> 'HttpSession':
        """add_form"""
        return self

    @overload
    def add_form(self, name: str, value: Any) -> 'HttpSession':
        """add_form"""
        return self

    def add_form(self, name: Union[dict, str], value: Any = None) -> 'HttpSession':
        """add_form"""
        return self._add_item('form', name, value)

    def _add_item(self, key: str, name: Union[dict, str], value: Any = None):
        if not name and value is None:
            return self
        if isinstance(name, dict):
            for _key, _value in name.items():
                if key == 'query':
                    self.add_query(_key, _value)
                else:
                    self.add_form(_key, _value)
        if value is None:
            return self
        if isinstance(value, (list, dict)):
            value = json.dumps(value)
        self._set_options_dict_value(key, name, value)
        return self

    @overload
    def add_file(self, name: str, file: FileTypes):
        """add_file"""
        pass

    def add_file(self, name: str, file: FileTypes):
        """add_file"""
        if file is None:
            return self
        self._set_options_dict_value('files', name, file)
        return self

    def add_json(self, json_data: dict):
        """add_json"""
        if not json_data:
            return self
        if not isinstance(json_data, dict):
            raise TypeError('json data must be dict')
        if not self._options.json:
            self._options.json = json_data
        else:
            self._options.json.update(json_data)
        return self

    def verify(self, verify: bool):
        """verify"""
        self._options.verify = verify
        return self

    def _log_verbose(self, message: Any, *args):
        if self._options.verbose is False:
            return
        if self.defaults.verbose is not True:
            return
        if isinstance(message, str):
            request_logger.info(message, *args)
        elif callable(message):
            request_logger.info(message(), *args)

    def _build_url(self):
        if self._options.url.startswith('http'):
            return self._options.url
        if self.defaults.base_url:
            base_url = self.defaults.base_url.strip('/\\')
            url = self._options.url.lstrip("/\\")
            return f'{base_url}/{url}'
        return self._options.url

    def _build_params(self, http_method: str) -> dict:
        url = self._build_url()
        headers = self._options.headers or {}
        params = self._options.query or {}
        request_params = dict(
            url=url,
            headers=headers,
            cookies=self._options.cookies,
            timeout=self._options.timeout or self.defaults.timeout,
            follow_redirects=self._options.redirects,
        )
        request_params['params'] = params
        if http_method in ('GET', 'DELETE'):
            # pylint: disable=deprecated-method
            if self._options.form:
                request_logger.warning(
                    f'{http_method} Request not to use add_form to add parameters, ignored'
                )
            if self._options.files:
                request_logger.warning(
                    f'{http_method} Request not to use add_file to add parameters, ignored'
                )

        elif http_method in ('POST', 'PUT', 'PATCH'):
            if self._options.form:
                request_params['data'] = self._options.form
            if content := self._options.content:
                request_params['content'] = content
            request_params['files'] = self._options.files
        if self._options.json:
            request_params['json'] = self._options.json
        return request_params

    @staticmethod
    def _format_log_url(params: dict):
        return httpx.URL(params['url'], params=params['params'])

    @staticmethod
    def _format_log_params(params: dict):
        if not params:
            return params
        formatted_params = {}
        for key, value in params.items():
            copy_value = deepcopy(value)
            if key in ('url', 'params'):
                continue
            if key == 'headers':
                for h_key, h_value in value.items():
                    if h_key.lower() in ["authorization"]:
                        copy_value.pop(h_key)
            if not value:
                continue
            formatted_params[key] = copy_value
        return formatted_params

    def _format_log_response(self, response: httpx.Response):
        esp = time.time() - self._st
        if "application/json" in response.headers.get("content-type", []):
            return f"{response.status_code} ({round(esp * 1000)}ms) {response.text}"
        return f"{response.status_code} ({round(esp * 1000)}ms) content-type:{response.headers.get('content-type')}, " \
               f"content-disposition:{response.headers.get('content-disposition')}"

    @staticmethod
    def _format_returns(response: httpx.Response):
        return HttpResponse(response)

    def _format_response(
        self,
        method: str,
        response: httpx.Response,
        retry_count: int,
        is_last_time: bool
    ):
        if response.status_code >= 500:
            if not is_last_time:
                request_logger.debug(
                    f'{method} {self._options.url} Server returned status code '
                    f'{response.status_code} ready to retry {retry_count + 1} times'
                )
                return None
            request_logger.debug(
                f'{method} {self._options.url} '
                f'The server returns a status code {response.status_code}'
            )
        self._log_verbose(lambda: f'{self._format_log_response(response)}')
        return self._format_returns(response)

    def _retry_error_debug_log(
        self,
        method: str,
        is_last_time: bool,
        exception: Exception,
        retry_count: int
    ):
        if not is_last_time:
            request_logger.debug(
                f'{method.upper()} {self._options.url} {str(exception)} '
                f'Ready to retry {retry_count + 1} times'
            )
        else:
            request_logger.debug(
                f'{method.upper()} {self._options.url} {str(exception)} '
                f'Maximum number of retries reached'
            )

    def get(self) -> HttpResponse:
        """get"""
        return self.request('GET')

    def post(self) -> HttpResponse:
        """post"""
        return self.request('POST')

    def put(self) -> HttpResponse:
        """put"""
        return self.request('PUT')

    def delete(self) -> HttpResponse:
        """delete"""
        return self.request('DELETE')

    # pylint: disable=inconsistent-return-statements
    def request(self, method: str) -> HttpResponse:
        """request"""
        assert method, 'method cannot be none'
        method = method.upper()
        params = self._build_params(method)
        self._log_verbose(lambda: f'{method} {self._format_log_url(params)}')
        self._log_verbose(lambda: f'{self._format_log_params(params)}')
        max_retries = 1 if not self._options.max_retries else self._options.max_retries + 1
        for i in range(max_retries):
            is_last_time = (i + 1) == max_retries
            try:
                response = httpx.request(method=method, **params)
                if (
                    response.status_code >= 500
                    and not is_last_time
                    and self._options.retry_interval is not None
                ):
                    time.sleep(self._options.retry_interval)
                formatted_response = self._format_response(
                    method,
                    response,
                    retry_count=i,
                    is_last_time=is_last_time
                )
                if not formatted_response:
                    continue
                return formatted_response
            except (
                asyncio.TimeoutError,
                ConnectionRefusedError,
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout
            ) as exc:  # pylint: disable=invalid-name
                if i == max_retries - 1:
                    raise exc
                if self._options.retry_interval is not None:
                    time.sleep(self._options.retry_interval)
                self._retry_error_debug_log(
                    method.upper(),
                    is_last_time=is_last_time,
                    exception=exc,
                    retry_count=i
                )
                continue

    async def aget(self) -> HttpResponse:
        """aget"""
        return await self.arequest('GET')

    async def apost(self) -> HttpResponse:
        """apost"""
        return await self.arequest('POST')

    async def aput(self) -> HttpResponse:
        """aput"""
        return await self.arequest('PUT')

    async def apatch(self) -> HttpResponse:
        """apatch"""
        return await self.arequest('PATCH')

    async def adelete(self) -> HttpResponse:
        """adelete"""
        return await self.arequest('DELETE')

    async def arequest(self, method: str) -> HttpResponse:
        """arequest"""
        assert method, 'method cannot be none'
        method = method.upper()
        params = self._build_params(method)
        is_created = await self._ensure_client_build()
        max_retries = 1 if not self._options.max_retries else self._options.max_retries + 1
        self._log_verbose(lambda: f'{method} {self._format_log_url(params)}')
        self._log_verbose(lambda: f'{self._format_log_params(params)}')
        for i in range(max_retries):
            is_last_time = (i + 1) == max_retries
            try:
                response = await self._client.request(method=method, **params)
                if (
                    response.status_code >= 500
                    and not is_last_time
                    and self._options.retry_interval is not None
                ):
                    await asyncio.sleep(self._options.retry_interval)
                formatted_response = self._format_response(
                    method,
                    response,
                    retry_count=i,
                    is_last_time=is_last_time
                )
                if not formatted_response:
                    continue
                if not is_created and not self._client.is_closed:
                    await self._client.aclose()
                return formatted_response
            except (
                asyncio.TimeoutError,
                ConnectionRefusedError,
                httpx.ConnectTimeout,
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError
            ) as exc:  # pylint: disable=invalid-name
                if is_last_time:
                    if not is_created and not self._client.is_closed:
                        await self._client.aclose()
                    raise exc
                if self._options.retry_interval is not None:
                    await asyncio.sleep(self._options.retry_interval)
                self._retry_error_debug_log(
                    method.upper(),
                    is_last_time=is_last_time,
                    exception=exc,
                    retry_count=i
                )
                continue
            finally:
                if is_last_time and not is_created and not self._client.is_closed:
                    await self._client.aclose()

    async def aclose(self):
        """aclose"""
        if not self._client:
            return
        await self._client.aclose()


# pylint: disable=too-few-public-methods
class HttpClient:
    """HttpClient"""

    def __init__(self, defaults: HttpDefaults = None):
        self.defaults: HttpDefaults = defaults or HttpDefaults(verbose=True)

    def create(self, url: str = None) -> HttpSession:
        """
        :param url:
        :return:
        """
        return HttpSession(url, self.defaults, HttpOptions())


http_client = HttpClient()
