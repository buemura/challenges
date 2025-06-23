import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceManager:
    def __init__(self):
        self.resources = []
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info("Entering ResourceManager context.")
        return self

    def add_resource(self, name, resource):
        """Registers a resource that has open()/close() methods."""
        try:
            if hasattr(resource, "open"):
                resource.open()
                logger.info(f"Resource '{name}' opened.")
            self.resources.append((name, resource))
            return resource
        except Exception as e:
            logger.error(f"Failed to open resource '{name}': {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Exiting ResourceManager context.")
        for name, resource in reversed(self.resources):
            try:
                if hasattr(resource, "close"):
                    resource.close()
                    logger.info(f"Resource '{name}' closed.")
            except Exception as e:
                logger.error(f"Error closing resource '{name}': {e}")
        duration = time.time() - self.start_time
        logger.info(f"Context duration: {duration:.4f} seconds")
        return False  # Don't suppress exceptions


class FakeDatabase:
    def open(self):
        logger.info("Database connection established.")

    def close(self):
        logger.info("Database connection closed.")

    def query(self, sql):
        logger.info(f"Running query: {sql}")
        return "query result"

class FakeAPI:
    def open(self):
        logger.info("API session started.")

    def close(self):
        logger.info("API session ended.")

    def fetch_data(self):
        logger.info("Fetching data from API...")
        return {"data": 123}


# Main test
if __name__ == "__main__":
    with ResourceManager() as manager:
        db = manager.add_resource("fake_db", FakeDatabase())
        api = manager.add_resource("fake_api", FakeAPI())

        result = db.query("SELECT * FROM users")
        data = api.fetch_data()

        logger.info(f"Query Result: {result}")
        logger.info(f"API Data: {data}")