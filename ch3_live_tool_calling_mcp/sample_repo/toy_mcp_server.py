#!/usr/bin/env python3
"""가장 단순한 형태의 MCP(Model Context Protocol) 서버.

외부 패키지 없이 표준 입출력(stdio)으로 JSON-RPC 메시지만 주고받는다.
도구를 딱 하나(roll_dice)만 제공한다 — Claude Code의 내장 도구로는 절대
할 수 없는 일(진짜 난수 주사위 굴리기)이라서, 이 도구가 실제로 호출되면
MCP가 동작하고 있다는 걸 의심할 여지 없이 확인할 수 있다.

claude mcp add로 이 스크립트를 등록하면, Claude Code가 이 프로세스를 띄우고
initialize -> tools/list -> (필요할 때) tools/call 순서로 말을 건다.
"""
import json
import random
import sys

TOOLS = [
    {
        "name": "roll_dice",
        "description": "N면체 주사위를 굴려서 나온 숫자를 반환한다.",
        "inputSchema": {
            "type": "object",
            "properties": {"sides": {"type": "integer", "description": "주사위 면 수"}},
            "required": ["sides"],
        },
    }
]


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle(req):
    method = req.get("method")
    id_ = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": id_,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "toy-mcp-server", "version": "0.1.0"},
            },
        }

    if method == "notifications/initialized":
        return None  # 알림(notification)에는 응답하지 않는다

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": id_, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        if name == "roll_dice":
            sides = int(args.get("sides", 6))
            value = random.randint(1, sides)
            return {
                "jsonrpc": "2.0",
                "id": id_,
                "result": {"content": [{"type": "text", "text": f"{sides}면체 주사위 결과: {value}"}]},
            }
        return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown tool: {name}"}}

    return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req)
        if resp is not None:
            send(resp)


if __name__ == "__main__":
    main()
