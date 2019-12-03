# chinese-chatbot
开放领域中文聊天机器人


>申明：跨专业小白菜课余第一次实践 ⁄(⁄ ⁄•⁄ω⁄•⁄ ⁄)⁄，兼容性拓展不足（翻译：预料兼容性bug良多），欢迎讨论，共同学习。  
搭建环境：python3.6.8 + MongoDB。  
设计时参考了[英文chatterbot](https://github.com/gunthercox/ChatterBot)，特此申明。  
本项目代码注释繁多，敬请谅解。 
20191203：目前上传的是整体项目文件，作为项目文件在spyder或pycharm等中打开即可使用。日后再打包。
 
## 1. 架构

/chinesechatterbot  
--||response_adapter：应答逻辑接口  
--||--__init__.py  
--||--match_based.py：继承父类，基于匹配检索的应答逻辑类。  
--||--response_adapter.py：父类，可拓展。日后可拓展基于知识图谱、情绪识别等的应答逻辑。  
|--__init__.py  
|--chatterbotbody.py：chatterbot主体，主程序请在这里运行。  
|--preparecorpus.py：载入语料请在这里运行。  
|--MongoDBstorage.py：数据库接口，采用MongoDB，当时没有考虑代码复用，就没有写拓展……  
|--conversation.py：定义Statement类。本包基本数据结构。  
|--response_selection.py：选择候选应答函数，被response_adapter调用。  
|--compare.py：计算语句相似性函数。  
|--search.py：定义search类。搜索数据库，被response_adapter调用。  
|--simhash.py：simhash类。被match_based调用。  
|--utils.py：其它。  
说明:  
当前实现的应答逻辑接口MatchBased类采用[simhash](https://blog.csdn.net/Daverain/article/details/80919418)计算语句相似性。


## 2. 语料库训练
### 数据库

暂只实现MongoDB数据库，该非关系型数据库搭建方便、界面友好，容易上手，建议下载。  
[MongoDB安装教程](https://www.runoob.com/mongodb/mongodb-window-install.html)  
[MongoDB可视化界面compass下载地址](https://www.mongodb.com/download-center/compass)  
### 语料库

来自[中文公开聊天语料库](https://github.com/codemayq/chinese_chatbot_corpus)。  
按照该git项目生成txt文档，将该txt文档目录传入preparecorpus.py中CorpusLoader类。载入及训练方法已在preparecorpus.py文件中写明。  
>注意：建议先加载chatterbot.txt和qingyun.txt语料库，训练过程较短；微博和贴吧语料巨大且噪音多，训练从半天到一天不等，训练时务必开启loadCorpus函数filtertrash参数。

## 3. 开始对话

进入chatterbotbody.py中，一句简单的get_response(input)即可开始对话！  
样例：  
>>You: 你好  
chatbot.name: 你好吗  
You: 我不好  
chatbot.name: 不好就不好啦，说这么大声是要全世界的人都听到吗  
You: 我难过呀  
chatbot.name: 慧慧一直都是一个人，特别害怕孤单  
You: 你没有生命，也没有情绪，怎么会害怕孤单呢  
chatbot.name: 切，这么点事会怕？  
You: 我也不怕孤独，只怕自己不在前进  
chatbot.name: 你不会孤独的  

如果需要在控制台输出对话日志进行调试，请在实例化chatterbotbody.py中的chatbot类时传入参数showlog=True。
