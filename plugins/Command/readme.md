Command
===

简介
--
> * 本插件提供处理游戏内指令并呼叫回调的功能，同时提供基础操作指令
> * 目前操作均透过默语频道（/e xxxxx）进行

操作指令
---
> * 注册指令：`@fpt`
> * 格式： `/e @fpt [func] [args]...`
> * 功能 (`*[arg]` 代表可选参数)：
> 
> 功能 | 介绍  | 格式
> --- |:---|:---:
> list| 列出当前安装插件 | `/e @fpt list`
> close| 关闭FPT（强烈推荐！） | `/e @fpt close`
> unload| 卸载指定插件 | `/e @fpt unload [module_name]`
> reload| 加载/重载指定插件 | `/e @fpt reload [module_name]`
