# example_project Documentation

**Version:** 1.0.0  
**Generated:** 2025-10-20 14:26:20

---

## 📊 Project Statistics

- **Total Files:** 1
- **Total Lines:** 176
- **Total Classes:** 2
- **Total Functions:** 2
- **Avg Complexity:** 5.0
- **Max Complexity:** 8
- **High Complexity Functions:**

## 🏛️ Classes

### `Calculator`

**Defined in:** `calculator.py:10`

**Description:**
> A simple calculator class that performs basic arithmetic operations.

This calculator supports addition, subtraction, multiplication, division,
and some advanced mathematical operations.

**Methods:**
- `__init__()`
- `add()`
- `subtract()`
- `multiply()`
- `divide()`
- `power()`
- `clear_history()`

**Properties:**
- `last_operation`

---

### `ScientificCalculator`

**Inherits from:** `Calculator`
**Defined in:** `calculator.py:91`

**Description:**
> Extended calculator with scientific functions.

Inherits from Calculator and adds trigonometric and logarithmic operations.

**Methods:**
- `sin()`
- `cos()`
- `log()`

---


## ⚡ Functions

### `batch_calculate(calculator, operations) -> List[float]`

**Defined in:** `calculator.py:136`
**Complexity:** 8

**Description:**
> Perform multiple calculations in batch.

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

**Parameters:**
- `calculator`: Calculator
- `operations`: List[tuple]

---

### `format_result(value, units) -> str`

**Defined in:** `calculator.py:120`
**Complexity:** 2

**Description:**
> Format a calculation result for display.

Args:
    value: The numeric value to format
    units: Optional units to append (e.g., 'm', 'kg')
    
Returns:
    Formatted string representation

**Parameters:**
- `value`: Union[float, int]
- `units`: str

---


## 📦 Dependencies

### `calculator.py`

- `math`
- `typing.List`
- `typing.Union`
