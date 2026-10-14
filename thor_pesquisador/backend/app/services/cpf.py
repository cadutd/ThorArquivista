import re


def normalizar_cpf(value: str) -> str:
    value = value.strip()
    if not re.fullmatch(r"(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}|[0-9]{9}-[0-9]{2})", value):
        raise ValueError("CPF invalido.")
    cpf = value.replace(".", "").replace("-", "")
    if len(set(cpf)) == 1:
        raise ValueError("CPF invalido.")
    for length in (9, 10):
        digit = (sum(int(cpf[i]) * (length + 1 - i) for i in range(length)) * 10) % 11
        if int(cpf[length]) != (0 if digit == 10 else digit):
            raise ValueError("CPF invalido.")
    return cpf
