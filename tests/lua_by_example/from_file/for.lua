for i=1, 5, 1 do
    print('first: ', i)
end

print('loop variable scope is local:', i) -- will print nil

print()

for i=1, 10, 1 do
    print('brk: ', i)
    if i == 5 then
        break
    end
end

print()

arr = {'a', 'b', 'c', 'd'}
for i,v in ipairs(arr) do
    print('arr: i, v', i, v)
end

print()

for i=1, 5 do
  if i % 2 == 0 then goto continue end
  print('odd: ', i)
  ::continue::
end