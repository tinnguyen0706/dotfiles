-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua

-- Giữ lại các tùy chỉnh cá nhân từ config cũ
vim.opt.tabstop = 2
vim.opt.shiftwidth = 2
vim.opt.scrolloff = 8
vim.opt.sidescrolloff = 8
vim.opt.listchars = { tab = "» ", trail = "·", nbsp = "␣" }
vim.opt.relativenumber = false
vim.opt.conceallevel = 0
vim.opt.clipboard = "unnamedplus"

vim.g.clipboard = {
  name = "wl-clipboard",
  copy = { ["+"] = "wl-copy --type text/plain", ["*"] = "wl-copy --primary --type text/plain" },
  paste = { ["+"] = "wl-paste --no-newline", ["*"] = "wl-paste --no-newline --primary" },
  cache_enabled = 0,
}
