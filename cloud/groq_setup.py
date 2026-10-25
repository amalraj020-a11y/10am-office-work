"""Register the authorized Groq Qwen route, preserving other jobs and secrets."""
import json
from pathlib import Path
import subprocess

MODEL_ID = 'qwen/qwen3.8-27b'

def set_config(key, value):
    subprocess.run(['openclaw', 'config', 'set', key, json.dumps(value), '--strict-json'], check=True)

def main():
    c = json.loads((Path.home() / '.openclaw/openclaw.json').read_text())
    provider = c['models']['providers']['groq']
    if not provider.get('apiKey'):
        raise RuntimeError('Existing Groq credential reference required')
    models = provider.get('models', [])
    if not any(m['id'] == MODEL_ID for m in models):
        models.append({'id': MODEL_ID, 'name': 'Groq Qwen office',
                       'input': ['text'], 'reasoning': False,
                       'contextWindow': 16000, 'contextTokens': 16000, 'maxTokens': 768,
                       'compat': {'supportsTools': True}})
    for model in models:
        if model['id'] == MODEL_ID:
            # Allow compact tool turns without OpenClaw's earlier 6800-token
            # context overflow. The workflow still limits each tool output.
            model.update(contextWindow=16000, contextTokens=16000, maxTokens=768)
    set_config('models.providers.groq.models', models)
    allowed = c['agents']['defaults'].get('modelPolicy', {}).get('allow', [])
    if allowed and 'groq/' + MODEL_ID not in allowed:
        set_config('agents.defaults.modelPolicy.allow', allowed + ['groq/' + MODEL_ID])
    print('Groq Qwen registered; no agent permissions or other jobs changed.')

if __name__ == '__main__':
    main()
