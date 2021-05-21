FFxivPythonTrigger —— 开发相关
===

简介
--
> * 本页文档主要介绍关于插件开发的规范以及框架提供的功能集成
> * 文档随缘更新，如果发现文档出现任何问题请想办法自己处理

Hello World
--
> * 先让我们看看一个基础的fpt插件
> ```python3
> from FFxivPythonTrigger import *
> 
> 
> class HelloWorld(PluginBase):
>     name = "My first plugin"
> 
>     def __init__(self):
>         super().__init__()
>         self.register_event("log_event", self.work)
> 
>     def _start(self):
>         self.logger.info("start!")
> 
>     def _onunload(self):
>         self.logger.info("close!")
> 
>     def work(self, evt):
>         self.logger.info(evt.message)
> ```
> * 一个标准的插件需要继承 `PluginBase` 类，并且定义自己的`name`作为插件唯一标识
> * 初始化时请确认调用 `super().__init__()`
> * 每个插件提供两个在初始化以外的触发事件：`_start`以及`_onunload`
> 
> 事件 | 用处 
> --- |:---:
> `_start` | 成功初始化后开始运行插件逻辑（一般用于挂起进程），区别于`__init__` ，在批量加载插件时会在全部插件初始化成功后才会呼叫
> `_onunload`| 插件卸载（关闭运行进程，清理hook、储存资料等）

> * `PluginBase` 类提供以下函数以及变量调用
> 
> 函数 | 用处 
> --- |:---:
> `create_mission(call:callable, *args:any, **kwargs:any)` | 创建一个子线程，并且传递参数
> `register_api(self, name: str, api_object: any)`| 注册api，让其他程序可以进行调用
> `register_event(event_id:any, call:callable)`| 注册事件，事件发生时会以`call(event)`进行呼叫
> 
> 变量 | 用处 
> --- |:---:
> `logger` | 进行文字输出的实体
> `storage`| 提供持续储存空间的实体
> * `register_api`以及`register_event`注册将会在插件卸载时自动注销

> * [Hooks](hook) 相关功能
> * fpt的hook相关功能依靠easyhook进行实现
> ```python3
> from ctypes import *
> from FFxivPythonTrigger.hook import Hook
> 
> 
> class HelloHook(Hook):
>     restype = c_int64 # 函数的返回类型
>     argtypes = [c_int64, c_int64, c_uint,c_float] # 函数的参数类型
> 
>     def hook_function(self,a1,a2,a3,a4):
>         # hook 调用的函数，可以透过self。original呼叫原函数
>         return self.original(a1,a2,a3,a4)+999
> 
> hello_hook=HelloHook(0x12345678) #提供函数地址，进行钩子挂载
> hello_hook.enable() #启用钩子
> hello_hook.disable() #禁用钩子
> hello_hook.uninstall() #卸载钩子 （卸载后本钩子不可再次使用，请重新实例化一个钩子）
> ```
