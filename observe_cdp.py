#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Observe Chrome DevTools Protocol (CDP) events during Facebook login.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

import websocket

CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
LOG_PATH = os.path.join("logs", "fb_login_trace.ndjson")

EVENTS_OF_INTEREST = {
    "Network.requestWillBeSent",
    "Network.responseReceived",
    "Network.requestWillBeSentExtraInfo",
    "Network.responseReceivedExtraInfo",
    "Page.frameNavigated",
    "Runtime.consoleAPICalled",
    "Log.entryAdded",
}


@dataclass
class RedirectChain:
    loader_id: str
    urls: List[str] = field(default_factory=list)
    statuses: List[int] = field(default_factory=list)


class CDPObserver:
    def __init__(self, ws_url: str, log_path: str) -> None:
        self.ws_url = ws_url
        self.log_path = log_path
        self.ws: Optional[websocket.WebSocketApp] = None
        self._next_id = 1
        self._main_frame_id: Optional[str] = None
        self._chains: Dict[str, RedirectChain] = {}

        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self._log_file = open(self.log_path, "a", encoding="utf-8")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _send(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        msg = {"id": self._next_id, "method": method}
        if params:
            msg["params"] = params
        self._next_id += 1
        self.ws.send(json.dumps(msg))

    def _redact_set_cookie(self, value: str) -> str:
        parts = [p.strip() for p in value.split(";")]
        if not parts:
            return "<redacted>"
        name_value = parts[0]
        if "=" in name_value:
            name = name_value.split("=", 1)[0]
            parts[0] = f"{name}=<redacted>"
        else:
            parts[0] = "<redacted>"
        return "; ".join(parts)

    def _extract_important_headers(self, headers: Any) -> Dict[str, Any]:
        if headers is None:
            return {}

        normalized: Dict[str, Any] = {}

        if isinstance(headers, dict):
            for k, v in headers.items():
                normalized[str(k).lower()] = v
        elif isinstance(headers, list):
            for item in headers:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).lower()
                value = item.get("value")
                if name:
                    normalized[name] = value

        important: Dict[str, Any] = {}
        if "location" in normalized:
            important["Location"] = normalized.get("location")
        if "set-cookie" in normalized:
            sc = normalized.get("set-cookie")
            if isinstance(sc, list):
                important["Set-Cookie"] = [self._redact_set_cookie(v) for v in sc]
            elif isinstance(sc, str):
                important["Set-Cookie"] = [self._redact_set_cookie(sc)]
            else:
                important["Set-Cookie"] = ["<redacted>"]
        return important

    def _write_log(self, entry: Dict[str, Any]) -> None:
        self._log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._log_file.flush()

    def _print_log(self, entry: Dict[str, Any]) -> None:
        ts = entry.get("timestamp")
        etype = entry.get("event")
        url = entry.get("url") or ""
        status = entry.get("status")
        status_part = f" {status}" if status is not None else ""
        print(f"[{ts}] {etype}{status_part} {url}")

    def _handle_redirect_chain(self, loader_id: str, url: str, status: Optional[int]) -> None:
        chain = self._chains.get(loader_id)
        if not chain:
            chain = RedirectChain(loader_id=loader_id)
            self._chains[loader_id] = chain
        if url and (not chain.urls or chain.urls[-1] != url):
            chain.urls.append(url)
        if status is not None:
            chain.statuses.append(int(status))

    def _finalize_chain(self, loader_id: str, final_url: str) -> None:
        chain = self._chains.pop(loader_id, None)
        if not chain:
            return
        if not chain.urls or chain.urls[-1] != final_url:
            chain.urls.append(final_url)
        entry = {
            "timestamp": self._now(),
            "event": "RedirectChain",
            "url": final_url,
            "status": chain.statuses[-1] if chain.statuses else None,
            "chain": chain.urls,
        }
        self._write_log(entry)
        print(f"[{entry['timestamp']}] RedirectChain {final_url}")
        for hop in chain.urls:
            print(f"  -> {hop}")

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        self.ws = ws
        self._send("Network.enable")
        self._send("Page.enable")
        self._send("Runtime.enable")
        self._send("Log.enable")
        print("CDP domains enabled: Network, Page, Runtime, Log")

    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return

        method = payload.get("method")
        params = payload.get("params", {})

        if method not in EVENTS_OF_INTEREST:
            return

        entry: Dict[str, Any] = {
            "timestamp": self._now(),
            "event": method,
            "url": None,
            "status": None,
            "headers": {},
        }

        if method == "Network.requestWillBeSent":
            request = params.get("request", {})
            entry["url"] = request.get("url")
            entry["headers"] = self._extract_important_headers(request.get("headers"))
            redirect = params.get("redirectResponse")
            if redirect:
                self._handle_redirect_chain(
                    params.get("loaderId"),
                    redirect.get("url"),
                    redirect.get("status"),
                )
            if params.get("type") == "Document" and params.get("frameId") == self._main_frame_id:
                self._handle_redirect_chain(
                    params.get("loaderId"),
                    request.get("url"),
                    None,
                )

        elif method == "Network.responseReceived":
            response = params.get("response", {})
            entry["url"] = response.get("url")
            entry["status"] = response.get("status")
            entry["headers"] = self._extract_important_headers(response.get("headers"))
            if params.get("type") == "Document" and params.get("frameId") == self._main_frame_id:
                self._handle_redirect_chain(
                    params.get("loaderId"),
                    response.get("url"),
                    response.get("status"),
                )

        elif method == "Network.requestWillBeSentExtraInfo":
            entry["url"] = params.get("request", {}).get("url")
            entry["headers"] = self._extract_important_headers(params.get("headers"))

        elif method == "Network.responseReceivedExtraInfo":
            entry["url"] = params.get("response", {}).get("url")
            entry["headers"] = self._extract_important_headers(params.get("headers"))

        elif method == "Page.frameNavigated":
            frame = params.get("frame", {})
            entry["url"] = frame.get("url")
            if frame.get("parentId") is None:
                self._main_frame_id = frame.get("id")
                loader_id = frame.get("loaderId")
                if loader_id:
                    self._finalize_chain(loader_id, frame.get("url"))

        elif method == "Runtime.consoleAPICalled":
            entry["url"] = None
            args = params.get("args", [])
            text = " ".join(str(a.get("value")) for a in args if "value" in a)
            if text:
                entry["message"] = text

        elif method == "Log.entryAdded":
            log_entry = params.get("entry", {})
            entry["url"] = log_entry.get("url")
            entry["message"] = log_entry.get("text")

        self._write_log(entry)
        self._print_log(entry)

    def on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        print(f"CDP error: {error}")

    def on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        print(f"CDP closed: {close_status_code} {close_msg}")

    def run(self) -> None:
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        try:
            self.ws.run_forever()
        except KeyboardInterrupt:
            print("Stopped by user")
        finally:
            self._log_file.close()


def get_cdp_ws_url() -> str:
    version_url = f"http://{CDP_HOST}:{CDP_PORT}/json/version"
    with urlopen(version_url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    ws_url = data.get("webSocketDebuggerUrl")
    if not ws_url:
        raise RuntimeError("webSocketDebuggerUrl not found. Is Chrome running with --remote-debugging-port?")
    return ws_url


def main() -> int:
    try:
        ws_url = get_cdp_ws_url()
    except Exception as exc:
        print(f"Failed to get CDP WebSocket URL: {exc}")
        return 1

    print(f"Connecting to CDP: {ws_url}")
    observer = CDPObserver(ws_url, LOG_PATH)
    observer.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
