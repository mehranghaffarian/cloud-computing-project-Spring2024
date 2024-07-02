from flask import Flask, jsonify, request, Response
from prometheus_client import generate_latest, CollectorRegistry, Counter, Gauge, Summary, Histogram
import psutil
import time

app = Flask(__name__)

# Create Prometheus metrics to track requests, errors, and latency.
REQUEST_COUNT = Counter('app_request_count', 'Total request count', ['method', 'endpoint'])
ERROR_COUNT = Counter('app_error_count', 'Total error count', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency in seconds', ['method', 'endpoint'])

# Gauge for CPU and Memory usage
CPU_USAGE = Gauge('app_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('app_memory_usage_percent', 'Memory usage percentage')

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    # Check CPU and memory usage
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent

    # Update Prometheus gauges
    CPU_USAGE.set(cpu_usage)
    MEMORY_USAGE.set(memory_usage)

    # Logic to determine health status
    status = "ok" if cpu_usage < 80 and memory_usage < 80 else "unhealthy"
    return jsonify({"status": status, "cpu_usage": cpu_usage, "memory_usage": memory_usage}), 200 if status == "ok" else 503

# Metrics endpoint
@app.route('/metrics', methods=['GET'])
def metrics():
    # Use a collector registry to collect and serve metrics
    registry = CollectorRegistry()
    registry.register(REQUEST_COUNT)
    registry.register(ERROR_COUNT)
    registry.register(REQUEST_LATENCY)
    registry.register(CPU_USAGE)
    registry.register(MEMORY_USAGE)

    return Response(generate_latest(registry), mimetype='text/plain; version=0.0.4; charset=utf-8')

# Middleware to track request count, errors, and latency
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_latency = time.time() - request.start_time
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.path).observe(request_latency)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()
    if response.status_code >= 400:
        ERROR_COUNT.labels(method=request.method, endpoint=request.path).inc()
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
