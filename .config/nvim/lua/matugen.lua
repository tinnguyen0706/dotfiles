 local M = {}

function M.setup()
  require('base16-colorscheme').setup({
    base00 = '#e6e8fa',
    base01 = '#eff0ff',
    base02 = '#dbddff',
    base03 = '#7177fc',
    base04 = '#4b55c8',
    base05 = '#0e0e43',
    base06 = '#0e0e43',
    base07 = '#0e0e43',
    base08 = '#fd4663',
    base09 = '#0e0e43',
    base0A = '#8e93d8',
    base0B = '#5d65f5',
    base0C = '#1a1a7f',
    base0D = '#091090',
    base0E = '#1b217e',
    base0F = '#f7bbc4',
  })

  local hi = function(group, opts)
    vim.api.nvim_set_hl(0, group, opts)
  end

  hi('TelescopeNormal',         { fg = '#0e0e43',          bg = '#e6e8fa' })
  hi('TelescopeBorder',         { fg = '#7177fc',             bg = '#e6e8fa' })
  hi('TelescopePromptNormal',   { fg = '#0e0e43',          bg = '#e6e8fa' })
  hi('TelescopePromptBorder',   { fg = '#7177fc',             bg = '#e6e8fa' })
  hi('TelescopePromptPrefix',   { fg = '#5d65f5',             bg = '#e6e8fa' })
  hi('TelescopePromptCounter',  { fg = '#4b55c8',  bg = '#e6e8fa' })
  hi('TelescopePromptTitle',    { fg = '#e6e8fa',             bg = '#5d65f5' })
  hi('TelescopePreviewTitle',   { fg = '#e6e8fa',             bg = '#8e93d8' })
  hi('TelescopeResultsTitle',   { fg = '#e6e8fa',             bg = '#0e0e43' })
  hi('TelescopeSelection',      { fg = '#0e0e43',          bg = '#dbddff' })
  hi('TelescopeSelectionCaret', { fg = '#5d65f5',             bg = '#dbddff' })
  hi('TelescopeMatching',       { fg = '#5d65f5',             bold = true })
end

 -- Register a signal handler for SIGUSR1 (matugen updates)
 local signal = vim.uv.new_signal()
 signal:start(
   'sigusr1',
   vim.schedule_wrap(function()
     package.loaded['matugen'] = nil
     require('matugen').setup()
   end)
 )

 return M
