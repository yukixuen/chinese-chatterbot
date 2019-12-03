# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 16:16:05 2019

@author: zys
"""
from chinesechatterbot.conversation import Statement
from jieba import analyse
import jieba.posseg as pseg

import json  
from datetime import date, datetime
  
class DateEncoder(json.JSONEncoder):  
    def default(self, obj):  
        if isinstance(obj, datetime):  
            return obj.strftime('%Y-%m-%d %H:%M:%S')  
        elif isinstance(obj, date):  
            return obj.strftime("%Y-%m-%d")  
        else:  
            return json.JSONEncoder.default(self, obj) 

class CorpusLoader(object):
    # 中文语料加载器
    # 初始化后调用loadCorpus(注意是否filtertrach)来完成所有
    #若语料选择生成json文件，则日后导入chatterbot数据库，date字段的类型是string而非ISOdate
        #使用MongoDB查询数据时，date字段要用string和ISOdate类型各查一遍，结果综合
    def __init__(self,chatbot,**kwargs):
        """
            需给出chatbot,wd语料地址,source加载语料文档名(.txt)和savepath(如果将语料存为json)
        """
        import re
        self.chatbot = chatbot
        self.wd = kwargs.get('wd',None)
        
        pattern= r'(\w+).txt'
        self.source = re.match(pattern,kwargs.get('source',None)).groups()[0]
        self.sourcefile = self.wd + '\\' + kwargs.get('source',None)
        self.savepath = kwargs.get('savepath',None)
        self.corpusdata = []
        self.corpusjson = []
        self.trash = []
    
    def readtxt(self,filtertrash):
        print("Read corpus txtfile:")
        try:
            with open(self.sourcefile,'r') as file:
                f = file.readlines()
                count = 0
                for line in f:
                    try:
                        line = line.strip()
                        pair = line.split('\t')
                        if filtertrash:
                            Qdiverse = set([char for char in pair[0] if char not in self.chatbot.signstopword])
                            # pair中问句里非符号停用词的种类够多，才保留，否则清洗掉
                            Adiverse = set([char for char in pair[1] if char not in self.chatbot.signstopword])                        
                            if len(Qdiverse)>=5 or len(Adiverse)>=5:
                                self.corpusdata.append(pair)
                            else:
                                self.trash.append(pair)
                                count = count + 1
                        else:
                            self.corpusdata.append(pair)
                    except:
                        print("one error when read.txt")
                        pass
        except UnicodeDecodeError:
            import codecs
            with codecs.open(self.sourcefile,'r',encoding='utf-8') as file:
                f = file.readlines()
                count = 0
                for line in f:
                    try:
                        line = line.strip()
                        pair = line.split('\t')
                        if filtertrash:
                            Qdiverse = set([char for char in pair[0] if char not in self.chatbot.signstopword])
                            # pair中问句里非符号停用词的种类够多，才保留，否则清洗掉
                            Adiverse = set([char for char in pair[1] if char not in self.chatbot.signstopword])
                            if len(Qdiverse)>5 or len(Adiverse)>5:
                                self.corpusdata.append(pair)
                            else:
                                self.trash.append(pair)
                                count = count + 1
                        else:
                            self.corpusdata.append(pair)
                    except:
                        print('one error when read.txt')
                        pass
        print("Completed. Drop {} records because of chatbot.signstopword.".format(count))
    
    def viewCorpusFilterred(self):
        return self.trash
    
    def extractkeyword(self,sentence):
        if len(sentence)<50:
            keyword = analyse.tfidf(sentence,topK=10)
        else:
            keyword = analyse.textrank(sentence,topK=10)
        return keyword
    
    def prepocess(self):
        from chinesechatterbot import simhash
        for pair in self.corpusdata:
            in_response_to = self.clean(pair[0])
            keyword_in_response_to = self.extractkeyword(in_response_to)
            tags_in_response_to = [flag for word,flag in pseg.cut(in_response_to)]
            text = self.clean(pair[1])
            keyword_text = self.extractkeyword(text)
            tags_text = [flag for word,flag in pseg.cut(text)]
            qhash = simhash.simhash(keyword_in_response_to).simhashindex()
            qhash = [None,str(qhash)][qhash > 0]
            ahash = simhash.simhash(keyword_text).simhashindex()
            ahash = [None,str(ahash)][ahash > 0]
            yield Statement(text.replace(" ",""),in_response_to.replace(" ",""),
                            # replace为了防止原始语料用空白分词
                                  keyword_in_response_to=keyword_in_response_to,
                                  tags_in_response_to=tags_in_response_to,
                                  keyword_text=keyword_text,
                                  tags_text=tags_text,
                                  simhash_text=ahash,
                                  simhash_in_response_to=qhash,
                                  source=self.source,
                                  persona=self.chatbot.name)
            
    def clean(self,text):
        strip = ''.join(self.chatbot.signstopword_withoutsome)
        return text.strip(strip) # 不用加' '清洗空白字符是因为preprocess()中已经有replace(" ","")
            
    def loadCorpus(self,jsonordb=1,filtertrash=False):
        # jsonordb=1 存储为json; jsonordb=0 直接存储入数据库
        from chinesechatterbot.utils import print_progress_bar
        self.readtxt(filtertrash)
        if jsonordb==0:
            print("Directly saved to database.")
            for iteration_count,item in enumerate(self.prepocess()):
                item.storage = self.chatbot.storage.trains
                item.save()
                print_progress_bar("Saving into {}.trains".format(self.chatbot.storage.database_uri),
                        iteration_count+1,
                        len(self.corpusdata)
                        )
                
        elif jsonordb==1:
            import codecs
            #import json
            #需要注意，生成的json文件如果日后导入chatterbot数据库，date字段的类型是string而非ISOdate
            #使用MongoDB查询数据时，date字段要用string和ISOdate类型各查一遍，结果综合
            with codecs.open(self.savepath,"w+","utf-8") as f1:
                for iteration_count,item in enumerate(self.prepocess()):
                    content = json.dumps(item.serialize(),ensure_ascii = False,cls=DateEncoder)#DateEncoder为了防止日期无法serialize，见本文档开头
                    f1.write(content)
                    f1.write('\n')
                    print_progress_bar("Saving into {}".format(self.savepath),
                        iteration_count+1,
                        len(self.corpusdata)
                        )
                
        else:
            print("Error arguments with loadCorpus's jsonordb")

if __name__=='__main__':
    from chinesechatterbot.chatterbotbody import chatbot
    mychatbot = chatbot("default",database_uri='mongodb://localhost:27017/tieba-chatterbot-database')
<<<<<<< HEAD
    corpusloader = CorpusLoader(mychatbot,source="tieba.txt",
                                wd=r"E:\zzx\Fudan University Life\DataAnalysisPractice\natural language process practice\chinese_chatbot_corpus-master\clean_chat_corpus",
                                savepath=r"E:\zzx\Fudan University Life\DataAnalysisPractice\natural language process practice\chatbot\trial.json")
=======
    corpusloader = CorpusLoader(mychatbot,source="tieba.txt")                               
>>>>>>> bdc5e09926790695598cb03c2bcf20ecaf25bad2
    corpusloader.loadCorpus(0,filtertrash=True) 
    # 注意，准备语料库时要么全部从json导入要么全部直接导入数据库，否则mongodbstorage.filter的时间排序出问题
    print(corpusloader.viewCorpusFilterred()[1:10])
                           
