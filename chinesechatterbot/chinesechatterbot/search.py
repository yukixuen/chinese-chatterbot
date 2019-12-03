# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 17:17:59 2019

@author: zys
"""

# 所有search类，初始化都应当接受chatbot参数
class Search(object):
    name = "SearchClass"
    def __init__(self,response_adapter):
        self.response_adapter = response_adapter

    def search(self,**kwargs):
        '''
            连接数据库并查询
        '''

class GeneralSearch(Search):
    # 实现倒排索引和近义词检索
    name = "GeneralSearch"
    def __init__(self,response_adapter,**kwargs):
        self.response_adapter = response_adapter
        self.reverseindex = kwargs.get('reverseindex',False)
        self.synonym = kwargs.get('synonym',False)
        
    def search(self,statement,**kwargs):
        # statement: Statement类
        if self.reverseindex==True:
            self.response_adapter.chatbot.logger.info("倒排索引待完善，程序中断，请选择其他选项")
        elif self.synonym==True:
            # 注意不对停用词查询近义词
            self.response_adapter.chatbot.logger.info("近义词添加待完善，程序中断，请选择其他选项")
        else:
            self.response_adapter.chatbot.logger.info("parameters:\treverseindex:False\tsynonym:False")
            keywords = [word for word in statement.keyword_in_response_to if word not in self.response_adapter.chatbot.stopword]
            results = []
            if keywords:
                generator = self.response_adapter.chatbot.storage.filter(keywords=keywords,**kwargs)
                # storage.filter返回了一个生成器，需迭代生成器内的项目
                for item in generator:
                    results.append(item)
                # results中每一个结果是Statement类
            else:
                self.response_adapter.chatbot.logger.info("{}.{} get 0 result.".format(self.response_adapter.name,self.name))
            return results
            
        