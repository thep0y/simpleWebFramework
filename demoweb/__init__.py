import json
from .app import DemoWeb

# 增加json支持
def jsonify(**kwargs):
    content = json.dumps(kwargs)
    return DemoWeb.Response(content, status=200, content_type='application/json', charset='utf-8')
