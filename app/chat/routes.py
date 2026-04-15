from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.llm_brain.llm_interface import LLMInterface
from app.orchestrator.db import (
    create_chat_session,
    save_chat_message,
    list_chat_sessions,
    get_chat_messages,
    delete_chat_session,
)
import httpx
import json
import uuid

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

llm_interface = LLMInterface()

SYSTEM_PROMPT = (
    "你是一名专业的网络安全渗透测试专家，擅长Web应用安全评估、漏洞分析、渗透测试工具使用和安全建议。"
    "你可以回答关于网络安全、渗透测试方法论、漏洞利用与防御、安全工具使用等专业问题。"
    "回答应当专业、准确、具有实操指导价值。使用Markdown格式回复。"
    "【重要】回答必须简洁精炼，控制在400字以内，不要冗长展开。"
    "直接回答用户的问题，不要主动列举工具清单或工具用法，除非用户明确询问工具相关内容。"
)


class ChatRequest(BaseModel):
    message: str
    model: str = "deepseek-chat"
    session_id: str = ""


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        create_chat_session(session_id, req.message[:30], req.model)

    save_chat_message(session_id, "user", req.message)

    tools_list = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post("http://127.0.0.1:9876/jsonrpc", json={
                "jsonrpc": "2.0", "method": "initialize",
                "params": {"client": "ai-chat", "version": "1.0.0"}, "id": 1
            })
            if r.status_code == 200:
                r = await client.post("http://127.0.0.1:9876/jsonrpc", json={
                    "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2
                })
                tools_data = r.json().get("result", {})
                tools_list = tools_data.get("tools", [])
    except Exception:
        pass

    prompt = req.message
    if tools_list:
        tools_desc = json.dumps(
            [{"name": t["name"], "desc": t["description"]} for t in tools_list],
            ensure_ascii=False, indent=2
        )
        prompt = (
            f"{req.message}\n\n"
            f"[参考：当前MCP可用工具]\n{tools_desc}\n\n"
            "以上工具仅供参考，当用户明确需要工具建议时再推荐，否则直接回答问题。"
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    db_msgs = get_chat_messages(session_id)
    for m in db_msgs[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": prompt})

    def event_generator():
        full_response = ""
        try:
            for chunk in llm_interface.chat_stream(messages, model=req.model, max_tokens=600):
                full_response += chunk
                data = json.dumps({"content": chunk, "session_id": session_id}, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        save_chat_message(session_id, "assistant", full_response, tools_info=tools_list if tools_list else None)

        done_data = json.dumps({"done": True, "session_id": session_id}, ensure_ascii=False)
        yield f"data: {done_data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/query")
async def chat_query(req: ChatRequest):
    try:
        session_id = req.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            create_chat_session(session_id, req.message[:30], req.model)

        save_chat_message(session_id, "user", req.message)

        tools_list = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post("http://127.0.0.1:9876/jsonrpc", json={
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {"client": "ai-chat", "version": "1.0.0"}, "id": 1
                })
                if r.status_code == 200:
                    r = await client.post("http://127.0.0.1:9876/jsonrpc", json={
                        "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2
                    })
                    tools_data = r.json().get("result", {})
                    tools_list = tools_data.get("tools", [])
        except Exception:
            pass

        prompt = req.message
        if tools_list:
            tools_desc = json.dumps(
                [{"name": t["name"], "desc": t["description"]} for t in tools_list],
                ensure_ascii=False, indent=2
            )
            prompt = (
                f"{req.message}\n\n"
                f"[参考：当前MCP可用工具]\n{tools_desc}\n\n"
                "以上工具仅供参考，当用户明确需要工具建议时再推荐，否则直接回答问题。"
            )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        db_msgs = get_chat_messages(session_id)
        for m in db_msgs[-10:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": prompt})

        response = llm_interface.chat(messages, model=req.model, max_tokens=600)

        save_chat_message(session_id, "assistant", response, tools_info=tools_list if tools_list else None)

        return {
            "status": "success",
            "response": response,
            "session_id": session_id,
            "tools": tools_list,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/models")
async def get_models():
    models = [
        {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "DeepSeek", "available": True},
        {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "provider": "DeepSeek", "available": True},
        {"id": "glm-4-flash", "name": "GLM-4.7-Flash", "provider": "ZhipuAI", "available": True},
    ]
    return {"status": "success", "models": models}


@router.get("/sessions")
async def get_sessions():
    sessions = list_chat_sessions()
    return {"status": "success", "sessions": sessions}


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    messages = get_chat_messages(session_id)
    return {"status": "success", "messages": messages}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    delete_chat_session(session_id)
    return {"status": "success", "message": "会话已删除"}
