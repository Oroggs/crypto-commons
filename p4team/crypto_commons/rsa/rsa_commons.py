from p4team.crypto_commons.generic import bytes_to_long, find_divisor, multiply, long_to_bytes


def rsa_printable(x, exp, n):
    """
    Calculate RSA encryption/decryption and return result as bytes
    :param x: plaintex or ciphertext, can be either bytes or long
    :param exp: exponent
    :param n: modulus
    :return: result bytes
    """
    return long_to_bytes(rsa(x, exp, n))


def rsa(x, exp, n):
    """
    Calculate RSA encryption/decryption and return result as long
    :param x: plaintex or ciphertext, can be either bytes or long
    :param exp: exponent
    :param n: modulus
    :return: result long
    """
    return pow(ensure_long(x), exp, n)


def ensure_long(x):
    if type(x) is str:
        x = bytes_to_long(x)
    return x


def solve_crt(residue_and_moduli):
    """
    Solve CRT for given modular residues and modulus values, eg:
    x = 1 mod 3
    x = 2 mod 4
    x = 3 mod 5
    x = 58
    residue_and_moduli = [(1,3), (2,4), (3,5)]
    :param residue_and_moduli: list of pairs with (modular residue mod n, n)
    :return: x
    """
    moduli = [x[1] for x in residue_and_moduli]
    residues = [x[0] for x in residue_and_moduli]
    N = reduce(lambda x, y: x * y, moduli)
    Nxs = [N / n for n in moduli]
    ds = [modinv(N / n, n) for n in moduli]
    mults = [residues[i] * Nxs[i] * ds[i] for i in range(len(moduli))]
    return reduce(lambda x, y: x + y, mults) % N


def get_fi_distinct_primes(primes):
    """
    Get Euler totient for list of pairwise co-prime numbers
    :param primes: list of co-prime numbers
    :return: fi(n) = (p-1)(q-1)...
    """
    return reduce(lambda x, y: x * y, [(p - 1) for p in primes])


def get_fi_repeated_prime(p, k=1):
    """
    Return Euler totient for prime power p^k
    :param p: prime number
    :param k: power
    :return: fi(p^k)
    """
    return pow(p, k - 1) * (p - 1)


def extended_gcd(a, b):
    """
    Calculate extended greates common divisor of numbers a,b
    :param a: first number
    :param b: second number
    :return: gcd(a,b) and reminders
    """
    lastremainder, remainder = abs(a), abs(b)
    x, lastx, y, lasty = 0, 1, 1, 0
    while remainder:
        lastremainder, (quotient, remainder) = remainder, divmod(lastremainder, remainder)
        x, lastx = lastx - quotient * x, x
        y, lasty = lasty - quotient * y, y
    return lastremainder, lastx * (-1 if a < 0 else 1), lasty * (-1 if b < 0 else 1)


def gcd(a, b):
    """
    Return simple greatest common divisor of a and b
    :param a:
    :param b:
    :return: gcd(a,b)
    """
    return extended_gcd(a, b)[0]


def gcd_multi(numbers):
    """
    Calculate gcd for the list of numbers
    :param numbers: list of numbers
    :return: gcd(a,b,c,d,...)
    """
    return reduce(gcd, numbers)


def lcm(a, b):
    """
    Calculate least common multiple of a,b
    :param a: first number
    :param b: second number
    :return: lcm(a,b)
    """
    return a * b / gcd(a, b)


def lcm_multi(numbers):
    """
    Calculate lcm for the list of numbers
    :param numbers: list of numbers
    :return: lcm(a,b,c,d,...)
    """
    return multiply(numbers) / gcd_multi(numbers)


def modinv(x, y):
    """
    Return modular multiplicative inverse of x mod y.
    It is a value d such that x*d = 1 mod y
    :param x: number for which we want inverse
    :param y: modulus
    :return: modinv if it exists
    """
    return extended_gcd(x, y)[1] % y


