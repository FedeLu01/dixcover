import json
import logging
import datetime

class StructuredLogger:
    
    def __init__(self, logger_name='StructuredLogger'):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG) # Configuration to capture all levels of logs
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    
    def _log(self, level, message, **kwargs):
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'level': level.upper(),
            'message': message,
            **kwargs
        }
        json_log = json.dumps(log_entry)
        getattr(self.logger, level)(json_log) # Invoke the method corresponding to the level
            
    
    def info(self, message, **kwargs):
        self._log('info', message, **kwargs)
        
    def warning(self, message, **kwargs):
        self._log('warning', message, **kwargs)
        
    def error(self, message, **kwargs):
        self._log('error', message, **kwargs)
        
    def debug(self, message, **kwargs):
        self._log('debug', message, **kwargs)
        
app_logger = StructuredLogger('DixcoverLogger')
