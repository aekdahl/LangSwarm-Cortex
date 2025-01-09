class BaseCapability:
    """
    Base class for agent capabilities.
    """
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def use(self, *args, **kwargs):
        """Override this method to execute the capability."""
        raise NotImplementedError("This method should be implemented in a subclass.")

    def run(self, *args, **kwargs):
        """Redirects to the `use` method for compatibility."""
        return self.use(*args, **kwargs)
