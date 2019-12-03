# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 13:11:58 2019

@author: zys
"""

from chinesechatterbot import response_selection
class ResponseAdapter(object):
    """
    This is an abstract class that represents the interface
    that all logic adapters should implement.

    :param search_method_name: The name of the search algorithm that should
        be used to search for close matches to the provided input.
        Defaults to the value of ``Search.name``.

    :param maximum_similarity_threshold:
        The maximum amount of similarity between two statement that is required
        before the search process is halted. The search for a matching statement
        will continue until a statement with a greater than or equal similarity
        is found or the search set is exhausted.
        Defaults to 0.95

    :param response_selection_method:
          The a response selection method.
          Defaults to ``get_first_response``
    :type response_selection_method: collections.abc.Callable

    :param default_response:
          The default response returned by this logic adaper
          if there is no other possible response to return.
    :type default_response: str or list or tuple
    """
    name = "ResponseAdapter"
    def __init__(self, chatbot,**kwargs):
        self.chatbot = chatbot
        self.minimum_similarity_threshold = kwargs.get(
            'minimum_similarity_threshold', 0.90
        )
        # By default, select the first available response
        select_response = kwargs.get(
            'response_selection_method',
            'get_random_response'
        )
        try:
            self.select_response = getattr(response_selection,select_response)
        except:
            self.chatbot.logger.error("Unknown select_response was selected.")
            import sys
            sys.exit("Exit this process.")

        default_responses = kwargs.get('default_response', ['抱歉，恐怕我不太明白。','人类的对话过于复杂，我感到迷惑，或许你愿意教教我？'])
        # Convert a single string into a list
        if isinstance(default_responses, str):
            default_responses = [
                default_responses
            ]        
        self.default_responses = [
            default for default in default_responses
        ]

    def regenerate(self,**kwargs):
        """
            response_adapter生成self.searchmethod
            参数：search_method_name
        """
        
        
    
    def can_process(self, statement):
        """
        A preliminary check that is called to determine if a
        response adapter can process a given statement. By default,
        this method returns true but it can be overridden in
        child classes as needed.

        :rtype: bool
        """
        return True

    def process(self, statement, additional_response_selection_parameters=None):
        """
        Override this method and implement your logic for selecting a response to an input statement.

        A confidence value and the selected response statement should be returned.
        The confidence value represents a rating of how accurate the logic adapter
        expects the selected response to be. Confidence scores are used to select
        the best response from multiple logic adapters.

        The confidence value should be a number between 0 and 1 where 0 is the
        lowest confidence level and 1 is the highest.

        :param statement: An input statement to be processed by the logic adapter.
        :type statement: Statement

        :param additional_response_selection_parameters: Parameters to be used when
            filtering results to choose a response from.
        :type additional_response_selection_parameters: dict

        :rtype: Statement
        """
        raise self.AdapterMethodNotImplementedError()

    def get_default_response(self, input_statement):
        """
        This method is called when a logic adapter is unable to generate any
        other meaningful response.
        参数：input_statement: Statement类
        """
        from random import choice
        
        if len(input_statement.in_response_to)<15:
            response = input_statement.in_response_to.rstrip("".join(self.chatbot.signstopword)) + "？"
        elif self.default_responses:
            response = choice(self.default_responses)
        else:
            response = input_statement.in_response_to.rstrip("".join(self.chatbot.signstopword)) + "？"

        self.chatbot.logger.info(
            'No known response to the input was found. Selecting a default response.'
        )

        # Set confidence to zero because a random response is selected
        input_statement.confidence = 0
        input_statement.text = response

        return input_statement
        # 返回写了answer结果的input_statement
'''
    @property
    def class_name(self):
        """
        Return the name of the current logic adapter class.
        This is typically used for logging and debugging.
        """
        return str(self.__class__.__name__)
        '''