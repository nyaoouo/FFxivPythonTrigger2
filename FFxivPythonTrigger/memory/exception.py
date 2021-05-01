class WinAPIError(Exception):
    def __init__(self, error_code):
        self.error_code = error_code
        message = 'Windows api error, error_code: {}'.format(self.error_code)
        super(WinAPIError, self).__init__(message)
