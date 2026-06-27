require("full-border"):setup({ type = ui.Border.ROUNDED })
require("what-size"):setup({ priority = 600 })

local function fmt_size(bytes)
  if not bytes then return "-" end
  if bytes < 2 then return "1 byte" end
  if bytes < 1024 then return bytes .. " bytes" end
  local units = { "KB", "MB", "GB", "TB" }
  local v = bytes / 1024
  for _, u in ipairs(units) do
    if v < 1024 then return string.format("%.1f %s", v, u) end
    v = v / 1024
  end
  return string.format("%.1f %s", v, "TB")
end

local function fmt_time(sec)
  if not sec or sec == 0 then return "" end
  local days = math.floor((os.time() - sec) / 86400)
  if days == 0 then return "Today"
  elseif days == 1 then return "Yesterday"
  elseif days < 7 then return string.format("%d days ago", days)
  elseif days < 30 then return string.format("%d week%s ago", math.floor(days / 7), math.floor(days / 7) > 1 and "s" or "")
  elseif days < 365 then return string.format("%d month%s ago", math.floor(days / 30), math.floor(days / 30) > 1 and "s" or "")
  else return string.format("%d year%s ago", math.floor(days / 365), math.floor(days / 365) > 1 and "s" or "")
  end
end

function Linemode:size_and_mtime()
  local size = ""
  if not self._file.cha.is_dir then
    size = fmt_size(self._file:size())
  end
  return string.format("%10s  %12s", size, fmt_time(self._file.cha.mtime))
end
