from collecte_2026_v2 import stg_collecte_2026_v2
from collecte_2026 import stg_collecte_2026
from not_like_others_2025 import stg_collecte_not_like_others_2025
from Raw_Data_collecte_from_excel2024_et_2025 import stg_collecte_2024_2025

def stg_collecte_all():
    all_data = []
    all_data.extend(stg_collecte_2024_2025())
    all_data.extend(stg_collecte_not_like_others_2025())
    all_data.extend(stg_collecte_2026())
    all_data.extend(stg_collecte_2026_v2())

    return all_data


