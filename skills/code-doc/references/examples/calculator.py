"""
Example calculator module.
Provides basic mathematical operations.
"""

from typing import Union, List
import math


class Calculator:
    """
    A simple calculator class that performs basic arithmetic operations.
    
    This calculator supports addition, subtraction, multiplication, division,
    and some advanced mathematical operations.
    """
    
    def __init__(self, precision: int = 2):
        """
        Initialize the calculator.
        
        Args:
            precision: Number of decimal places for results
        """
        self.precision = precision
        self.history: List[str] = []
    
    def add(self, a: float, b: float) -> float:
        """
        Add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Sum of a and b
        """
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = round(a - b, self.precision)
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """
        Divide a by b.
        
        Args:
            a: Numerator
            b: Denominator
            
        Returns:
            Result of division
            
        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = round(a / b, self.precision)
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """Calculate base raised to exponent."""
        result = round(math.pow(base, exponent), self.precision)
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result
    
    @property
    def last_operation(self) -> str:
        """Get the last operation from history."""
        return self.history[-1] if self.history else "No operations yet"
    
    def clear_history(self):
        """Clear the operation history."""
        self.history.clear()


class ScientificCalculator(Calculator):
    """
    Extended calculator with scientific functions.
    
    Inherits from Calculator and adds trigonometric and logarithmic operations.
    """
    
    def sin(self, x: float) -> float:
        """Calculate sine of x (in radians)."""
        return round(math.sin(x), self.precision)
    
    def cos(self, x: float) -> float:
        """Calculate cosine of x (in radians)."""
        return round(math.cos(x), self.precision)
    
    def log(self, x: float, base: float = math.e) -> float:
        """
        Calculate logarithm of x.
        
        Args:
            x: Number to take logarithm of
            base: Logarithm base (default: e for natural log)
            
        Returns:
            Logarithm of x with specified base
        """
        return round(math.log(x, base), self.precision)


def format_result(value: Union[float, int], units: str = "") -> str:
    """
    Format a calculation result for display.
    
    Args:
        value: The numeric value to format
        units: Optional units to append (e.g., 'm', 'kg')
        
    Returns:
        Formatted string representation
    """
    if units:
        return f"{value} {units}"
    return str(value)


def batch_calculate(calculator: Calculator, operations: List[tuple]) -> List[float]:
    """
    Perform multiple calculations in batch.
    
    This function takes a list of operations and executes them sequentially.
    Each operation is a tuple of (operation_name, arg1, arg2).
    
    Args:
        calculator: Calculator instance to use
        operations: List of operation tuples
        
    Returns:
        List of results
        
    Example:
        >>> calc = Calculator()
        >>> ops = [('add', 1, 2), ('multiply', 3, 4)]
        >>> results = batch_calculate(calc, ops)
        >>> results
        [3.0, 12.0]
    """
    results = []
    
    for op_name, *args in operations:
        if len(args) != 2:
            raise ValueError(f"Operation {op_name} requires exactly 2 arguments")
        
        if op_name == 'add':
            results.append(calculator.add(*args))
        elif op_name == 'subtract':
            results.append(calculator.subtract(*args))
        elif op_name == 'multiply':
            results.append(calculator.multiply(*args))
        elif op_name == 'divide':
            results.append(calculator.divide(*args))
        elif op_name == 'power':
            results.append(calculator.power(*args))
        else:
            raise ValueError(f"Unknown operation: {op_name}")
    
    return results
