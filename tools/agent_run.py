"""Runs one prompt with the Claude Agent SDK in this checkout, for the "Analyse a tool" workflow.

usage: python3 -I tools/agent_run.py <prompt file> <result file> [<spending limit in USD>]

The prompt runs with full tool access (the runner is thrown away afterwards, and the job has no write access to the
repository) and the model, turn limit and spending limit below: a run stops with an error once it has cost MAX_BUDGET_USD.
Only the final result is written, as JSON, to <result file>: Claude's messages stay out of the log (rule 9). Exits 1 when
the run ends with an error. The short first pass that plans the Windows run passes a lower spending limit.
"""
import asyncio, json, sys
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

MODEL = 'claude-opus-5-5'
MAX_TURNS = 300
MAX_BUDGET_USD = 10  # a full analysis has cost about $4


async def main(prompt_file, result_file, budget):
    opts = ClaudeAgentOptions(model=MODEL, max_turns=MAX_TURNS, max_budget_usd=budget,
                              permission_mode='bypassPermissions', setting_sources=['project'], cwd='.')
    res = None
    async for m in query(prompt=open(prompt_file).read(), options=opts):
        if isinstance(m, ResultMessage): res = m
    out = {'type': 'result', 'is_error': True, 'result': 'No result from Claude'} if res is None else {
        'type': 'result', 'is_error': res.is_error, 'subtype': res.subtype, 'result': res.result, 'errors': res.errors,
        'num_turns': res.num_turns, 'total_cost_usd': res.total_cost_usd, 'terminal_reason': res.terminal_reason}
    json.dump([out], open(result_file, 'w'))
    print(f"turns: {out.get('num_turns')}, cost: ${out.get('total_cost_usd') or 0:.2f}, error: {out['is_error']}")
    return 1 if out['is_error'] else 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else MAX_BUDGET_USD)))
