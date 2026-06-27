local trash_dir = os.getenv("HOME") .. "/.local/share/Trash/files"

local function is_data(mountpoint)
	if not mountpoint or mountpoint == "" then return false end
	if mountpoint:find("^/boot") then return false end
	if mountpoint:find("^/efi") then return false end
	if mountpoint == "[SWAP]" then return false end
	return true
end

local function is_big_enough(size_str)
	-- size_str like "200M", "16M", "99.2G", "355.7G", "783M"
	local num, unit = size_str:match("^([0-9.]+)([A-Z]+)$")
	if not num then return false end
	num = tonumber(num)
	if not num then return false end
	if unit == "G" and num >= 4 then return true end
	if unit == "T" then return true end
	if unit == "M" and num >= 4000 then return true end
	return false
end

local function trash_count()
	local output, err = Command("ls"):arg({ "-1", trash_dir }):stdout(Command.PIPED):output()
	if not output then return 0 end
	local n = 0
	for _ in output.stdout:gmatch("[^\n]+") do n = n + 1 end
	return n
end

local function mounts()
	local output, err = Command("lsblk"):arg({ "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE", "-l", "-n" }):stdout(Command.PIPED):output()
	if not output then return {}, {} end
	local mounted, unmounted = {}, {}
	for line in output.stdout:gmatch("[^\n]+") do
		local fields = {}
		for f in line:gmatch("%S+") do fields[#fields + 1] = f end
		if #fields < 3 then goto continue end
		local dtype = fields[3]
		if dtype ~= "part" and dtype ~= "crypt" and dtype ~= "lvm" then goto continue end
		if #fields >= 5 then
			if is_data(fields[4]) then
				table.insert(mounted, { name = fields[1], size = fields[2], mountpoint = fields[4], fstype = fields[5] })
			end
		else
			if is_big_enough(fields[2]) then
				table.insert(unmounted, { name = fields[1], size = fields[2], fstype = fields[4] or "" })
			end
		end
		::continue::
	end
	return mounted, unmounted
end

local function pick_key(i)
	if i <= 9 then return tostring(i) end
	return string.char(string.byte("a") + i - 10)
end

return {
	entry = function()
		local count = trash_count()
		local mounted, unmounted = mounts()
		local cands = {}

		table.insert(cands, { on = "t", desc = "Trash (" .. count .. ")" })

		for i, m in ipairs(mounted) do
			local mp = m.mountpoint
			if mp == "/" then mp = "/ (root)" end
			table.insert(cands, { on = pick_key(i), desc = mp .. "  [" .. m.size .. "]" })
		end

		for i, u in ipairs(unmounted) do
			local key = pick_key(#mounted + i)
			table.insert(cands, { on = key, desc = u.name .. "  [" .. u.size .. "]  (not mounted)" })
		end

		if #cands == 0 then
			ya.notify({ title = "Sidebar", content = "No locations found", timeout = 2, level = "info" })
			return
		end

		local choice = ya.which({ cands = cands })
		if not choice then return end

		if choice == 1 then
			ya.emit("cd", { Url(trash_dir) })
		elseif choice <= 1 + #mounted then
			ya.emit("cd", { Url(mounted[choice - 1].mountpoint) })
		else
			local u = unmounted[choice - 1 - #mounted]
			ya.notify({ title = "Sidebar", content = u.name .. " is not mounted", timeout = 3, level = "warn" })
		end
	end,
}
