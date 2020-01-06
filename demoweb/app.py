import re
from webob import Response, Request
from webob.dec import wsgify
from webob.exc import HTTPNotFound

from demoweb.utils import NestedContext, convert, RouterDict, Context


class _Router:
    def __init__(self, prefix=''):
        self.__prefix = prefix.rstrip('/\\')
        self.__routers = []
        # 未关联全局的上下文，在注册时注入
        self.context = NestedContext()
        # 拦截器
        self.pre_interceptor = []
        self.post_interceptor = []

    @property
    def prefix(self):
        return self.__prefix

    # 拦截器注册函数
    def register_pre_interceptor(self, fn):
        self.pre_interceptor.append(fn)
        return fn

    def register_post_interceptor(self, fn):
        self.post_interceptor.append(fn)
        return fn

    def route(self, rule, *methods):
        def wrapper(handler):
            pattern, info = convert(rule)
            self.__routers.append((methods, re.compile(pattern), info, handler, self.prefix))
            return handler

        return wrapper

    def get(self, pattern):
        return self.route(pattern, 'GET')

    def post(self, pattern):
        return self.route(pattern, 'POST')

    def head(self, pattern):
        return self.route(pattern, 'HEAD')

    def match(self, request: Request) -> None:
        if not request.path.startswith(self.prefix):
            return
        # 依次执行拦截请求
        for fn in self.pre_interceptor:
            request = fn(self.context, request)
        # TODO 将App中的routers可以改成前缀为key的字典，可以解决下面的多重判断
        if request.path == '/':
            return self.__routers[0][-2](request)
        else:  # 如果path不是主页("/")，才执行下面的代码，否则直接返回主页
            if self.__routers[0][-1]:  # App在注册时用的是append，所以__routers里有所有已注册的view函数，也包括主页，而主页的前缀为空，所以判断非空
                for methods, pattern, info, handler, prefix in self.__routers:
                    if not methods or request.method in methods:
                        matcher = pattern.search(request.path.replace(self.prefix, '', 1))
                        if matcher:
                            temp = {}
                            for key, value in matcher.groupdict().items():
                                temp[key] = info[key](value)
                            request.vars = RouterDict(temp)
                            # response = handler(self.context, request)
                            response = handler(request)
                            # 依次执行拦截响应
                            for fn in self.post_interceptor:
                                response = fn(self.context, request, response)
                            return response
                        # 开发环境报错
                        # raise TypeError('There is some TypeError in your URL.Please check Type or Value in you URL.')
                        # 生产环境报错
                        HTTPNotFound.explanation = '您访问的页面不存在，请检查URL是否输入正确。'
                        raise HTTPNotFound()


class DemoWeb:
    Router = _Router
    Request = Request
    Response = Response

    context = Context()  # 全局上下文
    ROUTERS = []

    def __init__(self, **kwargs):
        self.context.app = self
        for key, value in kwargs.items():
            self.context[key] = value

    # 拦截器
    PRE_INTERCEPTOR = []
    POST_INTERCEPTOR = []

    # 拦截器注册函数
    @classmethod
    def register_post_interceptor(cls, fn):
        cls.POST_INTERCEPTOR.append(fn)
        return fn

    @classmethod
    def register_pre_interceptor(cls, fn):
        cls.PRE_INTERCEPTOR.append(fn)
        return fn

    @classmethod
    def register(cls, router: Router):
        # 为Router实例注入全局上下文
        router.context.relate(cls.context)
        router.context.router = router
        cls.ROUTERS.append(router)

    # TODO 扩展接口
    @classmethod
    def extent(cls, name, ext):
        cls.context[name] = ext

    @wsgify
    def __call__(self, request: Request) -> Response:
        # 全局拦截请求
        for fn in self.PRE_INTERCEPTOR:
            request = fn(self.context, request)

        # 遍历routers，调用Router实例的match方法，看谁匹配
        for router in self.ROUTERS:
            response = router.match(request)
            # 全局拦截响应
            for fn in self.POST_INTERCEPTOR:
                response = fn(self.context, request, response)
            if response:  # 匹配则返回非None的Router对象
                return response
        HTTPNotFound.explanation = '您访问的页面被偷走了'
        raise HTTPNotFound()