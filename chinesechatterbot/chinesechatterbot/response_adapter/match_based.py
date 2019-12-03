# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:12:12 2019

@author: zys
"""
from chinesechatterbot.response_adapter.response_adapter import ResponseAdapter

class MatchBased(ResponseAdapter):
    name = 'MatchBased'
    def __init__(self,chatbot,**kwargs):
        super().__init__(chatbot,**kwargs)
        from chinesechatterbot.search import GeneralSearch
        # MatchBased 该response_adapter默认searchmethod为
        # 倒排索引FALSE且近义词FALSE的GeneralSearch
        self.searchmethod = GeneralSearch(self)
        
        
    def regenerate(self,**kwargs):
        # 实例化特定searchmethod是关键
        '''
        参数：
            search_method_name
            针对 GeneralSearch:
                reversedindex: T/F, 
                synonym: T/F
                倒排索引是否使用；近义词表是否使用
        '''
        super().regenerate(**kwargs)
        search_method_name = kwargs.get(
            'search_method_name',None                  
        )
        if search_method_name=='GeneralSearch':
            # 判断传入参数是否和MatchBased已经生成的GeneralSearch 一致
            # 若一致，不更新self.searchmethod
            # 这一切都是为了防止每次chatbot.get_response()都要重新实例化searchmethod
            # 防止重新加载synonym表
            reverseindex = kwargs.get('reverseindex',False)
            synonym = kwargs.get('synonym',False)
            if reverseindex==self.searchmethod.reverseindex and synonym==self.searchmethod.synonym:
                pass
            else:
                from chinesechatterbot.search import GeneralSearch
                self.searchmethod = GeneralSearch(self,
                                reverseindex=reverseindex,
                                synonym=synonym)
        elif search_method_name:
            dotted_path = "chinesechatterbot.search." + search_method_name
            from utils import import_module
            Class = import_module(dotted_path)
            self.searchmethod = Class(self,**kwargs)
        
        
    def can_process(self,statement):
        return True

    def process(self, statement,additional_response_selection_parameters=None):
        compare_method_name = additional_response_selection_parameters.pop('compare_method','hash_similarity')
        candidates = self.searchmethod.search(statement,**additional_response_selection_parameters)
        # candidates 来源于数据库原始记录，Statement类型
        if statement.simhash_in_response_to==None or not candidates:
            return self.get_default_response(statement)   
        
        from chinesechatterbot.utils import import_module
        dotted_path = "chinesechatterbot.compare." + compare_method_name
        compare_method = import_module(dotted_path)
        confidence = []
        for i,sentence in enumerate(candidates):
            score,factor = compare_method(sentence.simhash_in_response_to,statement.simhash_in_response_to)
            # factor记录该compare_method返回值越大越相似还是越小越相似
            if i==0:
                if factor=='small':
                    self.chatbot.logger.info("{} score: the smaller, the more similar".format(compare_method_name))
                    state = 0
                if factor=='big':
                    self.chatbot.logger.info("{} score: the greater, the more similar".format(compare_method_name))
                    state = 1
            if state==1:
                if score>=self.minimum_similarity_threshold:
                    sentence.confidence = score
                    confidence.append(sentence)
            elif score<=(1-self.minimum_similarity_threshold)*100:
                sentence.confidence = score
                confidence.append(sentence)
        if confidence:
            return self.select_response(statement,confidence,storage=self.chatbot.storage,logger=self.chatbot.logger)
        else:
            return self.get_default_response(statement)
            