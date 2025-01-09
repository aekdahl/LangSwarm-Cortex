class CapabilityRegistry:
    """
    Centralized registry for managing agent capabilities.
    """
    def __init__(self):
        self.capabilities = {}

    def register_capability(self, capability):
        """
        Register a new capability in the registry.
        """
        self.capabilities[capability.name] = capability

    def get_capability(self, capability_name):
        """
        Retrieve a capability by name.
        """
        return self.capabilities.get(capability_name, None)

    def list_capabilities(self):
        """
        List all registered capabilities.
        """
        return [{"name": name, "description": cap.description} for name, cap in self.capabilities.items()]
