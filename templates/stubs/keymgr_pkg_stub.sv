// Minimal keymgr_pkg stub: aes_core only needs hw_key_req_t.
package keymgr_pkg;
  parameter int Shares  = 2;
  parameter int KeyWidth = 256;
  typedef struct packed {
    logic valid;
    logic [Shares-1:0][KeyWidth-1:0] key;
  } hw_key_req_t;
  parameter hw_key_req_t HW_KEY_REQ_DEFAULT = '{
    valid: 1'b0,
    key: {Shares{KeyWidth'(32'hDEADBEEF)}}
  };
endpackage
