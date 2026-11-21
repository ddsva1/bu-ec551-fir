// fir_serial.v - serial-MAC FIR low-pass for the FPGA audio demo
//
// One multiply-accumulate per clock (maps to a single DSP48 slice).
// N = 371 taps, 4 coefficient sets selected by set_sel (SW1-2).
// At 100 MHz and 48 kHz audio there are ~2083 clocks per sample;
// one output takes N + 5 = 376 clocks.
//
// Data:   16-bit signed samples (Q1.15)
// Coefs:  16-bit signed Q1.15, 4 sets x 512 words in fir_coeffs.mem
// Output: rounded (half up) and saturated back to 16 bits
//
// Latency: the filter's group delay is (N-1)/2 = 185 samples (3.85 ms);
// the computation itself adds 376 clocks (3.8 us at 100 MHz).

module fir_serial #(
    parameter integer N         = 371,
    parameter integer DW        = 16,          // sample width
    parameter integer CW        = 16,          // coefficient width (Q1.15)
    parameter integer AW        = 40,          // accumulator width
    parameter integer LW        = 9,           // log2(delay-line depth = 512)
    parameter         COEF_FILE = "fir_coeffs.mem"
) (
    input  wire                 clk,
    input  wire                 rst,
    input  wire                 in_valid,      // one-cycle strobe per new sample
    input  wire signed [DW-1:0] in_sample,
    input  wire [1:0]           set_sel,       // coefficient set, latched per sample
    output reg                  out_valid,     // one-cycle strobe
    output reg  signed [DW-1:0] out_sample,
    output wire                 busy           // high while a sample is being filtered
);
    localparam integer DEPTH = 1 << LW;

    // Delay line (circular buffer) and coefficient ROM, both inferred as block RAM
    reg signed [DW-1:0] dline [0:DEPTH-1];
    reg signed [CW-1:0] crom  [0:4*DEPTH-1];

    integer i;
    initial begin
        for (i = 0; i < DEPTH; i = i + 1) dline[i] = 0;
        $readmemh(COEF_FILE, crom);
    end

    // Control
    reg [LW-1:0] wr_ptr;       // next write position
    reg [LW-1:0] cur;          // position of the newest sample
    reg [LW-1:0] tap;          // k = 0 .. N-1
    reg [1:0]    set_q;
    reg          running;

    // Pipeline: read (1) -> multiply (2) -> accumulate (3) -> output (4)
    reg signed [DW-1:0]    x_q;
    reg signed [CW-1:0]    c_q;
    reg signed [DW+CW-1:0] prod;
    reg signed [AW-1:0]    acc;
    reg v1, v2, v3, first1, first2, last1, last2, last3;

    assign busy = running | v1 | v2 | v3;

    // Stage 0/1: accept a sample, then stream addresses and read both memories
    always @(posedge clk) begin
        if (rst) begin
            wr_ptr  <= 0;
            cur     <= 0;
            tap     <= 0;
            set_q   <= 0;
            running <= 1'b0;
            v1      <= 1'b0;
            first1  <= 1'b0;
            last1   <= 1'b0;
        end else begin
            v1     <= running;
            first1 <= running && (tap == 0);
            last1  <= running && (tap == N - 1);

            if (running) begin
                x_q <= dline[cur - tap];             // x[n-k], wraps mod 512
                c_q <= crom[{set_q, tap}];           // h_set[k]
                if (tap == N - 1) running <= 1'b0;
                tap <= tap + 1'b1;
            end else if (in_valid && !busy) begin
                dline[wr_ptr] <= in_sample;
                cur     <= wr_ptr;
                wr_ptr  <= wr_ptr + 1'b1;
                set_q   <= set_sel;
                tap     <= 0;
                running <= 1'b1;
            end
        end
    end

    // Stage 2: multiply (DSP48 M register)
    always @(posedge clk) begin
        if (rst) begin
            v2 <= 1'b0; first2 <= 1'b0; last2 <= 1'b0;
        end else begin
            v2     <= v1;
            first2 <= first1;
            last2  <= last1;
            if (v1) prod <= x_q * c_q;
        end
    end

    // Stage 3: accumulate (DSP48 P register)
    always @(posedge clk) begin
        if (rst) begin
            v3 <= 1'b0; last3 <= 1'b0; acc <= 0;
        end else begin
            v3    <= v2;
            last3 <= v2 && last2;
            if (v2) acc <= first2 ? {{(AW-DW-CW){prod[DW+CW-1]}}, prod}
                                  : acc + {{(AW-DW-CW){prod[DW+CW-1]}}, prod};
        end
    end

    // Stage 4: round half up, shift back to Q1.15, saturate to 16 bits
    localparam signed [AW-1:0] HALF = {{(AW-CW+1){1'b0}}, 1'b1, {(CW-2){1'b0}}};
    localparam signed [AW-1:0] MAXV =  (1 <<< (DW-1)) - 1;
    localparam signed [AW-1:0] MINV = -(1 <<< (DW-1));
    wire signed [AW-1:0] rounded = (acc + HALF) >>> (CW - 1);

    always @(posedge clk) begin
        if (rst) begin
            out_valid  <= 1'b0;
            out_sample <= 0;
        end else begin
            out_valid <= last3;
            if (last3)
                out_sample <= (rounded > MAXV) ? MAXV[DW-1:0] :
                              (rounded < MINV) ? MINV[DW-1:0] :
                                                 rounded[DW-1:0];
        end
    end
endmodule
