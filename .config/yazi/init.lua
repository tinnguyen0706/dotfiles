require("full-border"):setup({ type = ui.Border.ROUNDED })
require("what-size"):setup({ priority = 600 })

local dir_counts = {}

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

local function count_dir(url_str)
  local h = io.popen("ls -1AU " .. url_str .. " 2> /dev/null | wc -l")
  if not h then return 0 end
  local r = h:read("*a")
  h:close()
  return tonumber(r) or 0
end

function Linemode:size_and_mtime()
  local time = fmt_time(self._file.cha.mtime)

  if self._file.cha.is_dir then
    local url = tostring(self._file.url)
    if dir_counts[url] == nil then
      dir_counts[url] = count_dir(url)
    end
    local n = dir_counts[url]
    return string.format("%10s  %12s", n .. " item" .. (n ~= 1 and "s" or ""), time)
  end

  return string.format("%10s  %12s", fmt_size(self._file:size()), time)
end
