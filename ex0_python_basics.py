# ==============================================================================
# HOW COMMENTING WORKS IN PYTHON
# ==============================================================================
# 1. Single-line comments start with a hashtag (#). Python ignores everything after it.
# 2. Inline comments can be placed at the end of a line of code.
# 3. Multi-line comments can be done using multiple single lines, or triple quotes.
"""
This is a multi-line comment (docstring).
It can span multiple lines.
Python does not execute this text.
"""

# ==============================================================================
# 1. VARIABLE DEFINITIONS
# ==============================================================================
user_name = "Alice"
age = 25
score = 15
pi_value = 3.14
is_active = True

print("--- 1. Variable Definitions ---")
print("User Name:", user_name)
print("Age:", age)
print("Score:", score)
print("Pi Value:", pi_value)
print("Is Active:", is_active)
print()  # Prints a blank line for spacing


# ==============================================================================
# 2. BASIC MATH OPERATIONS
# ==============================================================================
sum_result = 10 + 5              # 15 (Addition)
diff_result = 10 - 5             # 5  (Subtraction)
prod_result = 10 * 5             # 50 (Multiplication)
div_result = 10 / 5              # 2.0 (Division)
exp_result = 10 ** 2             # 100 (Exponentiation)

print("--- 2. Basic Math Operations ---")
print("10 + 5 =", sum_result)
print("10 - 5 =", diff_result)
print("10 * 5 =", prod_result)
print("10 / 5 =", div_result)
print("10 ** 2 =", exp_result)
print()


# ==============================================================================
# 3. LISTS
# ==============================================================================
fruits = ["apple", "banana", "cherry"]
fruits.append("orange")          # Adds orange to the end
first_fruit = fruits[0]          # Accesses the first item

print("--- 3. Lists ---")
print("Full Fruit List:", fruits)
print("First Fruit in List:", first_fruit)
print()


# ==============================================================================
# 4. IMPORTING AND DEFINING FUNCTIONS
# ==============================================================================
import math                      # Importing a complete library
from random import randint       # Importing a specific function

def greet_user(name):            # Defining your own function
    return f"Hello, {name}!"

# Executing the functions
square_root = math.sqrt(16)      
random_num = randint(1, 10)      
welcome_message = greet_user(user_name)

print("--- 4. Importing and Functions ---")
print("Square root of 16:", square_root)
print("Random number between 1 and 10:", random_num)
print("Function output:", welcome_message)
print()


# ==============================================================================
# 5. CONDITIONAL STATEMENTS AND LOOPS
# ==============================================================================
print("--- 5. Conditional Statements and Loops ---")

# IF / ELIF / ELSE
if score > 20:
    print("Condition Result: The score is greater than 20.")
elif score == 15:
    print("Condition Result: The score is exactly 15.")
else:
    print("Condition Result: The score is low.")

# FOR Loop
print("\nRunning FOR Loop:")
for fruit in fruits:
    print(f"- {fruit}")

# WHILE Loop
print("\nRunning WHILE Loop:")
counter = 0
while counter < 3:
    print(f"While counter is at: {counter}")
    counter = counter + 1
