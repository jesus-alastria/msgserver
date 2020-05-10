# The Flask web server
from flask import Flask, request, render_template, make_response
from flask import abort, redirect, url_for, jsonify

# A very fast cache with expiration: https://github.com/tkem/cachetools/
from cachetools import TTLCache

# Add CORS support to allow being called from any domain
# This function add the CORS headers to the reply of an OPTIONS reques coming from the browser
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

# This function adds the CORS header to the actual request (POST or GET)
def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# Create the app object
app = Flask(__name__)

# Load the configuration from a file
app.config.from_pyfile('app_config.cfg')

# Get the cache config parameters. Default is 10.000 elements where each element expires after 60 seconds
cache_elements = app.config.get("TTLCACHE_NUM_ELEMENTS", 10000)
cache_expiration = app.config.get("TTLCACHE_EXPIRATION", 60)

# Create the cache
c = TTLCache(cache_elements, cache_expiration)

# The route for writes
@app.route('/write/<sessionKey>', methods=["POST", "OPTIONS"])
def write_item(sessionKey):
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    
    # Check if we have received some data in the POST
    if request.content_length == 0:
        return {"error": "No data received"}

    # Get the payload as a string
    payload = request.get_data(as_text=True)

    # Store in the cache and return the session key
    c[sessionKey] = payload
    return _corsify_actual_response(jsonify({"sessionKey": sessionKey}))


# The route for reads
@app.route("/read/<sessionKey>", methods=["GET", "OPTIONS"])
def read_item(sessionKey):
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()

    # Try to get the element from the cache
    element = c.get(sessionKey)
    return _corsify_actual_response(jsonify({"payload": element}))

# The route for API docs
@app.route("/docs", methods=["GET"])
def docs():
    html = """
<!DOCTYPE html>
<html>
<head>
<link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
<title>OpenAPI specs for Application</title>
</head>
<body>
<div id="swagger-ui">
</div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
<!-- `SwaggerUIBundle` is now available on the page -->
<script>
const ui = SwaggerUIBundle({
    url: '/static/swagger.json',
    dom_id: '#swagger-ui',
    presets: [
    SwaggerUIBundle.presets.apis,
    SwaggerUIBundle.SwaggerUIStandalonePreset
    ],
    layout: "BaseLayout",
    deepLinking: true
})
</script>
</body>
</html>"""

    return html

# The route for favicon.ico
@app.route("/favicon.ico", methods=["GET", "OPTIONS"])
def favicon():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()

    return _corsify_actual_response(redirect("/static/favicon.ico"))


# The route for the home page
@app.route("/", methods=["GET", "OPTIONS"])
def index():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()

#    return render_template('index.html')
    return _corsify_actual_response(redirect("/static/index.html"))


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app.
    app.run(host='0.0.0.0', port=8080, debug=True)