local function sum(...)
    print("items: ", ...)
    total = 0
    for idx, num in ipairs({...}) do
        total = total + num
    end
    print("total: ",total)
end

sum(1, 2)
sum(1, 2, 3)

nums = {1, 2, 3, 4}
sum(table.unpack(nums))