import requests, logging, time, traceback, sys


class Manager:
    """
    The Manager class provides a structured approach to managing API interactions.
    It handles instance initialization and logs creation, controls execution flow through the run method, and delegates specific logic to child classes via execute.
    The class also supports API data retrieval with optional JSON parsing and retry mechanisms in get_api_data.
    By encapsulating these operations, Manager promotes code reuse and ensures consistent handling of API requests and responses.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor for Manager class.

        Logs a message indicating that an instance of the class has been created.

        Args:
        - *args: Positional arguments to pass to create_instance.
        - **kwargs: Keyword arguments to pass to create_instance.
        """
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        try:
            self.create_instance(*args, **kwargs)
            self.all_good = True
            logging.info(f"{self.__class__.__name__} instance created")
        except Exception as e:
            logging.error(
                f"Creation of {self.__class__.__name__} failed due to error: {e}"
            )

    def create_instance(self, *args, **kwargs):
        """
        Placeholder method that should be overridden by subclasses.

        Args:
        - *args: Positional arguments.
        - **kwargs: Keyword arguments.

        Raises:
        - NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses should implement create_instance method")

    def run(self):
        """
        Executes the main logic of the Manager class.

        This method logs the start and end of execution, and delegates
        the actual execution logic to the `execute` method implemented
        by the child classes.
        """
        class_name = self.__class__.__name__
        logging.info(f"Starting execution in {class_name} class")

        try:
            # Call the implementation provided by the child class
            return self.execute_with_error_handling()
        except Exception as e:
            # Get the function name from the traceback
            function_name = self._get_function_name_from_traceback()
            # Log an error message with the specific function name that raised the error
            logging.error(f"Error occurred in {class_name}.{function_name}: {str(e)}")
        finally:
            logging.info(
                f"Ending execution in {class_name} class. All good state: {self.all_good}"
            )

    def _get_function_name_from_traceback(self):
        """
        Helper method to get the name of the function where the exception occurred.
        """
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback_details = traceback.extract_tb(exc_tb)
        filename, line_num, func_name, line_text = traceback_details[-1]

        return func_name

    def execute_with_error_handling(self):
        """
        Wrapper method to call the child class execute method and handle exceptions.
        """
        try:
            return self.execute()
        except Exception as e:
            raise e

    def execute(self):
        """
        Placeholder method that should be overridden by subclasses.

        Raises:
        - NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses should implement execute method")

    def get_api_data(
        self,
        base_url,
        success_info,
        params="",
        JSON=False,
        max_retries=10,
        retry_interval=3,
    ):
        """
        Fetches data from an API endpoint using get.

        Args:
        - base_url (str): The base URL of the API endpoint.
        - success_info (str): Information about what data was retrieved, for logging.
        - params (str, optional): Parameters to be passed in the request. Defaults to "".
        - JSON (bool, optional): Whether the response is expected to be JSON. Defaults to False.
        - max_retries (int, optional): Maximum number times the get call can be executed
        - retry_intervals (int): Gap in seconds to wait between each attempt if 202 Accepeted Status

        Returns:
        - dict or str: The parsed JSON response if JSON is True, otherwise the raw response content as a string.
                      Returns "Error" if an exception occurs.
        """
        try:
            # Make the request with the base_url and params
            response = requests.get(base_url, params=params)

            for _ in range(max_retries):
                response = requests.get(base_url, params=params)

                if response.status_code == 200:
                    result = response.json() if JSON else response.content
                    logging.info(success_info)
                    return result

                elif response.status_code == 202:
                    logging.info(
                        f"Request accepted. Waiting for data to be available..."
                    )
                    time.sleep(retry_interval)

                else:
                    logging.error(
                        f"Request failed with status code {response.status_code}"
                    )
                    return "Error"

        except Exception as e:
            # Log the error and return "Error" as a placeholder
            logging.error(f"Error retrieving data: {e}")
            return "Error"
