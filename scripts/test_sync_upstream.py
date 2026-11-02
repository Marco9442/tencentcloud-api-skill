#!/usr/bin/env python3
"""sync_upstream.fetch 的重试行为。"""

from __future__ import annotations

import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_upstream


URL = "https://example.test/skill"


class Body:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "Body":
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(URL, code, "error", hdrs=None, fp=io.BytesIO(b"no"))


class FetchRetryTest(unittest.TestCase):
    def test_returns_body_without_retry_when_upstream_is_healthy(self) -> None:
        with mock.patch.object(
            sync_upstream.urllib.request, "urlopen", return_value=Body(b"ok")
        ) as urlopen, mock.patch.object(sync_upstream.time, "sleep") as sleep:
            self.assertEqual(sync_upstream.fetch(URL), b"ok")

        self.assertEqual(urlopen.call_count, 1)
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.get_header("User-agent"),
            "Marco9442/tencentcloud-api-skill sync workflow",
        )
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 60)
        sleep.assert_not_called()

    def test_retries_five_times_then_returns_body(self) -> None:
        responses = [http_error(500) for _ in range(5)] + [Body(b"ok")]
        with mock.patch.object(
            sync_upstream.urllib.request, "urlopen", side_effect=responses
        ) as urlopen, mock.patch.object(sync_upstream.time, "sleep") as sleep:
            self.assertEqual(sync_upstream.fetch(URL), b"ok")

        self.assertEqual(urlopen.call_count, 6)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2, 4, 8, 16])

    def test_raises_after_five_retries_are_exhausted(self) -> None:
        with mock.patch.object(
            sync_upstream.urllib.request,
            "urlopen",
            side_effect=[http_error(500) for _ in range(6)],
        ) as urlopen, mock.patch.object(sync_upstream.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                sync_upstream.fetch(URL)

        self.assertEqual(caught.exception.code, 500)
        self.assertEqual(urlopen.call_count, 6)
        self.assertEqual(sleep.call_count, 5)

    def test_retries_rate_limit_and_network_errors(self) -> None:
        cases = (
            [http_error(429), Body(b"ok")],
            [urllib.error.URLError("timed out"), Body(b"ok")],
            [TimeoutError("timed out"), Body(b"ok")],
        )
        for responses in cases:
            with self.subTest(responses=responses):
                with mock.patch.object(
                    sync_upstream.urllib.request, "urlopen", side_effect=responses
                ) as urlopen, mock.patch.object(sync_upstream.time, "sleep") as sleep:
                    self.assertEqual(sync_upstream.fetch(URL), b"ok")
                self.assertEqual(urlopen.call_count, 2)
                sleep.assert_called_once_with(1)

    def test_does_not_retry_client_errors(self) -> None:
        for code in (400, 401, 403, 404, 422):
            with self.subTest(code=code):
                with mock.patch.object(
                    sync_upstream.urllib.request, "urlopen", side_effect=http_error(code)
                ) as urlopen, mock.patch.object(sync_upstream.time, "sleep") as sleep:
                    with self.assertRaises(urllib.error.HTTPError) as caught:
                        sync_upstream.fetch(URL)
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(urlopen.call_count, 1)
                sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
