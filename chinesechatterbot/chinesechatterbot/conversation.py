# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 15:51:35 2019

@author: zys
"""

from pytz import UTC
from datetime import datetime
from dateutil import parser as date_parser

class StatementMixin(object):
    """
    This class has shared methods used to
    normalize different statement models.
    """

    statement_field_names = [
        'id',
        'text', # the answer text
        'keyword_text', # the keywordd of the answer text
        'tags_text', # the 词性标注 of the answer text
        'simhash_text', # simhash值用字符串储存因为mongoDB只能处理8位Int
        'source', # 来自训练语料还是对话日志;训练语料显示语料来源
        'persona', # chatbot的名字，personality
        'in_response_to',  # the question in pair sentence
        'keyword_in_response_to', # keywords of the question in pair sentence
        'tags_in_response_to',
        'simhash_in_response_to',
        'created_at',
    ]

    extra_statement_field_names = []

    def get_statement_field_names(self):
        """
        Return the list of field names for the statement.
        """
        return self.statement_field_names + self.extra_statement_field_names

    def get_tags_text(self):
        """
        Return the list of tags for this answer statement.
        """
        return self.tags_text

    def add_tags(self, *tags):
        """
        Add a list of strings to the answer statement as tags.
        """
        self.tags_text.extend(tags)

    def get_tags_in_response_to(self):
        """
        Return the list of tags for this question statement.
        """
        return self.tags_in_response_to

    def add_tags_in_response_to(self, *tags):
        """
        Add a list of strings to the question statement as tags.
        """
        self.tags_in_response_to.extend(tags)
        
    def get_simhash_text(self):
        return self.simhash_text
    
    def get_simhash_in_response_to(self):
        return self.simhash_in_response_to

    def serialize(self):
        """
        :returns: A dictionary representation of the statement object.
        :rtype: dict
        """
        data = {}

        for field_name in self.get_statement_field_names():
            format_method = getattr(self, 'get_{}'.format(
                field_name
            ), None)

            if format_method:
                data[field_name] = format_method()
            else:
                data[field_name] = getattr(self, field_name)

        return data


class Statement(StatementMixin):
    """
    A statement represents a single spoken entity, sentence or
    phrase that someone can say.
    """

    __slots__ = (
        'id',
        'text',
        'keyword_text',
        'tags_text',
        'simhash_text',
        'source',
        'persona',
        'in_response_to',  # the question in pair sentence
        'keyword_in_response_to', # keywords of the question in pair sentence
        'tags_in_response_to',
        'simhash_in_response_to',
        'created_at',
        'confidence',
        'storage',
    )

    def __init__(self, text=None, in_response_to=None, **kwargs):

        self.id = kwargs.get('id',None)
        self.text = kwargs.get('text',text)
        self.keyword_text = kwargs.get('keyword_text', [])
        self.tags_text = kwargs.get('tags_text', [])
        self.simhash_text = kwargs.get('simhash_text',None)
        self.source = kwargs.get('source',None)
        self.persona = kwargs.get('persona', '')
        self.in_response_to = kwargs.get('in_response_to',in_response_to)
        self.keyword_in_response_to = kwargs.get('keyword_in_response_to', [])
        self.tags_in_response_to = kwargs.get('tags_in_response_to', [])
        self.simhash_in_response_to = kwargs.get('simhash_in_response_to',None)
        self.created_at = kwargs.get('created_at', datetime.now())
        try:
            if self.text == None and self.in_response_to == None:
                raise self.StatementGenerationError()
        except self.StatementGenerationError as e:
            print(e)
            import sys
            sys.exit()
            
        
        if not isinstance(self.created_at, datetime):
            self.created_at = date_parser.parse(self.created_at)

        # Set timezone to UTC if no timezone was provided
        if not self.created_at.tzinfo:
            self.created_at = self.created_at.replace(tzinfo=UTC)

        # This is the confidence with which the chat bot believes
        # this is an accurate response. This value is set when the
        # statement is returned by the chat bot.
        self.confidence = 0
        #self.storage = None 
        #避免MongoDBstorage.py中重写Statement的self.storage后，
        #一旦初始化又被self.storage=None覆盖
    
    class StatementGenerationError(Exception): # 一个自定义异常
        def __init__(self):
            super().__init__(self) #初始化父类
            self.errorinfo="<StatementGenerationError>:Statement cannot be generated when both 'text' and 'in_response_to' are None."
        def __str__(self):
            return self.errorinfo

    def __str__(self):
        return self.text

    def __repr__(self):
        return '<Statement text:%s>' % (self.text)

    def save(self):
        """
        Save the statement in the database.
        需要先设置self.storage,不能为none
        初始化self.storage在MongoDBstorage.get_statement_model
        """
        self.storage.insert(self.serialize())
        