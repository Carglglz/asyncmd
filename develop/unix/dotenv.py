import re


def _parse_envdata(data):
    var, value = data.decode().split("=")
    return {var.strip(): value.strip()}


def sub_var(env_values, value):
    try:
        m = re.search(r"\${.*}", value)
        try:
            if not m:
                return eval(value)
        except NameError:
            return value
        var_rep = m.group(0)
        var_key = var_rep.replace("${", "").replace("}", "")
        value = value.replace(var_rep, env_values.get(var_key))
    except Exception as e:
        raise e
    try:
        return eval(value)
    except Exception:
        return value


def replace_vars(env_values):
    return {k: sub_var(env_values, v) for k, v in env_values.items()}


def dotenv_values(env, debug=False):
    env_values = {}
    try:
        with open(env, "rb") as _env:
            if debug:
                print(f"DOTENV: {env}")
            for line in _env:
                if not line.startswith(b"#"):
                    if debug:
                        print(line.decode().strip())
                    env_values.update(**_parse_envdata(line))
    except Exception:
        print(f"WARNING: configuration '{env}' file not found or corrupted")
    return replace_vars(env_values)


if __name__ == "__main__":
    print(dotenv_values(".env"))
