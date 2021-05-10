XivCraft
===

简介
--
> * 本插件提供分析游戏内生产情况从而提供解法的功能

启用
--
> * 游戏内执行`/e @fpt reload XivCraft`
> * 或参考[如何启动默认加载插件](https://github.com/nyaoouo/FFxivPythonTrigger2#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98)

增减solver
--
>修改[registered_solvers](__init__.py#L32)

常见问题
---
> 报错 `ImportError: DLL load failed while importing win32api: 找不到指定的模块。`
> * 解决方法：将`Lib/site-packages/pywin32_system32/`下的所有文件拷贝至`C:/Windows/System32`
