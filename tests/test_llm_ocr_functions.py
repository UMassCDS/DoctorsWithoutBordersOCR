import unittest
from unittest.mock import patch
import logging
from typing import Optional
from requests.models import Response

import openai
from openai import APIConnectionError, AuthenticationError, APIStatusError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIHandler:
    """Process data using AI."""

    MODEL = "gpt-4"

    def __init__(self, openai_key: str) -> None:
        """
        Initialize the class with the OpenAI API key.

        Args:
            openai_key: The API key for accessing the OpenAI service.
        """
        self.openai_key = openai_key
        openai.api_key = self.openai_key

    def query_api(self, query: str) -> Optional[str]:
        """
        Query the AI API.

        Args:
            query: Query to send to the API

        Returns:
            Response message from the API
        """
        logging.info("Querying API...")

        # No need to query the API if there is no query content
        if not query:
            return None

        message = [{"role": "user", "content": query}]

        result = None
        try:
            completion = openai.ChatCompletion.create(
                model=self.MODEL, messages=message
            )
            result = completion.choices[0].message['content']
        except AuthenticationError as ex:
            logger.error("Authentication error: %s", ex)
        except APIConnectionError as ex:
            logger.error("API connection error: %s", ex)
        except APIStatusError as ex:
            logger.error("API status error: %s", ex)

        return result

# Mocking classes for testing
class MockedChoice:
    def __init__(self, content: str) -> None:
        self.message = {"content": content}


class MockedCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [MockedChoice(content)]


class TestAIHandler(unittest.TestCase):

    @patch('openai.ChatCompletion.create')
    def test_query_api(self, mock_create):
        # Mocking the response from OpenAI API
        mock_create.return_value = MockedCompletion("This is a mocked response from AI.")

        # Initialize the handler with a fake API key
        handler = AIHandler(openai_key="fake_api_key")

        # Call the method with a test query
        response = handler.query_api("Test query")

        # Check that the mocked response is returned
        self.assertEqual(response, "This is a mocked response from AI.")

        # Check that the API was called with the correct parameters
        mock_create.assert_called_once_with(
            model="gpt-4", messages=[{"role": "user", "content": "Test query"}]
        )

    @patch('openai.ChatCompletion.create')
    def test_query_api_authentication_error(self, mock_create):
        # Create a mock response object
        mock_response = Response()
        mock_response.status_code = 401  # Unauthorized status code

        # Mock the error
        mock_create.side_effect = AuthenticationError(
            message="Invalid API key",
            response=mock_response,
            body={}
        )

        handler = AIHandler(openai_key="fake_api_key")
        response = handler.query_api("Test query")

        self.assertIsNone(response)
        mock_create.assert_called_once_with(
            model="gpt-4", messages=[{"role": "user", "content": "Test query"}]
        )



