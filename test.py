from wsgiref.simple_server import make_server

from demoweb import DemoWeb, jsonify

index = DemoWeb.Router()
py = DemoWeb.Router('/python')

DemoWeb.register(index)
DemoWeb.register(py)


@index.get('^/$')
def index(request):
    return DemoWeb.Response('<h1>这是主页</h1>')


# @py.post(r'^/(\d+)')  #  原始路由是用正则表达式表示的，有些麻烦
@py.post('/<name:str>/<id:int>')  # 傻瓜后的路由通过utils里的convert函数可将固定格式的url转换成需要的正则表达式
def p(request):
    return DemoWeb.Response('<h2>这是Python</h2>')


# 拦截器举例
# @DemoWeb.register_pre_interceptor
# def show_headers(context: Context, request: DemoWeb.Request) -> DemoWeb.Request:
#     print(request.path)
#     print(request.user_agent)
#     return request


# @py.register_pre_interceptor
# def show_prefix(context: Context, request: DemoWeb.Request) -> DemoWeb.Request:
#     print(f'----prefix = {context.router.prefix}')
#     return request


@py.register_post_interceptor
def showjson(context: DemoWeb.context, request: DemoWeb.Request, response: DemoWeb.Response):
    body = response.body.decode()
    return jsonify(body=body)


if __name__ == '__main__':
    ip = '127.0.0.1'
    port = 9999
    server = make_server(ip, port, DemoWeb())
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()