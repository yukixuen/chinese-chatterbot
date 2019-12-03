# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 17:22:50 2019

@author: zys
"""


def get_most_frequent_response(input_statement, response_list, storage=None,logger=None,**kwargs):
    """
    :param input_statement: A statement, that closely matches an input to the chat bot.
    :type input_statement: Statement

    :param response_list: A list of statement options to choose a response from.
    :type response_list: list

    :param storage: An instance of a storage adapter to allow the response selection
                    method to access other statements if needed.
    :type storage: StorageAdapter

    :return: The response statement with the greatest number of occurrences.
    :rtype: Statement
    """
    matching_response = None
    occurrence_count = -1

    #logger = logging.getLogger(__name__)
    logger.info('Selecting response with greatest number of occurrences.')

    for statement in response_list:
        count = len(list(storage.filter(
            text=statement.text,
            in_response_to=input_statement.in_response_to)
        ))

        # Keep the more common statement
        if count >= occurrence_count:
            matching_response = statement
            occurrence_count = count

    # Choose the most commonly occuring matching response
    return matching_response


def get_first_response(input_statement, response_list, storage=None,logger=None,**kwargs):
    """
    :param input_statement: A statement, that closely matches an input to the chat bot.
    :type input_statement: Statement

    :param response_list: A list of statement options to choose a response from.
    :type response_list: list

    :param storage: An instance of a storage adapter to allow the response selection
                    method to access other statements if needed.
    :type storage: StorageAdapter

    :return: Return the first statement in the response list.
    :rtype: Statement
    """
    #logger = logging.getLogger(__name__)
    logger.info('Selecting first response from list of {} options.'.format(
        len(response_list)
    ))
    return response_list[0]


def get_random_response(input_statement, response_list, storage=None,logger=None,**kwargs):
    """
    :param input_statement: A statement, that closely matches an input to the chat bot.
    :type input_statement: Statement

    :param response_list: A list of statement options to choose a response from.
    :type response_list: list

    :param storage: An instance of a storage adapter to allow the response selection
                    method to access other statements if needed.
    :type storage: StorageAdapter

    :return: Choose a random response from the selection.
    :rtype: Statement
    """
    from random import choice
    #logger = logging.getLogger(__name__)
    logger.info('Selecting a response from list of {} options.'.format(
        len(response_list)
    ))
    return choice(response_list)

def get_most_confident_response(input_statement, response_list,storage=None,logger=None,topk=1,factor='big'):
    # factor取决于compare_method，越小越相似'small'还是越大越相似'big'
    # topk 取最相似的k个句子
    import heapq
    scores = []
    for statement in response_list:
        scores.append(statement.confidence)
    results = []
    if factor=='big':
        for index in list(map(scores.index, heapq.nlargest(topk, scores))):
            results.append(response_list[index])
    elif factor=='small':
        for index in list(map(scores.index, heapq.nsmallest(topk, scores))):
            results.append(response_list[index])
    return results