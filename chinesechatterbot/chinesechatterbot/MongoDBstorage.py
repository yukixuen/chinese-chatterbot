# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 17:42:51 2019

@author: zys
"""
#import re
class MongoDatabaseAdapter(object):
    def __init__(self,database_uri):
        from pymongo import MongoClient
        from pymongo.errors import OperationFailure
        self.database_uri = database_uri
        self.client = MongoClient(self.database_uri)
        # Increase the sort buffer to 42M if possible
        try:
            self.client.admin.command({'setParameter': 1, 'internalQueryExecMaxBlockingSortBytes': 44040192})
        except OperationFailure:
            pass
        self.database = self.client.get_database()
        self.trains = self.database['trains']
        self.dialogues = self.database['dialogues']
        self.synonyms = self.database['synonyms']
    
    def get_statement_model(self):
        """
        Return the class for the statement model.
        """
        from chinesechatterbot.conversation import Statement

        # Create a storage-aware statement
        statement = Statement
        statement.storage = self # 重写Statement类，否则，statement类的storage为none

        return statement

    def count_tableTrains(self):
        return self.trains.count()
    
    def count_tableDialogues(self):
        return self.dialogues.count()
    
    def count_tableSynonyms(self):
        return self.synonyms.count()

    def mongo_to_object(self, statement_data):
        """
        Return Statement object when given data
        returned from Mongo DB.
        被 get_random调用
        """
        Statement = self.get_statement_model()

        statement_data['id'] = statement_data['_id']

        return Statement(**statement_data)

    def filter(self, **kwargs):
        """
        Returns a list of statements in the database
        that match the parameters specified.
        """
        import pymongo

        page_size = kwargs.pop('page_size', 1000)
        order_by = kwargs.pop('order_by', None)
        #tags = kwargs.pop('tags', [])
        #exclude_text = kwargs.pop('exclude_text', None)
        #exclude_text_words = kwargs.pop('exclude_text_words', [])
        #persona_not_startswith = kwargs.pop('persona_not_startswith', None)
        keywords = kwargs.pop('keywords', None)
        
        if keywords:
            kwargs['keyword_in_response_to'] = {
                    '$in':keywords
                        }
        '''
        if tags:
            kwargs['tags'] = {
                '$in': tags
            }

        if exclude_text:
            if 'text' not in kwargs:
                kwargs['text'] = {}
            elif 'text' in kwargs and isinstance(kwargs['text'], str):
                text = kwargs.pop('text')
                kwargs['text'] = {
                    '$eq': text
                }
            kwargs['text']['$nin'] = exclude_text

        if exclude_text_words:
            if 'text' not in kwargs:
                kwargs['text'] = {}
            elif 'text' in kwargs and isinstance(kwargs['text'], str):
                text = kwargs.pop('text')
                kwargs['text'] = {
                    '$eq': text
                }
            exclude_word_regex = '|'.join([
                '.*{}.*'.format(word) for word in exclude_text_words
            ])
            kwargs['text']['$not'] = re.compile(exclude_word_regex)

        if persona_not_startswith:
            if 'persona' not in kwargs:
                kwargs['persona'] = {}
            elif 'persona' in kwargs and isinstance(kwargs['persona'], str):
                persona = kwargs.pop('persona')
                kwargs['persona'] = {
                    '$eq': persona
                }
            kwargs['persona']['$not'] = re.compile('^bot:*')

        if search_text_contains:
            or_regex = '|'.join([
                '{}'.format(word) for word in search_text_contains.split(' ')
            ])
            kwargs['search_text'] = re.compile(or_regex)
'''

        mongo_ordering = []

        if order_by:

            # Sort so that newer datetimes appear first
            if 'created_at' in order_by:
                order_by.remove('created_at')
                mongo_ordering.append(('created_at', pymongo.DESCENDING, ))

            for order in order_by:
                mongo_ordering.append((order, pymongo.ASCENDING))

        total_statements = self.trains.find(kwargs).count()

        for start_index in range(0, total_statements, page_size):
            if mongo_ordering:
                for match in self.trains.find(kwargs).sort(mongo_ordering).skip(start_index).limit(page_size):
                    yield self.mongo_to_object(match)
            else:
                for match in self.trains.find(kwargs).skip(start_index).limit(page_size):
                    yield self.mongo_to_object(match)
    '''
    def create(self, **kwargs):
        """
        Creates a new statement matching the keyword arguments specified.
        Returns the created statement.
        """
        Statement = self.get_statement_model()

        if 'tags' in kwargs:
            kwargs['tags'] = list(set(kwargs['tags']))

        if 'search_text' not in kwargs:
            kwargs['search_text'] = self.tagger.get_bigram_pair_string(kwargs['text'])

        if 'search_in_response_to' not in kwargs:
            if kwargs.get('in_response_to'):
                kwargs['search_in_response_to'] = self.tagger.get_bigram_pair_string(kwargs['in_response_to'])

        inserted = self.statements.insert_one(kwargs)

        kwargs['id'] = inserted.inserted_id

        return Statement(**kwargs)
    '''
    '''
    def create_many(self, statements):
        """
        Creates multiple statement entries.
        """
        create_statements = []

        for statement in statements:
            statement_data = statement.serialize()
            tag_data = list(set(statement_data.pop('tags', [])))
            statement_data['tags'] = tag_data

            if not statement.search_text:
                statement_data['search_text'] = self.tagger.get_bigram_pair_string(statement.text)

            if not statement.search_in_response_to and statement.in_response_to:
                statement_data['search_in_response_to'] = self.tagger.get_bigram_pair_string(statement.in_response_to)

            create_statements.append(statement_data)

        self.statements.insert_many(create_statements)
        # self.statements是database['statements']，见本文件开头
        '''
    '''
    def update(self, statement):
        data = statement.serialize()
        data.pop('id', None)
        data.pop('tags', None)

        data['search_text'] = self.tagger.get_bigram_pair_string(data['text'])

        if data.get('in_response_to'):
            data['search_in_response_to'] = self.tagger.get_bigram_pair_string(data['in_response_to'])

        update_data = {
            '$set': data
        }

        if statement.tags:
            update_data['$addToSet'] = {
                'tags': {
                    '$each': statement.tags
                }
            }

        search_parameters = {}

        if statement.id is not None:
            search_parameters['_id'] = statement.id
        else:
            search_parameters['text'] = statement.text
            search_parameters['conversation'] = statement.conversation

        update_operation = self.statements.update_one(
            search_parameters,
            update_data,
            upsert=True
        )

        if update_operation.acknowledged:
            statement.id = update_operation.upserted_id

        return statement
    '''
    def get_random(self):
        """
        Returns a random statement from the database
        """
        from random import randint

        count = self.count_tableTrains()

        if count < 1:
            raise self.EmptyDatabaseException()

        random_integer = randint(0, count - 1)

        statements = self.statements.find().limit(1).skip(random_integer)

        return self.mongo_to_object(list(statements)[0])

    def remove(self, statement_text):
        """
        Removes the statement that matches the input text.
        """
        self.statements.delete_one({'text': statement_text})

    def drop(self):
        """
        Remove the database.
        """
        self.client.drop_database(self.database.name)
        
    class EmptyDatabaseException(Exception):
        def __init__(self, message=None):
            default = 'The database currently contains no entries. At least one entry is expected. You may need to train your chat bot to populate your database.'
            super().__init__(message or default)
if __name__ == '__main__':
    # 成功的测试
    mongo = MongoDatabaseAdapter('mongodb://localhost:27017/my-chatterbot-database')
    snew = mongo.get_statement_model()
    print(snew.storage)
    s = snew("我是汪藏海","你是谁",source="trial")
    print(s.storage)
    s.storage = s.storage.dialogues #从数据库中选一个表（集合）
    s.save()
    '''
    from chinesechatterbot.conversation import Statement
    s = Statement("我是汪藏海","你是谁",source="trial")
    s.storage = mongo.dialogues
    print(s.storage)
    s.save()'''