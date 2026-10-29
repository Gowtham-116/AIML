import sys

# 1. Primitive Scalar Types
print(f"Integer (0):         {sys.getsizeof(0)} bytes")
print(f"Integer (42):         {sys.getsizeof(4)} bytes")
print(f"Large Integer (2**60): {sys.getsizeof(2**60)} bytes")
print(f"Float (3.14):        {sys.getsizeof(3.14)} bytes")
print(f"Boolean (True):      {sys.getsizeof(True)} bytes")

# 2. String Types (Showing PEP 393 optimization)
print(f"Empty String:        {sys.getsizeof('')} bytes")
print(f"ASCII String ('a'):  {sys.getsizeof('a')} bytes")
print(f"Emoji String ('🐍'):  {sys.getsizeof('🐍')} bytes")

# 3. Collection Types (Empty vs. 1 item)
print(f"Empty List:          {sys.getsizeof([])} bytes")
print(f"List with 1 item:    {sys.getsizeof([1])} bytes")
print(f"Empty Tuple:         {sys.getsizeof(())} bytes")
print(f"Empty Dictionary:    {sys.getsizeof({})} bytes")


import sys
import numpy as np

# Create a list and a NumPy array with 1,000,000 integers
items = 1_000_000
python_list = list(range(items))
numpy_array = np.arange(items, dtype=np.int32) # Uses 4 bytes per integer

# Calculate memory sizes
# System size of the list structure + size of all individual integer objects
list_memory = sys.getsizeof(python_list) + sum(sys.getsizeof(x) for x in python_list)
array_memory = numpy_array.nbytes

print(f"Python List Memory: {list_memory / 1_000_000:.2f} MB")
print(f"NumPy Array Memory: {array_memory / 1_000_000:.2f} MB")



import sys

# Standard Class (Creates a hidden dictionary for every instance)
class StandardPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Optimized Class (Allocates a fixed space like a C struct)
class SlotsPoint:
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

p1 = StandardPoint(1, 2)
p11 = StandardPoint(1, 2)
p2 = SlotsPoint(1, 2)

# Measure memory (including the internal dictionary for the standard class)
p1_size = sys.getsizeof(p1) + sys.getsizeof(p1.__dict__)
p2_size = sys.getsizeof(p2) + sys.getsizeof(p2.__dir__)


print(f"Standard Class Instance: {p1_size} bytes")
print(f"Slots Class Instance:    {p2_size} bytes")


import tracemalloc
import time

# Start tracking memory allocations
tracemalloc.start()

def memory_heavy_operation():
    # Simulate a running loop adding items to a global cache
    cache = []
    for i in range(500_000):
        cache.append(f"string_data_{i}")
    return cache

print("Starting operation...")
start_snapshot = tracemalloc.take_snapshot()

# Run the operation
data_leak = memory_heavy_operation()

end_snapshot = tracemalloc.take_snapshot()

# Compare the snapshots to see the net memory growth
top_stats = end_snapshot.compare_to(start_snapshot, 'lineno')

print("\n--- Top Memory Allocations ---")
for stat in top_stats[:3]:
    print(stat)


import sys

# EFFICIENT: Yields a tuple containing two separate values
def get_squares_generator(n):
    for i in range(n):
        # We yield a tuple: (the original number, the squared number)
        yield i, i ** 2

# Create the generator object
gen_obj = get_squares_generator(100_000)

# Even though it now tracks two pieces of information per iteration,
# the generator container size stays practically identical in memory.
print(f"Generator Object Container Size: {sys.getsizeof(gen_obj)} bytes")

import ctypes


def print_integer_internals(number):
    # 1. Get the raw physical memory address of the object
    memory_address = id(number)

    # 2. In 64-bit Python, ob_size sits exactly 16 bytes after the start address
    # (8 bytes for refcnt + 8 bytes for type pointer)
    ob_size_address = memory_address + 16

    # 3. Read the 8-byte signed integer directly out of that RAM address
    ob_size_value = ctypes.c_ssize_t.from_address(ob_size_address).value

    print(f"Decimal: {number:<15} | RAM Address: {memory_address:<14} | ob_size: {ob_size_value}")


# Test 1: Zero uses 0 chunks
print_integer_internals(0)

# Test 2: Standard small integers fit entirely inside 1 chunk
print_integer_internals(42)

# Test 3: Negative numbers turn the counter negative
print_integer_internals(-42)

# Test 4: Exceeding 2**30 forces Python to allocate a 2nd chunk
print_integer_internals(2 ** 30)

# Test 5: A massive number spanning across multiple chunks
print_integer_internals(2 ** 65)

import ctypes


