import itertools

N = [100, 500, 1000, 5000, 10000, 50000, 100000]
D = [1, 1.25, 1.5, 1.75, 2]
C = [5, 10, 25, 50, 100, 250, 500, 1000]

for n, d, c in itertools.product(N, D, C):
    if n / c < 4: continue
    for re, s in [("-r", 111111111), ("-r", 222222222), ("-r", 333333333),
                  ("-e", 444444444), ("-e", 555555555), ("-e", 666666666)]:
        args = tuple(map(str, ["-n", n, "-m", int(n * d), "-l", n // c, "-s", s, re]))
        print("./random-lplan", *args, "/dev/null", " out/lplan" + "".join(args) + ".gml")
