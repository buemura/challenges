from inspect import signature, ismethod
from typing import Any, Dict

# Registry to store classes
class_registry: Dict[str, type] = {}


# Custom exception for contract violations
class ContractViolationError(TypeError):
    pass


# Metaclass that enforces API contract and handles registration
class ContractEnforcer(type):
    required_methods = {
        'run': ['self'],
    }
    required_class_attrs = ['version']

    def __init__(cls, name, bases, namespace):
        # Skip base class checks
        if not bases:
            return super().__init__(name, bases, namespace)

        # Check for required methods
        for method_name, expected_args in ContractEnforcer.required_methods.items():
            method = namespace.get(method_name) or getattr(cls, method_name, None)
            if not callable(method):
                raise ContractViolationError(
                    f"Class '{name}' must define method '{method_name}({', '.join(expected_args)})'"
                )

            # Check method signature
            sig = signature(method)
            actual_args = list(sig.parameters.keys())
            if actual_args != expected_args:
                raise ContractViolationError(
                    f"Method '{method_name}' in class '{name}' must have arguments {expected_args}, "
                    f"but has {actual_args}"
                )

        # Check for required class attributes
        for attr in ContractEnforcer.required_class_attrs:
            if not hasattr(cls, attr):
                raise ContractViolationError(
                    f"Class '{name}' must define class attribute '{attr}'"
                )

        # Register class
        class_registry[name] = cls

        print(f"[INFO] Registered class: {name}")
        super().__init__(name, bases, namespace)


# Example base class using the metaclass
class BasePlugin(metaclass=ContractEnforcer):
    pass


# ✅ This class will work
class MyPlugin(BasePlugin):
    version = "1.0"

    def run(self):
        print("Running MyPlugin")


# # ❌ This class will raise a ContractViolationError (no `run` method)
# class BadPlugin(BasePlugin):
#     version = "1.0"

# # ❌ This class will raise a ContractViolationError (missing `version`)
# class AnotherBadPlugin(BasePlugin):
#     def run(self):
#         print("Oops")

# ✅ Runtime check: Instantiate and run
plugin = MyPlugin()
plugin.run()

print(f"\nClass Registry: {class_registry}")
