HttpApi
===

简介
--
> * 本插件提供一个 http api 供其他程序调用本程序功能

相关问题
---
> * 本程序默认监听 `http://127.0.0.1:2019` 如果有需要更改，请修改 `AppData/Plugins/HttpApi/data`
> ```javascript
> {
>    "server": {
>         "host": "127.0.0.1",//监听host
>         "port": 2019//监听端口
>     }
> }
> ```
> * 然后重载插件