def inspect_integer_chunks(number):
    memory_address = id(number)

    # 1. Read ob_size to determine how many chunks exist
    ob_size_address = memory_address + 16
    ob_size = ctypes.c_ssize_t.from_address(ob_size_address).value

    # 2. Determine the number of active digit slots to read
    num_chunks = abs(ob_size)

    chunks = []
    # 3. The ob_digit array starts exactly 24 bytes after the object's base address
    # (8 bytes refcnt + 8 bytes type pointer + 8 bytes size counter)
    digit_base_address = memory_address + 24

    for i in range(num_chunks):
        # Each chunk is a 4-byte (32-bit) unsigned integer slot
        chunk_address = digit_base_address + (i * 4)
        chunk_value = ctypes.c_uint32.from_address(chunk_address).value
        chunks.append(chunk_value)

    print(f"Number: {f'2**{number.bit_length()}' if number > 1000 else number}")
    print(f"├── ob_size: {ob_size}")
    if num_chunks == 0:
        print("└── ob_digit chunks: [Empty]")
    else:
        # Convert chunk integers to binary strings padded to 30 bits
        bin_strings = [f"bin({val}) = {val:030b}₂" for val in chunks]
        print(f"└── ob_digit chunks: {chunks}")
        for idx, b_str in enumerate(bin_strings):
            print(f"    └── Chunk [{idx}]: {b_str}")
    print("-" * 60)


# Test 1: Fits in 1 chunk
inspect_integer_chunks(42)

# Test 2: The exact point where a single chunk maxes out (2**30 - 1)
inspect_integer_chunks(1073741823)

# Test 3: Spills across 2 chunks (2**30)
inspect_integer_chunks(1073741824)

# Test 4: A massive number requiring 3 distinct digital slots
inspect_integer_chunks(3 ** 65)

import ctypes


def inspect_string_internals(text):
    memory_address = id(text)

    # 1. In PyASCIIObject, the 'length' field sits 16 bytes after the start address
    length_address = memory_address + 16
    string_length = ctypes.c_ssize_t.from_address(length_address).value

    # 2. Basic ASCII headers consume exactly 48 bytes of structure overhead.
    # The actual text array starts immediately at byte 48.
    character_base_address = memory_address + 48

    char_bytes = []
    for i in range(string_length):
        char_address = character_base_address + i
        # Read each character byte out of RAM
        byte_value = ctypes.c_uint8.from_address(char_address).value
        char_bytes.append(byte_value)

    print(f"String Variable:   '{text}'")
    print(f"├── RAM Address:   {memory_address}")
    print(f"├── Length Field:  {string_length} character(s)")
    print(f"└── Raw Byte Array: {char_bytes} -> {[chr(b) for b in char_bytes]}")
    print("-" * 65)


# Test with simple ASCII text
inspect_string_internals("Python")
inspect_string_internals("RAM")


import ctypes

def get_ref_count(obj):
    # The reference counter sits at the absolute start of the object's memory address (offset 0)
    memory_address = id(obj)
    return ctypes.c_ssize_t.from_address(memory_address).value

# Step 1: Create a brand new unique object
print("--- Creating Data ---")
data_block = ["unique_list_item"]
# Starting reference count is typically 1 (held by variable 'data_block')
print(f"Initial Count: {get_ref_count(data_block)}")

# Step 2: Create a secondary label pointing to the SAME data block
print("\n--- Creating References ---")
alias_1 = data_block
alias_2 = data_block
print(f"Count after assigning aliases: {get_ref_count(data_block)}") # Counter jumps to 3

# Step 3: Remove the pointers using 'del'
print("\n--- Deleting References ---")
del alias_1
print(f"Count after deleting alias_1:  {get_ref_count(data_block)}") # Drops to 2
del alias_2
print(f"Count after deleting alias_2:  {get_ref_count(data_block)}") # Drops back to 1


import sys

# Baseline metadata cost for an empty string
empty_size = sys.getsizeof("")
print(f"Empty String Layout Cost: {empty_size} bytes")

# 1. Latin-1 / ASCII: Adds exactly 1 byte per character
str_ascii = "abcd"
size_ascii = sys.getsizeof(str_ascii)
per_char_ascii = (size_ascii - empty_size) / len(str_ascii)
print(f"ASCII String Size:        {size_ascii} bytes ({per_char_ascii} byte/char)")

# 2. UCS-2 (Non-Latin): Baseline jumps slightly, adds 2 bytes per character
str_hindi = "हिंदी"
size_hindi = sys.getsizeof(str_hindi)
print(f"Hindi String Size:        {size_hindi} bytes (UCS-2 Encoding)")

# 3. UCS-4 (Emoji): Baseline jumps, forces 4 bytes per character
str_emoji = "abcd🐍"
size_emoji = sys.getsizeof(str_emoji)
print(f"Emoji Tax String Size:    {size_emoji} bytes (All 5 chars forced to 4 bytes)")


# These two variables contain identical text content
a = "hello_world"
b = "hello_world"

# Python automatically points them to the exact same hardware RAM location
print(f"Are they at the exact same address? {a is b}")  # Returns True
print(f"Address A: {id(a)} | Address B: {id(b)}")
