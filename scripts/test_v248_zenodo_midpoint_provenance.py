def test_midpoint():
    pre=(10,20,30); post=(14,24,34)
    assert tuple((a+b)//2 for a,b in zip(pre,post))==(12,22,32)
