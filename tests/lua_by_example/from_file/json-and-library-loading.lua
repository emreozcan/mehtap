local JSON = require 'jfjson'
local inspect = require 'inspect'

local lua_value = JSON:decode('[ "Larry", "Curly", "Moe" ]')
print('json array -> lua', inspect(lua_value))

local raw_json_text = JSON:encode({ "a", "b", "c"})
print('lua -> json array: ', raw_json_text)

local raw_json_map = JSON:encode({
    ['key'] = 'value'
})
print('lua -> json map: ', raw_json_map)