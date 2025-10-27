def to_bool(value: str, strict: bool = True) -> bool:
    """
    Convertit une chaîne en booléen.

    Cette fonction reconnaît plusieurs variantes de valeurs "vraies" et "fausses",
    en français et en anglais. Elle peut lever une exception si la valeur est invalide,
    ou retourner False par défaut en mode non strict.

    Paramètres :
        value (str) : La chaîne à convertir (ex. "oui", "no", "true", "0", etc.).
        strict (bool) : Si True, lève une ValueError pour les valeurs inconnues.
                        Si False, retourne False pour toute valeur non reconnue.

    Retour :
        bool : True ou False selon la valeur fournie.

    Exceptions :
        ValueError : Si strict=True et que la valeur n'est pas reconnue.
    """
    true_values = {"1", "true", "yes", "on", "oui"}
    false_values = {"0", "false", "no", "off", "non"}

    value_clean = value.strip().lower()
    if value_clean in true_values:
        return True
    elif value_clean in false_values:
        return False
    elif strict:
        raise ValueError(f"Valeur booléenne invalide : '{value}'")
    return False
