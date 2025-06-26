
//=============================================================================
// ALU Module
//=============================================================================
// Performs arithmetic and logic operations.
module alu #(
    parameter DATA_WIDTH = 16
)(
    input  logic [DATA_WIDTH-1:0] a,         // Operand A (from AC)
    input  logic [DATA_WIDTH-1:0] b,         // Operand B (from MDR)
    input  logic [2:0]              alu_op,    // ALU operation select
    output logic [DATA_WIDTH-1:0] result,
    output logic                    carry_out
);
    import definitions_pkg::*;

    always_comb begin
        result = '0;
        carry_out = 1'b0;
        case (alu_op)
            ALU_AND:      result = a & b;
            ALU_ADD:      {carry_out, result} = a + b;
            ALU_CMA:      result = ~a;
            ALU_TRANSFER: result = b;
            ALU_INC:      {carry_out, result} = a + 1;
            ALU_CLA:      result = '0;
            default:      result = '0;
        endcase
    end
endmodule : alu
