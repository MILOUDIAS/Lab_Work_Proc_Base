//=============================================================================
// 1. Package with Global Definitions
//=============================================================================
// This package contains all the constants, such as instruction opcodes,
// cycle states, and ALU operations, making the code more readable and
// easier to maintain.
package definitions_pkg;

    // --- Data and Address Widths ---
    parameter DATA_WIDTH = 16;
    parameter ADDR_WIDTH = 12;
    parameter IO_WIDTH   = 8;

    // --- FSM Cycles (encoded by F and R flip-flops) ---
    // FR = 00
    parameter CYCLE_FETCH    = 2'b00;
    // FR = 01
    parameter CYCLE_INDIRECT = 2'b01;
    // FR = 10
    parameter CYCLE_EXECUTE  = 2'b10;
    // FR = 11 (Reserved for Interrupts)
    parameter CYCLE_INTERRUPT = 2'b11;

    // --- Instruction Opcodes (q0-q6 for IRM) ---
    parameter [2:0] OP_AND = 3'b000; // q0
    parameter [2:0] OP_ADD = 3'b001; // q1
    parameter [2:0] OP_LDA = 3'b010; // q2
    parameter [2:0] OP_STA = 3'b011; // q3
    parameter [2:0] OP_BIN = 3'b100; // q4
    parameter [2:0] OP_BSA = 3'b101; // q5
    parameter [2:0] OP_ISZ = 3'b110; // q6
    // Opcode 111 is reserved for IRR/IES
    parameter [2:0] OP_NON_IRM = 3'b111; // q7

    // --- ALU Operations (S2, S3, S4 from Chapitre IV, Page 27) ---
    parameter [2:0] ALU_AND      = 3'b000;
    parameter [2:0] ALU_ADD      = 3'b001;
    parameter [2:0] ALU_CMA      = 3'b010; // Complement AC (NOT)
    parameter [2:0] ALU_TRANSFER = 3'b101; // Transfer B to output (A <- B)
    parameter [2:0] ALU_INC      = 3'b110; // Increment AC
    parameter [2:0] ALU_CLA      = 3'b111; // Clear AC (Mise à Zéro)
    // Note: CIR and CIL are not included in the 8 primary ALU ops,
    // they are often handled by a shifter external or internal to the ALU.
    // We will model them as part of the AC register logic for simplicity.

endpackage : definitions_pkg