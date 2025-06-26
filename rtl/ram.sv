//=============================================================================
// 2. Main Memory (RAM) Module
//=============================================================================
// Models the 4Kx16 Main Memory.
// It has synchronous write and asynchronous read.
module ram #(
    parameter DATA_WIDTH = 16,
    parameter ADDR_WIDTH = 12
)(
    input  logic                      clk,
    input  logic [ADDR_WIDTH-1:0]     addr,
    input  logic [DATA_WIDTH-1:0]     data_in,
    input  logic                      wr_en, // Write Enable
    input  logic                      rd_en, // Read Enable
    output logic [DATA_WIDTH-1:0]     data_out
);
    // Memory storage array: 4K words (2^12 = 4096)
    logic [DATA_WIDTH-1:0] mem [2**ADDR_WIDTH];

    // Synchronous write operation
    always_ff @(posedge clk) begin
        if (wr_en) begin
            mem[addr] <= data_in;
        end
    end

    // Asynchronous read operation
    assign data_out = rd_en ? mem[addr] : 'z;

endmodule : ram
