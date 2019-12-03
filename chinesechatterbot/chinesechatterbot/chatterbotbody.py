# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 09:41:52 2019

@author: zys
"""
"""
    Chinese chatterbot
"""
import logging
from chinesechatterbot.MongoDBstorage import MongoDatabaseAdapter
from jieba import analyse
import jieba.posseg as pseg

class chatbot(object):
    def __init__(self, name,**kwargs):
        '''
        参数: 
            name: chatbot's name: str
            storage_adapter: 储存数据库: str
            database_uri: 数据库接口地址: str
            showlog: 是否控制台显示日志: True/False
            response_adapter: chatbot回应逻辑: list, 每项形如match_based.MatchBased
            response_adapter initialize参数:
                    mininum_silarity_threshold
                    response_selection_method
                    default_response
        '''
        self.name = name
        storage_adapter = kwargs.pop('storage_adapter','MongoDatabaseAdapter')
        database_uri = kwargs.pop('database_uri','mongodb://localhost:27017/chatterbot-database')
        if storage_adapter=='MongoDatabaseAdapter':
            self.storage = MongoDatabaseAdapter(database_uri)
        else:
            print("ERROR:数据库类型尚未支持。")
        
        response_adapter =  kwargs.pop('response_adapter',['match_based.MatchBased'])
        self.response_adapter = []
        from chinesechatterbot.utils import import_module
        dotted_path = "chinesechatterbot.response_adapter"
        # 实例化response_adapter列表中所有adapter
        for name in response_adapter:
            Class = import_module(dotted_path+'.'+name)
            self.response_adapter.append(Class(self,**kwargs))
        
        self.signstopword = []
        with open(r".\signstopword.txt","r",encoding="utf-8") as f:
            while True:
                line = f.readline()
                if line:
                    self.signstopword.append(line.strip())
                else:
                    break
        self.signstopword_withoutsome = [word for word in self.signstopword if word not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPGRSTUVWXYZ。，！？']
        
        self.stopword = []
        with open(r".\stopword.txt","r",encoding="utf-8") as f:
            while True:
                line = f.readline()
                if line:
                    self.stopword.append(line.strip())
                else:
                    break        
        
        showlog = kwargs.get('showlog',False)
        if showlog:
            logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')            
            self.logger = logging.getLogger(__name__)
        else:
            logger = logging.getLogger(__name__)
            logger.setLevel(level = logging.INFO)
            if not logger.handlers: # 避免日志重复
                handler = logging.FileHandler("log.txt") # 存在chinesechatterbot\log.txt
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            self.logger = logger
        
    class ChatBotException(Exception):
        pass
    
    def preprocess(self,sentence):
        # 清洗chatbot收到的输入语句，该输入语句待查询
        # 和preparecorpus.py中的预处理一致，和Statement数据结构一致
        from chinesechatterbot import simhash
        strip = ''.join(self.signstopword_withoutsome)
        in_response_to = sentence.strip(strip+' ') # +' '清洗掉句首句尾的空白字符
        if len(in_response_to)<50:
            keyword_in_response_to = analyse.tfidf(in_response_to,topK=10)
        else:
            keyword_in_response_to = analyse.textrank(in_response_to,topK=10)
        tags_in_response_to = [flag for word,flag in pseg.cut(in_response_to)]
        qhash = simhash.simhash(keyword_in_response_to).simhashindex()
        qhash = [None,str(qhash)][qhash > 0]
        self.logger.info("Input sentence:{},keywords extracted:{}".format(in_response_to,keyword_in_response_to))
        return (in_response_to,keyword_in_response_to,tags_in_response_to,qhash)
    
    def get_response(self, statement=None, **kwargs):
        """
        Return the bot's response based on the input.

        :param statement: A string.
        :returns: A response to the input.
        :rtype: Statement

        :param additional_response_selection_parameters: Parameters to pass to the
            chat bot's response adapters to control response selection.
        :type additional_response_selection_parameters: dict
        :including compare_method, search_method_name, page_size,order_by
        """
        Statement = self.storage.get_statement_model()

        additional_response_selection_parameters = kwargs.pop('additional_response_selection_parameters', {})

        if isinstance(statement, str):
            # 若statement是字符串
            in_response_to,keyword_in_response_to,tags_in_response_to,simhash_in_response_to = self.preprocess(statement)
        else:
            raise self.ChatBotException(
                'A string argument is required as input.'
            )
            self.logger.warning("get_response failed: A string argument is required as input.")

        input_statement = Statement(in_response_to=in_response_to,
                                    keyword_in_response_to=keyword_in_response_to,
                                    tags_in_response_to=tags_in_response_to,
                                    simhash_in_response_to=simhash_in_response_to)
        response = self.generate_response(input_statement, additional_response_selection_parameters)
        # response即为chatbot对input的answer
        
        # 存储response到数据库(generate_response中已改response.storage)
        response.save()
        
        '''
        # Update any response data that needs to be changed
        if persist_values_to_response:
            for response_key in persist_values_to_response:
                response_value = persist_values_to_response[response_key]
                if response_key == 'tags':
                    input_statement.add_tags(*response_value)
                    response.add_tags(*response_value)
                else:
                    setattr(input_statement, response_key, response_value)
                    setattr(response, response_key, response_value)

        if not self.read_only:
            self.learn_response(input_statement)

            # Save the response generated for the input
            self.storage.create(**response.serialize())
        '''
        return response.text

    def generate_response(self, input_statement, additional_response_selection_parameters=None):
        """
        Return a response based on a given input statement.

        :param input_statement: Statement type.
        
        :additional_response_selection_parameters
        :dict
        :including compare_method, search_method_name, page_size,order_by
        """
        Statement = self.storage.get_statement_model()

        results = []
        result = None
        max_confidence = -1

        for adapter in self.response_adapter:
            if adapter.can_process(input_statement):
                adapter.regenerate(**additional_response_selection_parameters)
                    # 传入参数：search_method_name
                output = adapter.process(input_statement, 
                        additional_response_selection_parameters)
                    # 传入参数：compare_method,page_size,order_by
                if isinstance(output,list):
                    results.extend(output)
                if isinstance(output,Statement):
                    results.append(output)
                
                if isinstance(output,Statement):
                    self.logger.info(
                            '{} selected "{}" as a response with a confidence of {}'.format(
                            adapter.name, output.text, output.confidence
                            )
                        )
                    if output.confidence > max_confidence:
                        result = output
                        max_confidence = output.confidence                    
                elif isinstance(output,list):
                    for item in output:
                        self.logger.info(
                            '{} selected "{}" as a response with a confidence of {}'.format(
                            adapter.name, item.text, item.confidence
                            )
                        )                    
                        if item.confidence > max_confidence:
                            result = item
                            max_confidence = item.confidence

            else:
                self.logger.info(
                    'Not processing the statement using {}'.format(adapter.name)
                )


        class ResultOption:
            def __init__(self, statement, count=1):
                self.statement = statement
                self.count = count

        # If multiple adapters agree on the same statement,
        # then that statement is more likely to be the correct response
        if len(results) >= 3:
            result_options = {}
            for result_option in results:
                result_string = result_option.text + ':' + (result_option.in_response_to)

                if result_string in result_options:
                    result_options[result_string].count += 1
                    if result_options[result_string].statement.confidence < result_option.confidence:
                        result_options[result_string].statement = result_option
                else:
                    result_options[result_string] = ResultOption(
                        result_option
                    )

            most_common = list(result_options.values())[0]

            for result_option in result_options.values():
                if result_option.count > most_common.count:
                    most_common = result_option

            if most_common.count > 1:
                result = most_common.statement

        input_statement.text = result.text
        input_statement.keyword_text = result.keyword_text
        input_statement.tags_text = result.tags_text
        input_statement.simhash_text = result.simhash_text
        response = input_statement
        response.persona = self.name
        response.source = result.source
        
        response = Statement(**response.serialize())
        response.confidence = result.confidence
        response.storage = self.storage.dialogues
        
        return response



if __name__ == '__main__':
    mychatbot = chatbot("default",
                        database_uri='mongodb://localhost:27017/mini-chatterbot-database',
                        response_selection_method='get_random_response',
                        showlog=False)
    #get = mychatbot.get_response('你会说什么话',additional_response_selection_parameters={'compare_method':'hash_similarity'})
    # chatterbot数据库还应该做一个去重功能，还没做
    # chatterbot还应该同一问句不能总是只产生一种回答
    # 中文里怎么识别“不会抽烟”和“抽烟”。 “不好笑”被分成“不好”“笑”

    print('Type something to begin...')
  
    while True:
        try:
            user_input = input('You:')
    
            bot_response = mychatbot.get_response(user_input)
    
            print(mychatbot.name+":"+bot_response)
    
        # Press ctrl-c or ctrl-d on the keyboard to exit
        except (KeyboardInterrupt, EOFError, SystemExit):
            break
