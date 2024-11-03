local success = os.execute('mkdir -p /tmp/example')
if success then
    print('successfully created directory')
end

local handle = io.popen("date --date='@2147483647'")
if handle == nil then
    return
end
local stdout = handle:read()
success = handle:close()
if success then
    print('output is:', stdout)
else
    print('error when executing command')
end
