-- Base16 colorscheme with Matugen integration (Catppuccin Latte)
-- Không tắt tokyonight (LazyVim cần nó), chỉ ghi đè colorscheme

return {
  -- Đặt LazyVim dùng base16 làm colorscheme mặc định
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = function()
        local ok, matugen = pcall(require, "matugen")
        if ok then
          matugen.setup()
        end
      end,
    },
  },

  -- Base16 colorscheme plugin
  {
    "RRethy/nvim-base16",
    lazy = false,
    priority = 1000,
  },
}
