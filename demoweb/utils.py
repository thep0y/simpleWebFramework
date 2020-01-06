import re


class RouterDict:
    def __init__(self, d: dict):
        if not isinstance(d, dict):
            self.__dict__['_dict'] = {}
        else:
            self.__dict__['_dict'] = d

    def __getattr__(self, item):
        try:
            return self._dict[item]
        except KeyError:
            raise AttributeError(f"Could not find attribute {item}")

    def __setattr__(self, key, value):
        # 不允许设置属性
        raise NotImplementedError


# 上下文信息类
class Context(dict):  # App用
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f'Attribute {item} is not found.')

    def __setattr__(self, key, value):
        self[key] = value


class NestedContext(Context):  # Router用
    def __init__(self, global_context: Context = None):
        super().__init__()
        self.relate(global_context)

    def relate(self, global_context: Context = None):
        self.global_context = global_context

    def __getattr__(self, item):
        if item in self.keys():
            return self[item]
        return self.global_context[item]


"""
    /python/<name:str>/<id:int> -> /python/(?P<name>\w+)/(?P<id>[+-]\d+)
    写一个函数或类将路由规则傻瓜化，不需要手动写正则表达式
    <>内可以写命名和数据类型，也可以只写命名，如果只写命名，默认为any
"""
TYPEPATTERNS = {
    'str': r'\w+',  # 数字字母下划线
    'int': r'[+-]?\d+',  # 数字
    'float': r'[+-]?\d+\.\d+',  # 浮点
    'any': r'.+'  # 任意非空字符
}

TYPE = {
    'str': str,
    'int': int,
    'float': float,
    'any': str
}


def convert(path):
    info = {}
    start = 0
    end = len(path)
    result = ''
    while start < end:
        temp = path[start:end]
        target = re.search(r'<.*?>', temp)
        if target:
            position = target.span()
            result += temp[:position[0]]
            key, _, value = temp[position[0] + 1:position[1] - 1].partition(':')
            if not value:
                value = 'any'
            if value not in TYPEPATTERNS.keys():
                value = 'any'
                # raise TypeError(f'Type {value} is not Allowed.')
            info[key] = TYPE[value]
            result += f'(?P<{key}>{TYPEPATTERNS[value]})'
            start += position[1]
        else:
            result += path[start:]
            break
    return result, info


if __name__ == '__main__':
    dictionary = Context()
    dictionary.a = 100
    print(dictionary.a)
    print(dictionary)
    path1 = '/python/<name:str>/aaa/<id:int>'
    path2 = '/python/aaa/<id:int>/bbb'
    path3 = '/python/aaa/111'
    path4 = '/python/<name:>/aaa/<id>'
    path5 = '/python/<name:>/aaa/<id:xxx>'
    print(convert(path1))
    print(convert(path2))
    print(convert(path3))
    print(convert(path4))
    print(convert(path5))
