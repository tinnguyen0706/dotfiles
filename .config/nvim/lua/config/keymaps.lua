-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua

-- LazyVim đã có sẵn: <leader>w (save), <leader>q (quit), <C-h/j/k/l> (window nav),
-- <leader>l (Lazy), và rất nhiều keymaps khác.

-- Thêm keymaps cá nhân nếu cần
local map = vim.keymap.set
map("n", "<leader>Q", "<cmd>qa!<CR>", { desc = "Force quit all" })
