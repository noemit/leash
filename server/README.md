# Server Component

A Flask/FastAPI server that proxies requests to your Ollama/Pi AI instance.

## Quick Start

```python
from flask import Flask, request, jsonify
import subprocess, json

app = Flask(__name__)
OLLAMA_BASE = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')

@app.route('/api/chat', methods=['POST'])
def chat():
    payload = request.json
    messages = payload.get('messages', [])
    
    # Build Ollama request
    response = subprocess.check_output(
        f'ollama run pi: {json.dumps(messages)}',
        shell=True
    )
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
```

## Features

- Proxies all chat traffic to Ollama
- Adds response timing
- Rate limiting layer
- Session management

## Dependencies

```toml
[dependencies]
flask = ">=2.0"
ollama-client = ">=0.1"
```

## Security

- Add API key validation
- Rate limit per IP
- SSL termination at tunnel endpoint
