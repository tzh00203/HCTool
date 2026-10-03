// Minimal lc_ctrl_pkg stub for aes_core leaf verification. The real package
// pulls lc_ctrl_state_pkg + lc_ctrl_reg_pkg (and their transitive deps),
// none of which aes_core needs beyond lc_tx_t and the test functions.
package lc_ctrl_pkg;
  parameter int TxWidth = 4;
  typedef enum logic [TxWidth-1:0] {
    On  = 4'b0101,
    Off = 4'b1010
  } lc_tx_t;
  parameter lc_tx_t LC_TX_DEFAULT = lc_tx_t'(Off);

  function automatic logic lc_tx_test_true_strict(lc_tx_t val);
    return On == val;
  endfunction
  function automatic logic lc_tx_test_false_strict(lc_tx_t val);
    return Off == val;
  endfunction
  function automatic logic lc_tx_test_true_loose(lc_tx_t val);
    return Off != val;
  endfunction
  function automatic logic lc_tx_test_false_loose(lc_tx_t val);
    return On != val;
  endfunction
endpackage
