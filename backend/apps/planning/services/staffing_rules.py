"""
Reglas de staffing centralizadas.
Única fuente de verdad para cálculos de personal necesario.
"""


def get_evening_persons_needed(couvertures: int) -> int:
    """
    Calcula personas necesarias para turno tarde basado en couvertures.

    Regla de negocio:
    - >38 couvertures → 4 personas
    - >25 couvertures → 3 personas
    - >13 couvertures → 2 personas
    - 1-13 couvertures → 1 persona
    - 0 couvertures → 0 personas

    Args:
        couvertures: Número de habitaciones ocupadas (= couvertures a hacer)

    Returns:
        Número de personas necesarias para turno tarde
    """
    if couvertures > 38:
        return 4
    elif couvertures > 25:
        return 3
    elif couvertures > 13:
        return 2
    elif couvertures > 0:
        return 1
    return 0


def get_morning_persons_needed(departures: int, stays: int) -> int:
    """
    Calcula personas mínimas necesarias para turno mañana.

    Regla: Mínimo 2 personas si hay trabajo, 0 si no hay.

    Args:
        departures: Número de salidas (DEPART)
        stays: Número de estancias (RECOUCH)

    Returns:
        Número mínimo de personas para turno mañana
    """
    total_rooms = departures + stays
    if total_rooms > 0:
        return max(2, (total_rooms + 9) // 10)  # ~1 persona por cada 10 habitaciones, mínimo 2
    return 0
