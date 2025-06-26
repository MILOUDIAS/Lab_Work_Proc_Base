# test_control_unit.py
#
# Cocotb testbench for the SystemVerilog control_unit module from the
# "Processeur de Base" project.
#
# This testbench verifies:
# - Reset and startup sequence.
# - Correct FSM sequencing for Fetch, Indirect, and Execute cycles.
# - Correct control signal generation for representative instructions (ADD, CLA).

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import random

# --- Constants from definitions_pkg ---
# Opcodes (q0-q6 for IRM)
OP_ADD = 1
OP_NON_IRM = 7

# Instruction Hex Codes (for d_bits)
CLA_HEX = 0x7800  # For IRR, this means d_bits[11] is high


# Helper to create expected control word value
def expected_F(*args):
    """Creates a 49-bit integer with specified F-signals set (1-based)."""
    val = 0
    if not args:
        return val
    for bit in args:
        # The control_word is logic [49:1], so bit 1 is at index 0
        val |= 1 << (bit - 1)
    return val


class ControlUnitDriver:
    """A helper class to drive inputs and manage state for the control_unit DUT."""

    def __init__(self, dut, clk):
        self.dut = dut
        self.clk = clk
        # Set all inputs to a default, inactive state
        self.dut.op_code.value = 0
        self.dut.i_bit.value = 0
        self.dut.d_bits.value = 0
        self.dut.ac_is_zero.value = 0
        self.dut.ac_is_neg.value = 0
        self.dut.e_is_zero.value = 0
        self.dut.fgi.value = 0
        self.dut.fgo.value = 0
        self.dut.mdr_is_zero.value = 0
        self.dut.s_in.value = 0

    async def reset(self):
        """Perform the reset sequence."""
        self.dut.reset_n.value = 0
        await RisingEdge(self.clk)
        await RisingEdge(self.clk)
        self.dut.reset_n.value = 1
        self.dut._log.info("Reset complete.")

    async def start_processor(self):
        """Press the 'start' button."""
        self.dut.s_in.value = 1
        await RisingEdge(self.clk)
        self.dut.s_in.value = 0
        self.dut._log.info("Processor started.")

    def set_instruction(self, op_code, i_bit, d_bits=0):
        """Set the instruction inputs to the DUT."""
        self.dut.op_code.value = op_code
        self.dut.i_bit.value = i_bit
        self.dut.d_bits.value = d_bits
        self.dut._log.info(
            f"Driving instruction: op={op_code}, i={i_bit}, d=0x{d_bits:X}"
        )


# =============================================================================
# Test Cases
# =============================================================================


@cocotb.test()
async def test_reset_and_fetch_cycle(dut):
    """Verify reset behavior and the 4 steps of the Fetch cycle."""
    # Start the clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    driver = ControlUnitDriver(dut, dut.clk)

    # 1. Test Reset
    await driver.reset()
    assert dut.control_word.value == 0, "Control word should be 0 after reset."

    # 2. Start processor and set an instruction (ADD Direct)
    await driver.start_processor()
    driver.set_instruction(OP_ADD, 0)  # ADD, Direct mode

    # 3. Verify Fetch Cycle (T0-T3)
    dut._log.info("Verifying FETCH cycle control signals.")

    # T0
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(1), "FETCH-T0 should assert F1."

    # T1
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(2), "FETCH-T1 should assert F2."

    # T2
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(3), "FETCH-T2 should assert F3."

    # T3 - For ADD Direct, should transition to Execute
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(5), (
        "FETCH-T3 should assert F5 for direct instruction."
    )

    # At the next clock, we should be in EXECUTE cycle at T0
    await RisingEdge(dut.clk)
    dut._log.info("Fetch cycle test passed.")


@cocotb.test()
async def test_indirect_cycle(dut):
    """Verify the transition to and execution of the Indirect cycle."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    driver = ControlUnitDriver(dut, dut.clk)
    await driver.reset()
    await driver.start_processor()

    # Set an instruction that requires an indirect cycle (ADD Indirect)
    driver.set_instruction(OP_ADD, 1)

    # Let the fetch cycle run (T0-T3)
    for _ in range(3):
        await RisingEdge(dut.clk)

    # At T3 of FETCH, check for transition to INDIRECT
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(4), (
        "FETCH-T3 should assert F4 for indirect instruction."
    )
    dut._log.info("Transitioned to INDIRECT cycle.")

    # Now verify the INDIRECT cycle itself (T0-T3)
    # T0
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(6), "INDIRECT-T0 should assert F6."

    # T1
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(7), "INDIRECT-T1 should assert F7."

    # T2 (NOP)
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(), (
        "INDIRECT-T2 should be a NOP (no F signals)."
    )

    # T3 (Transition to EXECUTE)
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(9), "INDIRECT-T3 should assert F9."

    dut._log.info("Indirect cycle test passed.")


@cocotb.test()
async def test_execute_cycle_add_direct(dut):
    """Verify the EXECUTE cycle for a direct ADD instruction."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    driver = ControlUnitDriver(dut, dut.clk)
    await driver.reset()
    await driver.start_processor()
    driver.set_instruction(OP_ADD, 0)  # ADD, Direct mode

    # Run through the FETCH cycle to get to EXECUTE
    for _ in range(4):
        await RisingEdge(dut.clk)

    dut._log.info("Verifying EXECUTE cycle for ADD (Direct).")

    # T0 of EXECUTE
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(14), "EXECUTE-ADD-T0 should assert F14."

    # T1
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(15), "EXECUTE-ADD-T1 should assert F15."

    # T2
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(16), "EXECUTE-ADD-T2 should assert F16."

    # T3 (Return to FETCH)
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(13), "EXECUTE-IRM-T3 should assert F13."

    dut._log.info("Execute cycle for ADD (Direct) test passed.")


@cocotb.test()
async def test_execute_cycle_cla(dut):
    """Verify the EXECUTE cycle for a CLA (register-reference) instruction."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    driver = ControlUnitDriver(dut, dut.clk)
    await driver.reset()
    await driver.start_processor()

    # Set instruction to CLA (OP=111, I=0, d_bits[11]=1)
    driver.set_instruction(OP_NON_IRM, 0, d_bits=(1 << 11))

    # Run through FETCH cycle
    for _ in range(4):
        await RisingEdge(dut.clk)

    dut._log.info("Verifying EXECUTE cycle for CLA (IRR).")

    # T0 of EXECUTE for CLA
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(31), "EXECUTE-CLA-T0 should assert F31."

    # T1, T2, T3 should be NOPs for IRR, as it's a single-cycle execution at T0.
    # The FSM will still transition back to FETCH at T3, but no F signals are asserted
    # except the implicit ones that control the F/R flip-flops internally.
    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(), "EXECUTE-IRR-T1 should be a NOP."

    await RisingEdge(dut.clk)
    assert dut.control_word.value == expected_F(), "EXECUTE-IRR-T2 should be a NOP."

    await RisingEdge(dut.clk)
    # At T3, the FSM transitions back to fetch, but no F-signals are generated for IRR/IES.
    # The internal logic handles the f_ff/r_ff transition.
    assert dut.control_word.value == expected_F(), "EXECUTE-IRR-T3 should be a NOP."

    dut._log.info("Execute cycle for CLA test passed.")
