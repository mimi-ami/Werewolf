# Werewolf

一个基于 WebSocket 的狼人杀对局演示项目。后端使用 FastAPI 驱动回合流程，前端使用 React + Vite 展示房间与交互。当前实现为最小可运行版本，AI 行为为内置规则/固定策略，便于验证流程与前后端联调。

## Features

- WebSocket 实时对局状态同步
- 基础对局流程：夜晚行动、白天发言、警长竞选与投票处决
- 多角色能力示例：狼人、预言家、女巫、守卫
- 前后端分离，便于扩展

## Tech Stack

- Backend: FastAPI + Uvicorn + Python
- Frontend: React + Vite

## Project Structure

- `backend/` 后端服务与游戏流程
- `fronted/` 前端页面（Vite 项目）
- `README.md` 项目入口说明

## Quick Start

### 1) 启动后端

进入 `backend` 目录后运行：

```bash
uvicorn backend.run_server:app --reload --host 0.0.0.0 --port 8000
```

或直接：

```bash
python backend/run_server.py
```

后端 WebSocket 地址：`ws://localhost:8000/ws`

### 2) 启动前端

进入 `fronted` 目录后运行：

```bash
npm install
npm run dev
```

默认访问地址通常为 `http://localhost:5173`（以终端输出为准）。

## Notes

- `backend/requirements.txt` 目前为空，请按实际需要补齐依赖（至少需要 `fastapi` 与 `uvicorn`）。
- `backend/config/llm.yaml` 与 `backend/config/game.yaml` 为预留配置文件，目前内容为空。

## Dev Guide

- 前端 WebSocket 连接位于 `fronted/src/ws` 相关目录，可在此扩展事件与协议。
- 后端回合流程与消息类型主要在 `backend/run_server.py` 中实现。
- 若需要扩展 AI 行为或规则，请优先完善后端逻辑与协议约定。

## FAQ

- 启动后端报依赖缺失：请先安装 `fastapi`、`uvicorn`。
- 前端无法连接后端：请确认后端端口与 WebSocket 地址一致，且后端已启动。
