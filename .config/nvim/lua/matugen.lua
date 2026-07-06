local M = {}

function M.setup()
  local palette = vim.fn.json_decode(vim.fn.readfile(vim.fn.expand("~/.config/palette.json")))

  require('base16-colorscheme').setup({
    base00 = palette.background,
    base01 = '#e6e9ef',
    base02 = '#ccd0da',
    base03 = palette.white,
    base04 = '#4c4f69',
    base05 = palette.foreground,
    base06 = palette.foreground,
    base07 = palette.foreground,
    base08 = palette.red,
    base09 = '#fe640b',
    base0A = palette.yellow,
    base0B = palette.green,
    base0C = palette.cyan,
    base0D = palette.blue,
    base0E = palette.magenta,
    base0F = '#e64553',
  })

  local bg = palette.background
  local fg = palette.foreground
  local panel_bg = '#e6e9ef'
  local element_bg = '#ccd0da'
  local blue = palette.blue
  local cyan = palette.cyan
  local green = palette.green
  local magenta = palette.magenta
  local white = palette.white

  local hi = function(group, opts)
    vim.api.nvim_set_hl(0, group, opts)
  end

  hi('TelescopeNormal',         { fg = fg,            bg = bg })
  hi('TelescopeBorder',         { fg = blue,           bg = bg })
  hi('TelescopePromptNormal',   { fg = fg,            bg = bg })
  hi('TelescopePromptBorder',   { fg = blue,           bg = bg })
  hi('TelescopePromptPrefix',   { fg = green,          bg = bg })
  hi('TelescopePromptCounter',  { fg = white, bg = bg })
  hi('TelescopePromptTitle',    { fg = bg,             bg = green })
  hi('TelescopePreviewTitle',   { fg = bg,             bg = cyan })
  hi('TelescopeResultsTitle',   { fg = bg,             bg = fg })
  hi('TelescopeSelection',      { fg = fg,            bg = panel_bg })
  hi('TelescopeSelectionCaret', { fg = green,          bg = panel_bg })
  hi('TelescopeMatching',       { fg = green,          bold = true })

  hi('NormalFloat',             { fg = fg,            bg = bg })
  hi('FloatBorder',             { fg = blue,           bg = bg })
  hi('WhichKeyFloat',           { fg = fg,            bg = bg })
  hi('WhichKeyBorder',          { fg = blue,           bg = bg })
end

local signal = vim.uv.new_signal()
signal:start(
  'sigusr1',
  vim.schedule_wrap(function()
    package.loaded['matugen'] = nil
    require('matugen').setup()
  end)
)

return M
