# Marketing Engine

Content generation and chat monitoring for @otklicker (bot: @otklicker_bot).
AI models used for post generation and chat responses via global orchestrator.
Do NOT load parent project instructions -- this engine is self-contained.

## AI Model Usage

This module uses the global AI Orchestrator (`~/.ai-orchestrator/`).

| Task Type | Model | Example |
|-----------|-------|---------|
| Post generation (template-based) | DeepSeek V3 | "Generate launch day post" |
| Chat response drafting | Qwen 2.5 VL 72B | "Reply to user asking about pricing" |
| Content strategy / persona | Kimi K2.5 | "Redesign Artem's voice for new segment" |
| Critical analysis / audit | Claude 4.7 | "Security review of userbot permissions" |

Use `ai "prompt"` from project root for automatic routing, or `ai --tier <tier> "prompt"` for explicit model selection.
