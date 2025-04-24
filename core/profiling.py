import time
import functools
import logging

logger = logging.getLogger(__name__)

def profile_endpoint(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        response = view_func(request, *args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log the execution time
        logger.info(
            f'API Endpoint: {request.path} | Method: {request.method} | Time: {execution_time:.4f}s'
        )
        
        # Add profiling info to response headers
        response['X-Execution-Time'] = f'{execution_time:.4f}s'
        
        return response
    return wrapper