| bench | case | median ns/op | run medians |
|---|---|---:|---|
| registry_lookup | 1T Lookup hit (weak_ptr::lock + release) | 90.991 | 70.113-254.324 |
| registry_lookup | 1T LookupBorrowed hit (raw pointer) | 17.243 | 14.849-62.221 |
| registry_lookup | 2T Lookup hit, same entries | 206.881 | 137.711-218.561 |
| registry_lookup | 2T LookupBorrowed hit, same entries | 26.482 | 20.050-31.282 |
