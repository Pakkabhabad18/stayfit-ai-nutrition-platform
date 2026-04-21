import requests
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS on the gateway so the frontend can hit it
CORS(app, supports_credentials=True)

# Microservice registry
SERVICES = {
    'auth': 'http://127.0.0.1:5001',
    'profile': 'http://127.0.0.1:5001', # profile is under auth service
    'meals': 'http://127.0.0.1:5002',
    'recommendations': 'http://127.0.0.1:5002',
    'analytics': 'http://127.0.0.1:5003',
    'notifications': 'http://127.0.0.1:5004'
}

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    if request.method == 'OPTIONS':
        # CORS is handled by the Flask-CORS wrapper
        return '', 200
        
    service_namespace = path.split('/')[0]
    
    if service_namespace not in SERVICES:
        return jsonify({'error': f'Service namespace "{service_namespace}" not found'}), 404

    target_url = f"{SERVICES[service_namespace]}/api/{path}"
    if request.query_string:
        target_url += f"?{request.query_string.decode('utf-8')}"
    
    # Forward headers safely
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}

    try:
        req_kwargs = {
            "method": request.method,
            "url": target_url,
            "headers": headers,
            "data": request.get_data(),
            "cookies": request.cookies,
            "allow_redirects": False
        }
        
        excluded_headers_list = [
            'content-encoding', 'content-length', 'transfer-encoding', 'connection',
            'access-control-allow-origin', 'access-control-allow-credentials',
            'access-control-allow-methods', 'access-control-allow-headers',
            'access-control-expose-headers'
        ]

        # Support SSE Streaming dynamically
        if service_namespace == 'notifications':
            req_kwargs["stream"] = True
            resp = requests.request(**req_kwargs)
            
            def stream_generate():
                for chunk in resp.iter_content(chunk_size=None):
                    yield chunk
                    
            resp_headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers_list]
            return Response(stream_generate(), resp.status_code, resp_headers, mimetype='text/event-stream')
        else:
            resp = requests.request(**req_kwargs)
            resp_headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers_list]
            return Response(resp.content, resp.status_code, resp_headers)
            
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'The {service_namespace} microservice is currently down or unreachable.'}), 503

if __name__ == '__main__':
    print("API Gateway starting on port 5000...")
    app.run(port=5000, debug=True)
