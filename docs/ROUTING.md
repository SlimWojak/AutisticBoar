# AutistBoar — Model Routing

## Current Setup

### Interactive Chat (Telegram)
**Session:** main (this conversation)  
**Model:** `openrouter/anthropic/claude-sonnet-4.5`  
**Use Case:** G's interactive assistant, personality-driven responses, complex reasoning  
**Cost:** ~$3/1M input tokens

### Autonomous Heartbeat (Cron)
**Session:** isolated (spawned every 10 minutes)  
**Model:** `openrouter/deepseek/deepseek-chat`  
**Fallback:** None configured (single model, fail if unavailable)  
**Use Case:** Execute HEARTBEAT.md checklist, structured decision-making  
**Cost:** ~$0.30/1M input tokens, ~$0.12/1M output tokens (10x cheaper than Sonnet)

## Cron Configuration

```yaml
Schedule: Every 10 minutes (600,000ms)
Payload: agentTurn with HEARTBEAT.md prompt
Model: deepseek/deepseek-chat
Timeout: 300 seconds
Delivery: none (no Telegram announcements unless alert)
```

Job ID: `39f92597-872d-493e-b847-95fe8929ea0c`

## Why This Split?

- **Sonnet** excels at personality, wit, complex multi-step reasoning → ideal for chat
- **Qwen 2.5 72B** is cheap, fast, good at structured tasks → ideal for HEARTBEAT.md execution
- **Cost savings:** ~$2.85/1M tokens saved per heartbeat cycle
- **Isolation:** Heartbeat failures don't pollute main chat session

## Fallback Strategy

If Qwen fails, the heartbeat job will error and retry on next 10-min cycle. No automatic fallback to prevent accidental Sonnet bleed. Monitor via:

```bash
openclaw cron runs --jobId 980bf93d-31a2-4cae-9379-8e881e420485 --limit 10
```

## Changing Models

To update the heartbeat model, delete and recreate the job (update not supported for payload fields):

```bash
openclaw cron remove --jobId 39f92597-872d-493e-b847-95fe8929ea0c
openclaw cron add --job '{...}' # with new model
```

To update the main agent model, edit `~/.openclaw/openclaw.json`:

```json
"agents": {
  "defaults": {
    "model": {
      "primary": "openrouter/anthropic/claude-sonnet-4.5"
    }
  }
}
```

## Cost Tracking

Monitor spend via OpenRouter dashboard: https://openrouter.ai/activity

Expected usage:
- **Heartbeat:** ~144 cycles/day × ~18K tokens/cycle = 2.6M tokens/day × $0.30/1M = **$0.78/day**
- **Chat:** Variable, depends on G's activity. Assume 10 interactions/day × 50K tokens = 500K tokens/day × $3/1M = **$1.50/day**

**Total estimated:** ~$2.30/day or ~$70/month

**Actual observed (first heartbeat):**
- DeepSeek heartbeat: $0.0105 per cycle → $1.51/day (144 cycles)
- Savings vs Sonnet: ~$4.46/day (~$135/month)