def rsa_crt_distinct_multiprime(c, e, factors):
    """
    Calculate RSA-CRT solution. For c = pt^e mod n returns pt.
    n = factors[0]*factors[1]*... and each factor has to be relatively prime
    :param c: ciphertext
    :param e: public exponent
    :param factors: modulus factors
    :return: decoded ciphertext
    """
    k = len(factors)
    di = [modinv(e, prime - 1) for prime in factors]
    m = factors[0]
    tis = [-1]
    for prime in factors[1:]:
        tis.append(modinv(m, prime))
        m = m * prime
    y = c
    xis = []
    for i in range(k):
        xis.append(pow(y, di[i], factors[i]))
    x = xis[0]
    m = factors[0]
    for i in range(1, k):
        ri = factors[i]
        xi = xis[i]
        ti = tis[i]
        x += m * (((xi - x % ri) * ti) % ri)
        m = m * ri
    return x


def hensel_lifting(f, df, p, k, base_solution):
    """
    Calculate solutions to f(x) = 0 mod p^k for prime p
    :param f: function
    :param df: derivative
    :param p: prime
    :param k: power
    :param base_solution: solution to return for p=1
    :return: possible solutions to f(x) = 0 mod p^k
    """
    previous_solution = [base_solution]
    for x in range(k - 1):
        new_solution = []
        for i, n in enumerate(previous_solution):
            dfr = df(n)
            fr = f(n)
            if dfr % p != 0:
                t = (-(extended_gcd(dfr, p)[1]) * int(fr / p ** (k - 1))) % p
                new_solution.append(previous_solution[i] + t * p ** (k - 1))
            if dfr % p == 0:
                if fr % p ** k == 0:
                    for t in range(0, p):
                        new_solution.append(previous_solution[i] + t * p ** (k - 1))
        previous_solution = new_solution
    return previous_solution


def hastad_broadcast(residue_and_moduli):
    """
    Hastad RSA attack for the same message encrypted with the same public exponent e and different modulus.
    Requires exactly 'e' pairs as input
    Depends on gmpy2 because I don't know how to write a fast k-th integer root.
    :param residue_and_moduli: list of pairs (residue, modulus)
    :return: decrypted message
    """
    import gmpy2
    k = len(residue_and_moduli)
    solution, _ = gmpy2.iroot(solve_crt(residue_and_moduli), k)
    assert residue_and_moduli[0][0] == pow(int(solution), k, residue_and_moduli[0][1])
    return solution


def combine_signatures(signatures, N):
    return multiply(signatures) % N


def homomorphic_blinding_rsa(payload, get_signature, N, splits=2):
    """
    Perform blinding RSA attack on non-padded homomorphic implementations.
    It will use the signature service multiple times to get final signature.
    :param payload: data to sign
    :param get_signature: function returning signature
    :param N: public exponent
    :param splits: on how many parts the data should be split
    :return: signed data
    """
    data = payload
    if payload is not int:
        data = bytes_to_long(payload)
    parts = []
    for i in range(splits):
        smallest_divisor = find_divisor(data)
        parts.append(smallest_divisor)
        data = data / smallest_divisor
    parts.append(data)
    signatures = [get_signature(value) for value in parts]
    result_sig = combine_signatures(signatures, N)
    return result_sig


def modular_sqrt(a, p):
    """
    Calculates modular square root.
    For a = b^2 mod p calculates b
    :param a: residue
    :param p: modulus
    :return: root value
    """
    if legendre_symbol(a, p) != 1:
        return 0
    elif a == 0:
        return 0
    elif p == 2:
        return p
    elif p % 4 == 3:
        return pow(a, (p + 1) / 4, p)
    s = p - 1
    e = 0
    while s % 2 == 0:
        s /= 2
        e += 1
    n = 2
    while legendre_symbol(n, p) != -1:
        n += 1
    x = pow(a, (s + 1) / 2, p)
    b = pow(a, s, p)
    g = pow(n, s, p)
    r = e
    while True:
        t = b
        m = 0
        for m in xrange(r):
            if t == 1:
                break
            t = pow(t, 2, p)
        if m == 0:
            return x
        gs = pow(g, 2 ** (r - m - 1), p)
        g = (gs * gs) % p
        x = (x * gs) % p
        b = (b * g) % p
        r = m


def legendre_symbol(a, p):
    ls = pow(a, (p - 1) / 2, p)
    return -1 if ls == p - 1 else ls
