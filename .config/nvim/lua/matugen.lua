local M = {}
local palette_path = vim.fn.expand('~/.config/palette.json')

local function load_palette()
  local fd = io.open(palette_path, 'r')
  if not fd then return nil end
  local content = fd:read('*a')
  fd:close()
  local ok, data = pcall(vim.json.decode, content)
  return ok and data or nil
end

function M.setup()
  local p = load_palette()
  if not p then
    vim.notify('matugen: could not load palette.json', vim.log.levels.WARN)
    return
  end

  require('base16-colorscheme').setup({
    base00 = p.background,
    base01 = '#e6e9ef',
    base02 = '#ccd0da',
    base03 = p.white,
    base04 = p.bright_black,
    base05 = p.foreground,
    base06 = p.foreground,
    base07 = p.background,
    base08 = p.red,
    base09 = p.magenta,
    base0A = p.yellow,
    base0B = p.green,
    base0C = p.cyan,
    base0D = p.blue,
    base0E = p.magenta,
    base0F = p.bright_red,
  })

  local hi = function(group, opts)
    vim.api.nvim_set_hl(0, group, opts)
  end

  hi('TelescopeNormal',         { fg = p.foreground,  bg = p.background })
  hi('TelescopeBorder',         { fg = p.white,       bg = p.background })
  hi('TelescopePromptNormal',   { fg = p.foreground,  bg = p.background })
  hi('TelescopePromptBorder',   { fg = p.white,       bg = p.background })
  hi('TelescopePromptPrefix',   { fg = p.blue,        bg = p.background })
  hi('TelescopePromptCounter',  { fg = p.bright_black,bg = p.background })
  hi('TelescopePromptTitle',    { fg = p.background,  bg = p.blue })
  hi('TelescopePreviewTitle',   { fg = p.background,  bg = p.cyan })
  hi('TelescopeResultsTitle',   { fg = p.background,  bg = p.magenta })
  hi('TelescopeSelection',      { fg = p.foreground,  bg = '#ccd0da' })
  hi('TelescopeSelectionCaret', { fg = p.blue,        bg = '#ccd0da' })
  hi('TelescopeMatching',       { fg = p.blue,        bold = true })
end

local signal = vim.uv.new_signal()
signal:start('sigusr1', vim.schedule_wrap(function()
  package.loaded['matugen'] = nil
  require('matugen').setup()
end))

return M
