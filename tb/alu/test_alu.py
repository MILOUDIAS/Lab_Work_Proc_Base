# Cocotb testbench for the SystemVerilog ALU module from the "Processeur de Base" project.
#
# This testbench verifies all ALU operations:
# - ADD, AND, CMA, TRANSFER, INC, CLA
# It includes both directed tests for specific cases and a randomized test for robustness.

import cocotb
from cocotb.triggers import Timer
import random

# --- Constants for ALU Operations ---
# These must match the definitions in the SystemVerilog 'definitions_pkg'.
ALU_AND = 0
ALU_ADD = 1
ALU_CMA = 2
# ALU_AND:      result = a & b;       (op=0)
# ALU_ADD:      {carry_out, result} = a + b;  (op=1)
# ALU_CMA:      result = ~a;          (op=2)
# ALU_TRANSFER: result = b;          (op=5)
# ALU_INC:      {carry_out, result} = a + 1;  (op=6)
# ALU_CLA:      result = '0;          (op=7)
# Let's define them correctly here.
ALU_TRANSFER = 5
ALU_INC = 6
ALU_CLA = 7

# Data width from the DUT parameter
DATA_WIDTH = 16
MAX_VAL = (1 << DATA_WIDTH) - 1


async def drive_and_check(dut, a_val, b_val, op_code, op_name):
    """
    Helper coroutine to drive inputs, wait, and check the output against a golden model.
    """
    dut.a.value = a_val
    dut.b.value = b_val
    dut.alu_op.value = op_code

    # Since the ALU is combinational, we wait a tiny amount of time for
    # the simulator to propagate the new input values.
    await Timer(1, units="ns")

    # Golden model: Calculate the expected result in Python
    expected_result = 0
    expected_carry = 0

    if op_code == ALU_AND:
        expected_result = a_val & b_val
    elif op_code == ALU_ADD:
        # Python handles large integers, so we simulate hardware overflow
        res = a_val + b_val
        expected_result = res & MAX_VAL
        expected_carry = 1 if res > MAX_VAL else 0
    elif op_code == ALU_CMA:
        expected_result = ~a_val & MAX_VAL  # Complement and mask to 16 bits
    elif op_code == ALU_TRANSFER:
        expected_result = b_val
    elif op_code == ALU_INC:
        res = a_val + 1
        expected_result = res & MAX_VAL
        expected_carry = 1 if res > MAX_VAL else 0
    elif op_code == ALU_CLA:
        expected_result = 0
    else:
        # Default case in DUT results in 0
        expected_result = 0
        expected_carry = 0

    # Get actual results from the DUT
    actual_result = dut.result.value
    actual_carry = dut.carry_out.value

    # Assertions to check correctness
    assert actual_result == expected_result, (
        f"[{op_name}] Result mismatch! A={a_val}, B={b_val} -> DUT:{actual_result}, Expected:{expected_result}"
    )
    assert actual_carry == expected_carry, (
        f"[{op_name}] Carry mismatch! A={a_val}, B={b_val} -> DUT:{actual_carry}, Expected:{expected_carry}"
    )

    dut._log.info(f"PASSED: {op_name} with A={a_val}, B={b_val}")


@cocotb.test()
async def test_directed_operations(dut):
    """Test all ALU operations with specific, directed values."""
    dut._log.info("Starting directed tests for all ALU operations.")

    # Test values
    a = 0x1234
    b = 0xABCD

    # --- Test each operation ---
    await drive_and_check(dut, a, b, ALU_AND, "ALU_AND")
    await drive_and_check(dut, a, b, ALU_ADD, "ALU_ADD")
    await drive_and_check(dut, a, b, ALU_CMA, "ALU_CMA")
    await drive_and_check(dut, a, b, ALU_TRANSFER, "ALU_TRANSFER")
    await drive_and_check(dut, a, b, ALU_INC, "ALU_INC")
    await drive_and_check(dut, a, b, ALU_CLA, "ALU_CLA")

    # --- Test corner cases ---
    dut._log.info("Testing corner cases.")
    # Test ADD with carry
    await drive_and_check(dut, 0xFFFF, 0x0001, ALU_ADD, "ALU_ADD (Carry Out)")
    # Test INC with carry
    await drive_and_check(dut, 0xFFFF, 0x0000, ALU_INC, "ALU_INC (Carry Out)")
    # Test with zero values
    await drive_and_check(dut, 0x0000, 0x0000, ALU_ADD, "ALU_ADD (Zeros)")


@cocotb.test()
async def test_randomized_operations(dut):
    """Test all ALU operations with randomized inputs for robustness."""
    dut._log.info("Starting randomized tests.")

    operations = {
        "ALU_AND": ALU_AND,
        "ALU_ADD": ALU_ADD,
        "ALU_CMA": ALU_CMA,
        "ALU_TRANSFER": ALU_TRANSFER,
        "ALU_INC": ALU_INC,
        "ALU_CLA": ALU_CLA,
    }

    num_random_tests = 100
    dut._log.info(f"Running {num_random_tests} randomized checks.")

    for i in range(num_random_tests):
        # Generate random inputs
        rand_a = random.randint(0, MAX_VAL)
        rand_b = random.randint(0, MAX_VAL)

        # Pick a random operation
        op_name, op_code = random.choice(list(operations.items()))

        # Drive, wait, and check
        await drive_and_check(dut, rand_a, rand_b, op_code, op_name)

    dut._log.info("Randomized testing complete.")
